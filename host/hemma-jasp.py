#!/usr/bin/env python3
"""One socket-activated host JASP invocation. No arbitrary command/path protocol."""
from __future__ import annotations

import os
from pathlib import Path
import socket
import struct
import subprocess
import sys

APP = "org.jaspstats.JASP"
WORKSPACE = Path("/srv/hemma-workstation/workspace")
X11 = Path("/tmp/.X11-unix")  # Host bind mount of the owner's shared X socket directory.
REQUEST = b"JASP/1\n"


def command():
    # Flatpak runs on the HOST, not in Docker. Its normal sandbox remains enabled.
    return ["/usr/bin/flatpak", "run", "--user", "--socket=x11", "--nosocket=wayland",
            "--filesystem=home", f"--filesystem={WORKSPACE}",
            "--env=QT_QPA_PLATFORM=xcb", "--env=QT_XCB_NO_MITSHM=1",
            APP]


def serve(connection, home=None):
    home = Path.home() if home is None else Path(home)
    state = home / ".local/state/hemma-workstation"
    connection.settimeout(5)
    # Ordinary rootful Docker must preserve the host user's numeric UID.
    _, uid, _ = struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
    if uid != os.getuid():
        raise PermissionError("The launch socket requires the workstation owner's UID")
    with connection.makefile("rb") as source:
        if source.readline(16) != REQUEST:
            raise ValueError("Only the fixed JASP/1 launch request is accepted")
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    auth = state / "xauth/Xauthority"
    if not auth.is_file():
        raise RuntimeError("Host Xauthority is missing")
    if subprocess.run(["/usr/bin/mountpoint", "-q", str(WORKSPACE)]).returncode:
        raise RuntimeError("The durable workspace bind mount is not active")
    if subprocess.run(["/usr/bin/mountpoint", "-q", str(X11)]).returncode:
        raise RuntimeError("The host X11 socket directory bind mount is not active")
    env = dict(os.environ, HOME=str(home), DISPLAY=":1", XAUTHORITY=str(auth))
    env.pop("WAYLAND_DISPLAY", None)
    # A single preflight, not a wait/retry loop. Do not open JASP on another display.
    check = subprocess.run(["/usr/bin/xdpyinfo"], env=env, capture_output=True, timeout=5)
    if check.returncode:
        raise RuntimeError("Cannot authenticate to workstation X11 display :1")
    subprocess.run(["/usr/bin/flatpak", "info", "--user", APP],
                   check=True, stdout=subprocess.DEVNULL, timeout=10)
    child = subprocess.Popen(command(), env=env, cwd=home,
                             stdin=subprocess.DEVNULL, close_fds=True)
    # An acknowledgement means process creation, NOT a visible/working JASP window.
    # Loss of the client after launch does not cancel this host-side application.
    try:
        connection.sendall(b"OK JASP launch requested; verify its window on the desktop.\n")
    except (BrokenPipeError, ConnectionResetError):
        pass
    connection.close()
    return child.wait()


def main():
    os.umask(0o077)
    with socket.socket(fileno=0) as connection:  # StandardInput=socket from systemd.
        try:
            return serve(connection)
        except Exception as exc:
            message = f"JASP host launch failed: {type(exc).__name__}: {exc}"
            print(message, file=sys.stderr)
            try:
                connection.sendall(("ERROR " + message + "\n").encode()[:2048])
            except OSError:
                pass
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
