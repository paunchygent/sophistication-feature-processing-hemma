#!/usr/bin/env python3
"""Build-time assertion against the inherited Xvfb launcher; fail on upstream drift."""
from pathlib import Path

def patch(path):
    text = path.read_text()
    old = "    -ac " + chr(92) + "\n"
    new = "    -auth /run/workstation-xauth/Xauthority " + chr(92) + "\n"
    if text.count(old) != 1 or '-nolisten "tcp"' not in text or '/usr/bin/Xvfb' not in text:
        raise SystemExit("Reconcile the pinned image's Xvfb launcher before exporting its X socket")
    path.write_text(text.replace(old, new))


if __name__ == "__main__":
    patch(Path("/etc/s6-overlay/s6-rc.d/svc-xorg/run"))
