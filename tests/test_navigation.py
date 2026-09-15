from pathlib import Path
import importlib.util
import pytest
from conftest import SUPPORT
spec = importlib.util.spec_from_file_location('navigation_installer', SUPPORT / 'bin/install-navigation.py')
nav = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nav)


def test_plan_apply_idempotence_and_selective_rollback(paths, capsys):
    nav.apply(paths, SUPPORT, False)
    assert not paths.navigation.exists()
    nav.apply(paths, SUPPORT, True)
    nav.apply(paths, SUPPORT, True)
    assert (paths.navigation / '10 Workshop Texts').resolve() == paths.input
    assert not any('hemma-home' in str(p.resolve()) for p in paths.navigation.iterdir())
    modified = paths.home / 'Desktop/gothenburg-start.desktop'
    modified.write_text(modified.read_text() + '# operator modification\n')
    nav.rollback(paths)
    assert modified.exists()
    assert not (paths.navigation / '10 Workshop Texts').exists()
    assert not (paths.home / 'Desktop/gothenburg-taaled.desktop').exists()


def test_preexisting_navigation_is_preserved(paths):
    paths.navigation.mkdir(parents=True)
    conflict = paths.navigation / '10 Workshop Texts'
    conflict.mkdir()
    (conflict / 'keep.txt').write_text('private preexisting content')
    with pytest.raises(ValueError, match='conflicts'):
        nav.apply(paths, SUPPORT, True)
    assert (conflict / 'keep.txt').read_text() == 'private preexisting content'
    assert not (paths.home / 'Desktop').exists()


def test_preexisting_identical_items_not_claimed(paths):
    paths.navigation.mkdir(parents=True)
    link = paths.navigation / '10 Workshop Texts'
    link.symlink_to(paths.input)
    nav.apply(paths, SUPPORT, True)
    nav.rollback(paths)
    assert link.is_symlink()
