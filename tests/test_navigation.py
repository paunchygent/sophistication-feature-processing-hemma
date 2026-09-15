from pathlib import Path
import importlib.util
from conftest import SUPPORT

spec = importlib.util.spec_from_file_location('navigation_installer', SUPPORT / 'bin/install-navigation.py')
nav = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nav)


def test_navigation_is_general_and_idempotent(paths):
    paths.ellipse_train.mkdir(parents=True)
    paths.ellipse_test.mkdir(parents=True)
    paths.private_cohort.mkdir(parents=True)
    nav.apply(paths)
    nav.apply(paths)
    assert (paths.navigation / '00 Hemma Home').resolve() == paths.browse_root
    assert (paths.navigation / '10 ELLIPSE train').resolve() == paths.ellipse_train
    assert (paths.navigation / '20 Private cohort').resolve() == paths.private_cohort
    assert (paths.navigation / '30 Workshop texts').resolve() == paths.input


def test_missing_optional_dataset_is_not_invented(paths):
    nav.apply(paths)
    assert not (paths.navigation / '10 ELLIPSE train').exists()


def test_existing_navigation_is_preserved(paths):
    paths.navigation.mkdir(parents=True)
    conflict = paths.navigation / '00 Hemma Home'
    conflict.mkdir()
    (conflict / 'keep.txt').write_text('private preexisting content')
    try:
        nav.apply(paths)
    except ValueError as exc:
        assert 'already exists' in str(exc)
    else:
        raise AssertionError('expected a collision')
    assert (conflict / 'keep.txt').read_text() == 'private preexisting content'
