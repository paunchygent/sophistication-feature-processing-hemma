import sys
from pathlib import Path
import pytest
SUPPORT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SUPPORT / 'app/taaled'))
from workshop_common import Paths, OPTION_KEYS

@pytest.fixture
def paths(tmp_path):
    paths = Paths(tmp_path / 'runtime workspace', tmp_path / 'config')
    paths.input.mkdir(parents=True)
    (paths.input / 'alpha.txt').write_text('Synthetic fixture text, not a workshop essay.\n')
    (paths.input / 'beta, quoted.txt').write_text('Another synthetic fixture text.\n')
    paths.taaled_output.mkdir(parents=True)
    (paths.workspace / 'smoke-input').mkdir()
    paths.engine.parent.mkdir(parents=True)
    (paths.engine.parent / 'dep_files').mkdir()
    for name in ('adj_lem_list.txt', 'real_words.txt'):
        (paths.engine.parent / 'dep_files' / name).write_text('synthetic\n')
    paths.engine.write_text('# Test double only\n')
    return paths

@pytest.fixture
def options():
    result = {key: 0 for key in OPTION_KEYS}
    result.update(aw=1, mattr=1)
    return result
