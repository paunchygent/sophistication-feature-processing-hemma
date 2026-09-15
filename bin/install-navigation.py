#!/usr/bin/env python3
"""Create the disposable service's navigation links."""
from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app/taaled"))
from workshop_common import Paths


def desired(paths: Paths) -> dict[Path, Path]:
    return {
        paths.navigation / "00 Hemma Home": paths.browse_root,
        paths.navigation / "10 ELLIPSE train": paths.ellipse_train,
        paths.navigation / "11 ELLIPSE test": paths.ellipse_test,
        paths.navigation / "20 Private cohort": paths.private_cohort,
        paths.navigation / "30 Workshop texts": paths.input,
        paths.navigation / "80 Service output": paths.output,
        paths.navigation / "90 All service data": paths.workspace,
    }


def apply(paths: Paths) -> None:
    paths.navigation.mkdir(parents=True, exist_ok=True)
    for link, target in desired(paths).items():
        if not target.is_dir():
            continue
        # These declared aliases are disposable UI state. Repoint only the link
        # itself when the shared namespace changes; never touch its old target.
        if link.is_symlink():
            if os.readlink(link) == str(target):
                continue
            link.unlink()
        elif link.exists():
            raise ValueError(f"Navigation item already exists: {link}")
        link.symlink_to(target, target_is_directory=True)


def main() -> None:
    apply(Paths.environment())


if __name__ == "__main__":
    main()
