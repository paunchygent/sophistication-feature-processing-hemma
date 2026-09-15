#!/usr/bin/env python3
"""Plan/apply owned navigation additions. Conflicts are not replaced or erased."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app/taaled"))
from workshop_common import Paths, atomic_json, load_json

ENTRIES = (
    ("start", "00 Start Here", "Workshop routes and recovery notes", "help-browser"),
    ("taales", "TAALES 2.2", "Lexical sophistication — input and output route card", "accessories-text-editor"),
    ("taaled", "TAALED 1.4.1", "Lexical diversity — workshop GUI", "accessories-text-editor"),
    ("files", "Workshop Files", "Input, smoke input, materials and outputs", "system-file-manager"),
    ("output", "Workshop Output", "Generated runtime results, never distributable source", "folder-documents"),
    ("display", "Display and Fonts", "XFCE appearance settings; TAALED has separate Text DPI", "preferences-desktop-display"),
)


def entry(action, name, comment, icon, support):
    # Deliberately narrow installed-prefix contract; reject instead of inventing Exec quoting.
    executable = str(support / "bin/workshop-launch")
    if any(c in executable for c in '\n\r\t"`$\\%'):
        raise ValueError("Unsupported character in support prefix")
    return (f"[Desktop Entry]\nType=Application\nName={name}\nComment={comment}\n"
            f'Exec="{executable}" {action}\nTerminal=false\nIcon={icon}\n'
            "Categories=Education;Science;\nKeywords=workshop;lexical;TAALES;TAALED;\nStartupNotify=false\n")


def desired(paths, support):
    # These are links only, never copies and never a security boundary.
    links = {
        paths.navigation / "10 Workshop Texts": paths.input,
        paths.navigation / "20 Smoke Input": paths.workspace / "smoke-input",
        paths.navigation / "30 Output": paths.output,
        paths.navigation / "40 Materials": paths.workspace / "materials",
    }
    files = {}
    for action, name, comment, icon in ENTRIES:
        text = entry(action, name, comment, icon, support)
        for directory in (paths.home / "Desktop", paths.home / ".local/share/applications"):
            files[directory / f"gothenburg-{action}.desktop"] = text
    return links, files


def apply(paths, support, write):
    links, files = desired(paths, support)
    for target in links.values():
        if not target.is_dir():
            raise ValueError(f"Required route is absent: {target}")
    for link, target in links.items():
        if link.exists() or link.is_symlink():
            if not link.is_symlink() or os.readlink(link) != str(target):
                raise ValueError(f"Existing navigation item conflicts: {link}")
    for path, text in files.items():
        if path.is_symlink() or (path.exists() and (not path.is_file() or path.read_text() != text)):
            raise ValueError(f"Existing launcher conflicts: {path}")
    for link, target in links.items():
        print(f"link {link} -> {target}")
    for path in files:
        print(f"launcher {path}")
    if not write:
        return
    statefile = paths.state / "navigation-owned.json"
    owned = load_json(statefile).get("items", [])
    # Each create is journaled immediately; do not take ownership of pre-existing items.
    for link, target in links.items():
        if not link.is_symlink():
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(target, target_is_directory=True)
            owned.append({"path": str(link), "link": str(target)})
            atomic_json(statefile, {"items": owned})
    for path, text in files.items():
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as stream:
                stream.write(text)
            path.chmod(0o755)  # XFCE may additionally require a user trust confirmation.
            owned.append({"path": str(path), "sha256": hashlib.sha256(text.encode()).hexdigest()})
            atomic_json(statefile, {"items": owned})


def rollback(paths):
    statefile = paths.state / "navigation-owned.json"
    state = load_json(statefile)
    links, files = desired(paths, Path("/config/workshop-support"))
    allowed = set(links) | set(files)
    remaining = []
    for item in reversed(state.get("items", [])):
        path = Path(item["path"])
        if path not in allowed:
            raise ValueError("Owned manifest contains an unexpected path")
        if not path.exists() and not path.is_symlink():
            continue
        unchanged = (path.is_symlink() and os.readlink(path) == item.get("link")) if "link" in item else (
            path.is_file() and not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"])
        if unchanged:
            path.unlink()
        else:
            print(f"Preserved modified item: {path}")
            remaining.append(item)
    atomic_json(statefile, {"items": remaining})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Default is a read-only plan")
    parser.add_argument("--rollback", action="store_true", help="Remove only unchanged, recorded additions")
    args = parser.parse_args()
    if args.apply and args.rollback:
        parser.error("Choose apply or rollback, not both")
    paths = Paths.environment()
    if args.rollback:
        rollback(paths)
    else:
        apply(paths, Path(__file__).resolve().parents[1], args.apply)


if __name__ == "__main__":
    main()
