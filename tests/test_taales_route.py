import os
from pathlib import Path
import tkinter as tk
import pytest
import workshop_taales as route
from conftest import SUPPORT
pytestmark = pytest.mark.skipif(not os.environ.get('DISPLAY'), reason='Requires a test X server')


def test_route_card_preserves_binary_cwd_and_does_not_invent_flags(paths, monkeypatch):
    binary = paths.workspace / 'tools/taales_2.2/TAALES_2.2'
    binary.parent.mkdir(parents=True)
    binary.write_text('synthetic executable placeholder')
    binary.chmod(0o700)
    monkeypatch.setenv('WORKSHOP_ROOT', str(paths.workspace))
    monkeypatch.setenv('WORKSHOP_HOME', str(paths.home))
    root = tk.Tk()
    monkeypatch.setattr(route.tk, 'Tk', lambda: root)
    calls = []
    monkeypatch.setattr(route.subprocess, 'Popen', lambda args, **kwargs: calls.append((args, kwargs)) or object())
    def widgets(parent):
        for widget in parent.winfo_children():
            yield widget
            yield from widgets(widget)
    def interact():
        root.update()
        button = next(w for w in widgets(root) if 'text' in w.keys() and w.cget('text') == 'Launch TAALES')
        button.invoke()
        button.invoke()
    monkeypatch.setattr(root, 'mainloop', interact)
    try:
        route.main()
        assert len(calls) == 1
        args, kwargs = calls[0]
        assert args == [str(SUPPORT / 'bin/launch-taales-window'), str(binary)]
        assert kwargs['cwd'] == binary.parent
        notes = list((paths.output / 'taales').glob('*/RUN-NOTES.txt'))
        assert len(notes) == 1
        assert 'NOT a completion receipt' in notes[0].read_text()
        assert 'output prefix' in notes[0].read_text()
    finally:
        root.destroy()
