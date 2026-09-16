"""Local contract tests, not a host Flatpak/real-browser launch proof."""
import importlib.util
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import types

import pytest
from conftest import SUPPORT
from workshop_performance import Performance
from workshop_worker import Progress
from workshop_common import load_json, validate_csv


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_process_policy_reserves_affinity_headroom(monkeypatch):
    monkeypatch.setattr(os, 'sched_getaffinity', lambda _: set(range(4)))
    assert Performance(64, 2).n_process == 2
    with pytest.raises(ValueError, match='headroom'):
        Performance(64, 4)
    for value in (-1, 0, 8, True):
        with pytest.raises(ValueError):
            Performance(64, value)


def test_hot_status_does_not_rewrite_input_inventory(tmp_path):
    record = {'run_id': 'test', 'inputs': [{'name': str(n)} for n in range(8035)]}
    target = tmp_path / 'status.json'
    Progress(target, record).put('Working')
    assert 'inputs' not in load_json(target)
    assert len(record['inputs']) == 8035


def test_csv_order_is_part_of_identity(tmp_path):
    output = tmp_path / 'test.csv'
    output.write_text('filename,value\nb.txt,1\na.txt,2\n')
    with pytest.raises(ValueError, match='in order'):
        validate_csv(output, [{'name': 'a.txt'}, {'name': 'b.txt'}])


def test_xauth_build_patch_refuses_drift_and_preserves_tcp_off(tmp_path):
    helper = load('xauth_patch', SUPPORT / 'bin/require-xauth.py')
    launcher = tmp_path / 'run'
    old = '/usr/bin/Xvfb ' + chr(92) + '\n    -nolisten "tcp" ' + chr(92) + '\n    -ac ' + chr(92) + '\n'
    launcher.write_text(old)
    helper.patch(launcher)
    assert '-auth /run/workstation-xauth/Xauthority' in launcher.read_text()
    assert '-nolisten "tcp"' in launcher.read_text()
    assert '-ac ' not in launcher.read_text()
    with pytest.raises(SystemExit, match='Reconcile'):
        helper.patch(launcher)


def test_compose_x11_socket_directory_is_outside_snap_private_tmp():
    # Snap Docker's daemon resolves bind sources in a private /tmp, so the shared X
    # socket directory must come from owner state and appear as /tmp/.X11-unix inside.
    text = (SUPPORT / 'compose.yaml').read_text()
    assert 'source: /tmp/.X11-unix' not in text
    assert 'source: ${HEMMA_HOME_PATH:-/home/paunchygent}/.local/state/hemma-workstation/x11' in text
    assert '        target: /tmp/.X11-unix\n' in text


def test_host_jasp_command_is_fixed_and_uses_no_sandbox_bypass():
    host = load('host_jasp', SUPPORT / 'host/hemma-jasp.py')
    command = host.command()
    assert command[:3] == ['/usr/bin/flatpak', 'run', '--user']
    assert '--env=QT_XCB_NO_MITSHM=1' in command
    assert '--filesystem=home' in command
    assert '--filesystem=/srv/hemma-workstation/workspace' in command
    assert command[-1] == 'org.jaspstats.JASP'
    assert '--safeGraphics' not in command
    assert not any('no-sandbox' in value or 'privileged' in value for value in command)


def test_host_rejects_arbitrary_requests_before_launch(tmp_path):
    host = load('host_jasp', SUPPORT / 'host/hemma-jasp.py')
    server, client = socket.socketpair()
    with server, client:
        client.sendall(b'run shell\n')
        with pytest.raises(ValueError, match='fixed'):
            host.serve(server, tmp_path)


def test_socket_roundtrip_closing_client_does_not_cancel_host_child(tmp_path, monkeypatch):
    host = load('host_jasp', SUPPORT / 'host/hemma-jasp.py')
    client_module = load('jasp_client', SUPPORT / 'app/jasp_client.py')
    auth = tmp_path / '.local/state/hemma-workstation/xauth/Xauthority'
    auth.parent.mkdir(parents=True)
    auth.write_text('synthetic cookie placeholder')
    monkeypatch.setattr(host.subprocess, 'run', lambda *a, **k: types.SimpleNamespace(returncode=0))
    released = threading.Event()
    calls = []
    class Child:
        def wait(self):
            assert released.wait(3)
            return 0
    monkeypatch.setattr(host.subprocess, 'Popen', lambda args, **kwargs: calls.append((args, kwargs)) or Child())
    listener = socket.socket(socket.AF_UNIX)
    socket_path = str(tmp_path / 'jasp.sock')
    listener.bind(socket_path)
    listener.listen(1)
    errors = []
    def server():
        try:
            connection, _ = listener.accept()
            with connection:
                assert host.serve(connection, tmp_path) == 0
        except BaseException as exc:
            errors.append(exc)
    thread = threading.Thread(target=server)
    thread.start()
    try:
        reply = client_module.request(socket_path)
        assert 'launch requested' in reply
        assert thread.is_alive()  # Waiting for application, not the GUI client connection.
        assert calls[0][1]['env']['DISPLAY'] == ':1'
        assert calls[0][1]['cwd'] == tmp_path
    finally:
        released.set()
        thread.join(4)
        listener.close()
    assert not errors


def test_real_xvfb_accepts_cookie_and_rejects_no_cookie(tmp_path):
    import secrets
    import shutil
    import time
    if not all(shutil.which(c) for c in ('Xvfb', 'xauth', 'xdpyinfo')):
        pytest.skip('Xvfb/xauth/xdpyinfo required')
    display = next(f':{n}' for n in range(151, 200)
                   if not Path(f'/tmp/.X11-unix/X{n}').exists())
    raw, auth = tmp_path / 'raw', tmp_path / 'Xauthority'
    raw.touch(mode=0o600)
    auth.touch(mode=0o600)
    subprocess.run(['xauth', '-f', str(raw), 'add', display, 'MIT-MAGIC-COOKIE-1', secrets.token_hex(16)], check=True)
    entries = subprocess.check_output(['xauth', '-f', str(raw), 'nlist'])
    wild = b''.join(b'ffff' + line[4:] + b'\n' for line in entries.splitlines())
    subprocess.run(['xauth', '-f', str(auth), 'nmerge', '-'], input=wild, check=True)
    server = subprocess.Popen(['Xvfb', display, '-screen', '0', '1024x768x24',
                               '-nolisten', 'tcp', '-auth', str(auth), '-noreset'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + 5
        while not Path('/tmp/.X11-unix/X' + display[1:]).exists() and time.monotonic() < deadline:
            assert server.poll() is None
            time.sleep(.02)
        good = dict(os.environ, DISPLAY=display, XAUTHORITY=str(auth))
        bad = dict(good, XAUTHORITY=str(tmp_path / 'absent'))
        assert subprocess.run(['xdpyinfo'], env=good, capture_output=True, timeout=3).returncode == 0
        assert subprocess.run(['xdpyinfo'], env=bad, capture_output=True, timeout=3).returncode != 0
    finally:
        server.terminate()
        server.wait(timeout=5)
