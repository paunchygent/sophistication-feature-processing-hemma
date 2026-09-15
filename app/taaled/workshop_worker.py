"""One detached, locked TAALED run; not a background service or job scheduler."""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.metadata
import importlib.util
import json
import multiprocessing
import resource
from dataclasses import asdict
import os
from pathlib import Path
import platform
import re
import sys
import time
import traceback

from workshop_performance import Performance

from workshop_common import (AlreadyRunning, Paths, atomic_json, input_snapshot,
                             run_lock, sync_directory, utc_now, validate_csv,
                             validate_options, validate_output_root)


def load_engine(path: Path):
    spec = importlib.util.spec_from_file_location("workshop_legacy_taaled", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load the installed TAALED source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if getattr(module, "WORKSHOP_IO_REVISION", None) != 2:
        raise RuntimeError("The contained TAALED I/O patch has not been reconciled/applied")
    return module


def versions(engine: Path) -> dict:
    def installed(name: str) -> str:
        try:
            return importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            return "not available as a distribution"
    dependencies = {}
    for name in ("adj_lem_list.txt", "real_words.txt"):
        file = engine.parent / "dep_files" / name
        dependencies[name] = hashlib.sha256(file.read_bytes()).hexdigest()
    return {"python": platform.python_version(), "spacy": installed("spacy"),
            "en_core_web_sm": installed("en-core-web-sm"),
            "engine_sha256": hashlib.sha256(engine.read_bytes()).hexdigest(),
            "dependency_sha256": dependencies}


class Progress:
    def __init__(self, path: Path, record: dict):
        self.path, self.record = path, record
        self.last_write = 0.0

    def put(self, message: str) -> None:
        # GUI polls 4 times/second. No per-token events or Tk calls from this process.
        self.record.update(message=str(message), updated_at=utc_now())
        if time.monotonic() - self.last_write >= 0.25:
            # The full input inventory belongs in durable run.json, not in every
            # four-per-second UI status write during an 8,035-document analysis.
            atomic_json(self.path, {k: v for k, v in self.record.items() if k != "inputs"})
            self.last_write = time.monotonic()


def run(paths: Paths, input_folder: Path, output_parent: Path, options: dict,
        basic_only: bool, run_id: str, engine_loader=load_engine,
        *, performance: Performance | None = None) -> Path:
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}", run_id):
        raise ValueError("Invalid run identifier")
    performance = performance or Performance.environment()
    if performance.n_process > 1 and multiprocessing.get_start_method() != "spawn":
        raise ValueError("Multiprocess TAALED must run in the spawn-configured worker CLI")
    input_folder = input_folder.expanduser().resolve(strict=True)
    options = validate_options(options, basic_only)
    output_parent = validate_output_root(output_parent, paths)
    os.umask(0o077)
    with run_lock(paths.state):
        records = input_snapshot(input_folder)
        output_parent.mkdir(parents=True, exist_ok=True)
        stage = output_parent / (run_id + ".incomplete")
        final = output_parent / run_id
        if final.exists():
            raise FileExistsError("A completed run already has this identifier")
        stage.mkdir(mode=0o700)  # Fails on a collision; never reuse a run directory.
        record = {"schema": 1, "run_id": run_id, "state": "running",
                  "started_at": utc_now(), "updated_at": utc_now(),
                  "input_directory": str(input_folder), "inputs": records,
                  "input_count": len(records), "options": options,
                  "basic_counts_only": basic_only,
                  "execution": dict(asdict(performance),
                      start_method=multiprocessing.get_start_method(),
                      python_hash_seed=os.environ.get("PYTHONHASHSEED", "not fixed"),
                      native_threads={key: os.environ.get(key, "unset") for key in
                          ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS")}),
                  "output_parent": str(output_parent), "run_directory": str(stage),
                  "message": "Preparing analysis…"}
        published = False
        try:
            atomic_json(stage / "run.json", record)
            atomic_json(paths.state / "active.json", record)
            # Logs stay private alongside runtime output; never copy them into support.
            with (stage / "worker.log").open("x", encoding="utf-8", buffering=1) as log:
                with redirect_stdout(log), redirect_stderr(log):
                    try:
                        engine = engine_loader(paths.engine)
                        record["runtime"] = versions(paths.engine)
                        started = time.perf_counter()
                        before = [resource.getrusage(who) for who in
                                  (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN)]
                        details = engine.main(str(input_folder), str(stage / "taaled.csv"), options,
                                    input_files=[str(input_folder / r["name"]) for r in records],
                                    progress_queue=Progress(paths.state / "active.json", record),
                                    **asdict(performance))
                        elapsed = time.perf_counter() - started
                        after = [resource.getrusage(who) for who in
                                 (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN)]
                        record["measurement"] = {
                            "engine": details,
                            "analysis_wall_seconds": elapsed,
                            "files_per_second": len(records) / elapsed,
                            "input_bytes": sum(r["size"] for r in records),
                            "user_cpu_seconds": sum(b.ru_utime - a.ru_utime for a, b in zip(before, after)),
                            "system_cpu_seconds": sum(b.ru_stime - a.ru_stime for a, b in zip(before, after)),
                            "parent_peak_rss_kib": after[0].ru_maxrss,
                            # Not a sum of concurrent child memory. Sample the process
                            # tree/cgroup separately when evaluating multiprocessing.
                            "largest_reaped_child_peak_rss_kib": after[1].ru_maxrss,
                        }
                    except BaseException:
                        traceback.print_exc()
                        raise
            if input_snapshot(input_folder) != records:
                raise ValueError("Input file metadata changed during analysis; output remains incomplete")
            validate_csv(stage / "taaled.csv", records)
            if options["indout"]:
                expected = {r["name"][:-4] + "_processed.txt" for r in records}
                actual = {f.name for f in (stage / "taaled_diagnostic").iterdir() if f.is_file()}
                if actual != expected:
                    raise ValueError("Diagnostic files do not match the input files")
            record.update(state="complete", finished_at=utc_now(),
                          message=f"Complete — {len(records)} texts", run_directory=str(final))
            atomic_json(stage / "run.json", record)
            # Persist files before publishing the directory on the same filesystem.
            for file in stage.rglob("*"):
                if file.is_file():
                    with file.open("rb") as stream:
                        os.fsync(stream.fileno())
            for folder in sorted((f for f in stage.rglob("*") if f.is_dir()),
                                 key=lambda f: len(f.parts), reverse=True):
                sync_directory(folder)
            sync_directory(stage)
            stage.rename(final)
            published = True
            sync_directory(output_parent)
            atomic_json(paths.state / "active.json", record)
            return final
        except BaseException as exc:
            if published:
                # A valid final directory is already present. Do not relabel it failed
                # merely because the auxiliary active-status write failed.
                raise
            record.update(state="failed", finished_at=utc_now(),
                          run_directory=str(stage),
                          message=f"Analysis failed ({type(exc).__name__}); preserve this incomplete run and inspect worker.log locally")
            try:
                with (stage / "worker.log").open("a", encoding="utf-8") as log:
                    traceback.print_exc(file=log)
                atomic_json(stage / "run.json", record)
                atomic_json(paths.state / "active.json", record)
            except OSError:
                pass  # Disk/permission failure may prevent a final receipt; .incomplete remains.
            raise


def main() -> int:
    # Only the detached worker owns multiprocessing policy; never fork the Tk GUI.
    multiprocessing.set_start_method("spawn")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS"):
        os.environ.setdefault(key, "1")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-parent", type=Path, required=True)
    parser.add_argument("--options", required=True, help="JSON integer options; no credentials")
    parser.add_argument("--basic-only", action="store_true")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--n-process", type=int, choices=(1, 2, 4), default=None)
    args = parser.parse_args()
    try:
        defaults = Performance.environment()
        performance = Performance(args.batch_size if args.batch_size is not None else defaults.batch_size,
                                  args.n_process if args.n_process is not None else defaults.n_process)
        run(Paths.environment(), args.input, args.output_parent,
            json.loads(args.options), args.basic_only, args.run_id, performance=performance)
    except AlreadyRunning:
        return 75
    except Exception as exc:
        print(f"TAALED worker failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
