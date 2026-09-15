"""Shared paths and run-file operations. Runtime state is never distributable.

Linux-only locking is intentional: the observed application runs in Webtop.
There is no scheduler, database, automatic retry, or per-essay checkpoint.
"""
from __future__ import annotations

import csv
import fcntl
import glob
import json
import os
import tempfile
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from uuid import uuid4

GROUPS = (("aw", "All words"), ("cw", "Content words"), ("fw", "Function words"))
INDICES = (("simple_ttr", "Simple TTR"), ("root_ttr", "Root TTR"),
           ("log_ttr", "Log TTR"), ("maas_ttr", "Maas"), ("mattr", "MATTR"),
           ("msttr", "MSTTR"), ("hdd", "HD-D"), ("mltd", "MTLD Original"),
           ("mltd_ma", "MTLD MA Bi"), ("mtld_wrap", "MTLD MA Wrap"))
# Preserve the historic mltd / mltd_ma option keys. They are not spelling fixes.
OPTION_KEYS = tuple(k for k, _ in GROUPS + INDICES) + ("indout",)
INPUT_REL = Path("materials/data/ICNALE_500_merged_clean_texts/ICNALE_500_merged_clean")
ENGINE_REL = Path("tools/taaled_1_4_1/TAALED_1_4_1_Py3/TAALED_1_4_1_Hemma.py")


@dataclass(frozen=True)
class Paths:
    workspace: Path
    home: Path

    @classmethod
    def environment(cls) -> "Paths":
        return cls(Path(os.environ.get("WORKSHOP_ROOT", "/config/workspace")).resolve(),
                   Path(os.environ.get("WORKSHOP_HOME", "/config")).resolve())

    @property
    def browse_root(self) -> Path:
        return Path(os.environ.get("FEATURE_BROWSE_ROOT", "/hemma-home")).resolve()

    @property
    def ellipse_train(self) -> Path:
        return self.workspace / "materials/data/ELLIPSE_promoted_scorer_input_v1/texts/train"

    @property
    def ellipse_test(self) -> Path:
        return self.workspace / "materials/data/ELLIPSE_promoted_scorer_input_v1/texts/test"

    @property
    def private_cohort(self) -> Path:
        return self.workspace / "materials/data/HuleEdu_private_catalog_active_students_v1/essays"

    @property
    def input(self) -> Path:
        return self.workspace / INPUT_REL

    @property
    def output(self) -> Path:
        return self.workspace / "output"

    @property
    def taaled_output(self) -> Path:
        return self.output / "taaled"

    @property
    def navigation(self) -> Path:
        return self.home / "Navigation"

    @property
    def state(self) -> Path:
        return self.home / ".local/state/sophistication-feature-processing"

    @property
    def engine(self) -> Path:
        configured = os.environ.get("WORKSHOP_ENGINE")
        return Path(configured).resolve() if configured else self.workspace / ENGINE_REL


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid4().hex[:12]


def sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".workshop-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object: {path.name}")
    return data


class AlreadyRunning(RuntimeError):
    pass


@contextmanager
def run_lock(state: Path) -> Iterator[None]:
    state.mkdir(parents=True, exist_ok=True)
    # Never unlink this file: the kernel lock, not file existence, is authoritative.
    fd = os.open(state / "taaled.lock", os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise AlreadyRunning("Another TAALED worker is running") from exc
        yield
    finally:
        os.close(fd)


def worker_active(state: Path) -> bool:
    try:
        with run_lock(state):
            return False
    except AlreadyRunning:
        return True


def input_snapshot(folder: Path) -> list[dict]:
    folder = folder.resolve(strict=True)
    if not folder.is_dir():
        raise ValueError("Select a directory containing the text files")
    # Match the existing nonrecursive lowercase *.txt contract and ignore dot files.
    files = sorted(Path(p) for p in glob.glob(str(folder / "*.txt")))
    if not files:
        raise ValueError("No visible lowercase .txt files in this folder; select the inner text folder")
    records = []
    for file in files:
        if not file.is_file():
            raise ValueError(f"Not a regular text file: {file.name}")
        stat = file.stat()
        if stat.st_size == 0:
            raise ValueError(f"Empty text file: {file.name}; no analysis has started")
        with file.open("rb") as source:
            source.read(1)  # Check readability without retaining any content.
        records.append({"name": file.name, "size": stat.st_size,
                        "mtime_ns": stat.st_mtime_ns})
    return records


def validate_options(options: dict, basic_only: bool) -> dict:
    if set(options) != set(OPTION_KEYS):
        raise ValueError("Unexpected or missing analysis options")
    if any(type(value) is not int or value not in (0, 1) for value in options.values()):
        raise ValueError("Options must be integer zero or one")
    selected = dict(options)
    if basic_only:
        for key, _ in GROUPS + INDICES:
            selected[key] = 0
    elif not (any(selected[k] for k, _ in GROUPS) and
              any(selected[k] for k, _ in INDICES)):
        raise ValueError("Select at least one word group and one index, or explicitly choose basic counts only")
    return selected


def validate_output_root(folder: Path, paths: Paths) -> Path:
    folder = folder.expanduser().resolve()
    allowed = (paths.output.resolve(), paths.browse_root.resolve())
    if not any(folder == root or root in folder.parents for root in allowed):
        raise ValueError("Save results under Hemma Home or the service output folder")
    return folder


def validate_csv(path: Path, records: list[dict]) -> None:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.reader(stream)
        header = next(reader, [])
        if not header or header[0] != "filename":
            raise ValueError("Results CSV is missing the expected header")
        names = []
        for row in reader:
            if len(row) != len(header):
                raise ValueError("Results CSV has an incomplete or malformed row")
            names.append(row[0])
    if Counter(names) != Counter(record["name"] for record in records):
        raise ValueError("Results do not match the selected input files")


def read_status(paths: Paths) -> dict:
    active = worker_active(paths.state)
    state = load_json(paths.state / "active.json")
    if not state:
        return {"state": "running" if active else "idle", "active": active,
                "message": "Worker is starting…" if active else "Ready"}
    state["active"] = active
    final = Path(state["output_parent"]) / state["run_id"]
    if not active and final.is_dir():
        receipt = load_json(final / "run.json")
        if receipt.get("state") == "complete":
            receipt.update(active=False, run_directory=str(final),
                           message="Complete — taaled.csv is available")
            return receipt
    if not active and state.get("state") == "running":
        state.update(state="interrupted", message="Run interrupted. Preserve the .incomplete folder and start a new run; no automatic resume.")
    return state
