"""Synthetic adapter tests. They are not spaCy/ICNALE numerical validation."""
import ast
import csv
import importlib.util
import os
from pathlib import Path
import queue
import sys
import types
import pytest
from conftest import SUPPORT


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def core(tmp_path, monkeypatch):
    folder = tmp_path / 'core'
    folder.mkdir()
    candidate = folder / 'TAALED_1_4_1_Hemma.py'
    candidate.write_bytes((SUPPORT / 'app/taaled/TAALED_1_4_1_Hemma.py').read_bytes())
    deps = folder / 'dep_files'
    deps.mkdir()
    (deps / 'adj_lem_list.txt').write_text('quick\n')
    (deps / 'real_words.txt').write_text('the\nbirds\nsing\nquickly\n')
    tokens = [types.SimpleNamespace(text=t, tag_=tag, lemma_=lemma, dep_=dep)
              for t, tag, lemma, dep in [('the','DT','the','det'),('birds','NNS','bird','nsubj'),
                                        ('sing','VB','sing','ROOT'),('quickly','RB','quickly','advmod')]]
    class FakeNLP:
        pipe_names = ["synthetic"]
        def __call__(self, text):
            return types.SimpleNamespace(sents=[tokens])
        def pipe(self, records, *, as_tuples, batch_size, n_process):
            assert as_tuples
            for text, context in records:
                yield self(text), context
    monkeypatch.setitem(sys.modules, 'spacy', types.SimpleNamespace(load=lambda name: FakeNLP()))
    return load(candidate, 'candidate_core'), folder


def test_engine_resources_are_not_relative_to_launcher_cwd(core, tmp_path, monkeypatch):
    engine, folder = core
    monkeypatch.chdir(tmp_path)
    assert Path(engine.resource_path('dep_files/real_words.txt')) == folder / 'dep_files/real_words.txt'


def test_core_validates_without_tk_or_model_calls(core):
    engine, _ = core
    with pytest.raises(ValueError):
        engine.main('', '', {})


def test_actual_core_csv_handles_comma_and_closes_files(core, paths, options):
    engine, _ = core
    options['indout'] = 1
    result = paths.taaled_output / 'new.csv'
    engine.main(str(paths.input), str(result), options, progress_queue=queue.Queue())
    with result.open(newline='') as f:
        rows = list(csv.reader(f))
    assert rows[2][0] == 'beta, quoted.txt'
    assert all(len(row) == len(rows[0]) for row in rows)
    assert len(list((paths.taaled_output / 'new_diagnostic').iterdir())) == 2
    before = result.read_bytes()
    with pytest.raises(FileExistsError):
        engine.main(str(paths.input), str(result), options, progress_queue=queue.Queue())
    assert result.read_bytes() == before


def test_calculation_asts_match_uploaded_baseline():
    baseline = os.environ.get('BASELINE_TAALED')
    if not baseline:
        pytest.skip('Set BASELINE_TAALED to the supplied patched source for the invariance comparison')
    old = ast.parse(Path(baseline).read_text())
    new = ast.parse((SUPPORT / 'app/taaled/TAALED_1_4_1_Hemma.py').read_text())
    def functions(tree):
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        return {n.name: ast.dump(n, include_attributes=False) for n in main.body if isinstance(n, ast.FunctionDef)}
    assert len(functions(old)) == 15
    old_functions, new_functions = functions(old), functions(new)
    # Annotation moved out of the classifier. All fourteen measure/helper functions
    # must remain exactly unchanged; classifier statements are checked separately.
    del old_functions['tag_processor_spaCy'], new_functions['tag_processor_spaCy']
    assert old_functions == new_functions
    def classifier(tree):
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'tag_processor_spaCy')
        node.args.args[0].arg = 'tagged_text'
        node.body = [n for n in node.body if not (
            isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
            and isinstance(n.value.func, ast.Name) and n.value.func.id == 'nlp')]
        return ast.dump(node, include_attributes=False)
    assert classifier(old) == classifier(new)


def test_baseline_and_candidate_same_values_with_synthetic_nlp(core, tmp_path, monkeypatch):
    baseline = os.environ.get('BASELINE_TAALED')
    if not baseline:
        pytest.skip('Set BASELINE_TAALED; no baseline source is shipped in the distributable support tree')
    engine, folder = core
    original = load(Path(baseline), 'snapshot_core')
    monkeypatch.setattr(original, 'resource_path', engine.resource_path)
    monkeypatch.chdir(folder)
    input_dir = tmp_path / 'synthetic'
    input_dir.mkdir()
    (input_dir / 'one.txt').write_text('The birds sing quickly.')
    from workshop_common import OPTION_KEYS
    options = {key: 1 for key in OPTION_KEYS}
    options['indout'] = 0
    old = tmp_path / 'baseline.csv'
    new = tmp_path / 'candidate.csv'
    original.main(str(input_dir), str(old), options)
    engine.main(str(input_dir), str(new), options)
    with old.open(newline='') as first, new.open(newline='') as second:
        assert list(csv.reader(first)) == list(csv.reader(second))


def test_pipe_is_single_ordered_call_with_lazy_context(core, paths, options, monkeypatch):
    engine, _ = core
    calls = []
    class NLP:
        pipe_names = ['synthetic']
        def __call__(self, text):
            raise AssertionError('Per-document nlp(text) must not remain')
        def pipe(self, records, **kwargs):
            calls.append(kwargs)
            assert iter(records) is records
            for text, filename in records:
                assert '\n' not in text
                tokens = [types.SimpleNamespace(text='birds', tag_='NNS', lemma_='bird', dep_='ROOT')]
                yield types.SimpleNamespace(sents=[tokens]), filename
    loads = []
    def load_model(name):
        loads.append(name)
        return NLP()
    monkeypatch.setitem(sys.modules, 'spacy', types.SimpleNamespace(load=load_model))
    requested = [str(paths.input / 'beta, quoted.txt'), str(paths.input / 'alpha.txt')]
    output = paths.taaled_output / 'pipe.csv'
    engine.main(str(paths.input), str(output), options, input_files=requested, batch_size=16, n_process=1)
    with output.open(newline='') as source:
        assert [row['filename'] for row in csv.DictReader(source)] == [Path(f).name for f in requested]
    assert loads == ['en_core_web_sm']
    assert calls == [{'as_tuples': True, 'batch_size': 16, 'n_process': 1}]


@pytest.mark.parametrize('mode', ['reversed', 'truncated'])
def test_pipe_identity_violation_is_not_success(core, paths, options, monkeypatch, mode):
    engine, _ = core
    class NLP:
        pipe_names = ['synthetic']
        def pipe(self, records, **kwargs):
            records = list(records)
            records = records[::-1] if mode == 'reversed' else records[:1]
            for text, filename in records:
                tokens = [types.SimpleNamespace(text='birds', tag_='NNS', lemma_='bird', dep_='ROOT')]
                yield types.SimpleNamespace(sents=[tokens]), filename
    monkeypatch.setitem(sys.modules, 'spacy', types.SimpleNamespace(load=lambda _: NLP()))
    with pytest.raises(ValueError, match='Annotation stream'):
        engine.main(str(paths.input), str(paths.taaled_output / 'bad.csv'), options)


def test_invalid_process_count_rejected_before_model_or_output(core, paths, options):
    engine, _ = core
    with pytest.raises(ValueError, match='n_process'):
        engine.main(str(paths.input), str(paths.taaled_output / 'bad.csv'), options, n_process=-1)
    assert not (paths.taaled_output / 'bad.csv').exists()
