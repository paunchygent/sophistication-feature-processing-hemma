#!/usr/bin/env python3
"""Create a source-only release from DISTRIBUTION.txt; never walk runtime trees."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile


def package(output: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    output = output.resolve()
    if output == root or root in output.parents:
        raise ValueError('Write the archive outside the support tree')
    entries = []
    for line in (root / 'DISTRIBUTION.txt').read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        relative = Path(line)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Only explicit relative source files may be packaged')
        path = root / relative
        if any((root / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
            raise ValueError(f'Symlinks are not packaged: {line}')
        if not path.is_file():
            raise ValueError(f'Missing source file: {line}')
        allowed_names = {'Dockerfile', 'requirements.txt', 'workshop-launch',
                         'launch-taales-window', '50-workshop-setup', '.gitignore'}
        if path.suffix.lower() not in {'.py', '.md', '.txt', '.json', '.desktop', '.command', '.sh', '.yaml'} and path.name not in allowed_names:
            raise ValueError(f'Unexpected file type: {line}')
        entries.append((relative.as_posix(), path))
    if len({name for name, _ in entries}) != len(entries):
        raise ValueError('Duplicate distribution entry')
    checksums = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in entries}
    # "x" refuses to replace a previous release archive.
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, path in entries:
            archive.write(path, 'gothenburg-workshop-candidate/' + name)
        archive.writestr('gothenburg-workshop-candidate/SHA256SUMS.json', json.dumps(checksums, indent=2) + '\n')
    print(f'Packaged {len(entries)} explicit source/documentation files: {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    package(parser.parse_args().output)
