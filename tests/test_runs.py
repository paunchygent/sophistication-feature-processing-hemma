import csv
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import types

import pytest
import workshop_worker as worker
from workshop_common import (AlreadyRunning, atomic_json, input_snapshot, load_json,
                             new_run_id, read_status, run_lock, validate_options,
                             validate_output_root, worker_active)

class FakeEngine:
    @staticmethod
    def main(indir, outdir, options, *, input_files, progress_queue):
        progress_queue.put('Synthetic engine processing')
        with open(outdir, 'x', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(['filename', 'synthetic_value'])
            writer.writerows((Path(f).name, 1) for f in input_files)
        if options['indout']:
            folder = Path(outdir).with_name('taaled_diagnostic')
            folder.mkdir()
            for file in input_files:
                (folder / (Path(file).stem + '_processed.txt')).write_text('synthetic diagnostic\n')


def test_nonrecursive_visible_lowercase_input_contract(paths):
    (paths.input / '.hidden.txt').write_text('not selected')
    (paths.input / '._apple.txt').write_text('not selected')
    (paths.input / 'upper.TXT').write_text('not selected')
    sub = paths.input / 'nested'
    sub.mkdir()
    (sub / 'nested.txt').write_text('not selected')
    assert len(input_snapshot(paths.input)) == 2


def test_empty_input_rejected_before_reservation(paths, options):
    (paths.input / 'empty.txt').touch()
    with pytest.raises(ValueError, match='Empty text'):
        worker.run(paths, paths.input, paths.taaled_output, options, False,
                   new_run_id(), lambda _: FakeEngine)
    assert list(paths.taaled_output.iterdir()) == []


def test_options_require_explicit_meaning(options):
    empty = {key: 0 for key in options}
    with pytest.raises(ValueError, match='Select at least'):
        validate_options(empty, False)
    assert not any(validate_options(options, True).values())
    with pytest.raises(ValueError):
        validate_options({'unknown': 1}, False)


def test_output_cannot_follow_symlink_out_of_canonical_tree(paths, tmp_path):
    link = paths.output / 'elsewhere'
    link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match='Hemma Home'):
        validate_output_root(link, paths)


def test_completed_run_csv_diagnostics_and_receipt(paths, options):
    options['indout'] = 1
    folder = worker.run(paths, paths.input, paths.taaled_output, options, False,
                        new_run_id(), lambda _: FakeEngine)
    assert folder.is_dir() and not folder.name.endswith('.incomplete')
    state = read_status(paths)
    assert state['state'] == 'complete'
    assert state['input_count'] == 2
    assert not state['active']
    assert len(list((folder / 'taaled_diagnostic').iterdir())) == 2
    with (folder / 'taaled.csv').open(newline='') as f:
        assert list(csv.reader(f))[2][0] == 'beta, quoted.txt'
    assert stat_mode(folder) == 0o700
    assert stat_mode(folder / 'run.json') == 0o600


def stat_mode(path):
    return path.stat().st_mode & 0o777


def test_failure_preserves_previous_result_and_incomplete_output(paths, options):
    previous = worker.run(paths, paths.input, paths.taaled_output, options, False,
                          new_run_id(), lambda _: FakeEngine)
    before = (previous / 'taaled.csv').read_bytes()
    class Broken:
        @staticmethod
        def main(indir, outdir, *_args, **_kwargs):
            Path(outdir).write_text('filename,value\nalpha.txt,')
            raise RuntimeError('synthetic error')
    run_id = new_run_id()
    with pytest.raises(RuntimeError):
        worker.run(paths, paths.input, paths.taaled_output, options, False, run_id, lambda _: Broken)
    assert (previous / 'taaled.csv').read_bytes() == before
    assert (paths.taaled_output / (run_id + '.incomplete') / 'taaled.csv').is_file()
    assert not (paths.taaled_output / run_id).exists()
    assert read_status(paths)['state'] == 'failed'


def test_wrong_csv_identity_is_not_published(paths, options):
    class Wrong:
        @staticmethod
        def main(indir, outdir, *_args, **_kwargs):
            Path(outdir).write_text('filename,value\nwrong.txt,1\n')
    with pytest.raises(ValueError, match='match'):
        worker.run(paths, paths.input, paths.taaled_output, options, False,
                   new_run_id(), lambda _: Wrong)
    assert all(p.name.endswith('.incomplete') for p in paths.taaled_output.iterdir())


def test_changed_input_metadata_is_not_published(paths, options):
    class Change(FakeEngine):
        @staticmethod
        def main(indir, outdir, options, **kwargs):
            FakeEngine.main(indir, outdir, options, **kwargs)
            (Path(indir) / 'alpha.txt').write_text('changed input')
    with pytest.raises(ValueError, match='changed'):
        worker.run(paths, paths.input, paths.taaled_output, options, False,
                   new_run_id(), lambda _: Change)


def test_kernel_lock_not_lockfile_existence(paths):
    with run_lock(paths.state):
        assert worker_active(paths.state)
        with pytest.raises(AlreadyRunning):
            with run_lock(paths.state):
                pass
    assert (paths.state / 'taaled.lock').exists()
    assert not worker_active(paths.state)


def test_collision_cannot_overwrite_completed_run(paths, options):
    run_id = new_run_id()
    folder = worker.run(paths, paths.input, paths.taaled_output, options, False, run_id, lambda _: FakeEngine)
    before = (folder / 'taaled.csv').read_bytes()
    with pytest.raises(FileExistsError):
        worker.run(paths, paths.input, paths.taaled_output, options, False, run_id, lambda _: FakeEngine)
    assert (folder / 'taaled.csv').read_bytes() == before


def test_final_directory_is_recovered_after_status_write_failure(paths, options, monkeypatch):
    real_atomic = worker.atomic_json
    def fail_last(path, value):
        if path == paths.state / 'active.json' and value.get('state') == 'complete':
            raise OSError('synthetic final status failure')
        real_atomic(path, value)
    monkeypatch.setattr(worker, 'atomic_json', fail_last)
    with pytest.raises(OSError):
        worker.run(paths, paths.input, paths.taaled_output, options, False,
                   new_run_id(), lambda _: FakeEngine)
    assert read_status(paths)['state'] == 'complete'


def test_sigkill_releases_lock_and_does_not_publish_partial_run(paths, options):
    paths.engine.write_text('''WORKSHOP_IO_REVISION = 1
import time
from pathlib import Path
def main(indir, outdir, options, *, input_files, progress_queue):
    Path(outdir).write_text('filename,value\\nalpha.txt,')
    progress_queue.put('Synthetic worker waiting for kill')
    time.sleep(60)
''')
    run_id = new_run_id()
    env = dict(os.environ, WORKSHOP_ROOT=str(paths.workspace), WORKSHOP_HOME=str(paths.home))
    env.pop('DISPLAY', None)
    command = [sys.executable, str(Path(worker.__file__)), '--input', str(paths.input),
               '--output-parent', str(paths.taaled_output), '--options', json.dumps(options), '--run-id', run_id]
    child = subprocess.Popen(command, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    partial = paths.taaled_output / (run_id + '.incomplete') / 'taaled.csv'
    try:
        deadline = time.monotonic() + 8
        while not partial.exists() and time.monotonic() < deadline:
            assert child.poll() is None
            time.sleep(.02)
        assert partial.exists()
        assert worker_active(paths.state)
        second = subprocess.run(command, env=env, capture_output=True, timeout=8)
        assert second.returncode == 75
        child.kill()
        child.wait(timeout=3)
        assert not worker_active(paths.state)
        assert read_status(paths)['state'] == 'interrupted'
        assert not (paths.taaled_output / run_id).exists()
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()
