import os
from pathlib import Path
import time
import tkinter as tk
from tkinter import ttk
import pytest
import workshop_gui as gui
from workshop_common import read_status

pytestmark = pytest.mark.skipif(not os.environ.get('DISPLAY'), reason='Requires a local test X server')

@pytest.fixture
def app(paths):
    root = tk.Tk()
    application = gui.WorkshopApp(root, paths)
    root.update()
    yield application
    try:
        root.after_cancel(application.poll_id)
        root.destroy()
    except tk.TclError:
        pass


def test_cancel_keeps_selections(app, monkeypatch):
    before = app.input.get(), app.output.get()
    monkeypatch.setattr(gui.filedialog, 'askdirectory', lambda **kwargs: '')
    app.browse_input()
    app.browse_output()
    assert (app.input.get(), app.output.get()) == before


def test_basic_mode_is_explicit_and_disables_index_controls(app):
    assert not app.basic_only.get()
    assert not any(v.get() for v in app.options.values())
    app.basic_only.set(True)
    app.update_controls()
    assert all('disabled' in widget.state() for widget in app.analysis_controls)


@pytest.mark.parametrize('dpi', ['96', '120', '144', '192'])
def test_sticky_run_and_scroll_access_at_small_geometry(app, dpi):
    app.scale.set(dpi)
    app.apply_scale()
    app.root.geometry('760x500')
    app.root.update()
    run = app.run_button
    assert run.winfo_ismapped()
    y = run.winfo_rooty() - app.root.winfo_rooty()
    assert 0 <= y < app.root.winfo_height() - run.winfo_height()
    last = app.analysis_controls[-1]
    last.focus_force()
    app.root.update()
    assert app.canvas.canvasy(0) > 0
    # Options must fit horizontally after reflow.
    for widget in app.analysis_controls:
        assert widget.winfo_rootx() + widget.winfo_width() <= app.canvas.winfo_rootx() + app.canvas.winfo_width()


def test_gui_close_reopen_observes_detached_worker(app, paths, monkeypatch):
    paths.engine.write_text('''WORKSHOP_IO_REVISION = 1
import time, csv
from pathlib import Path
def main(indir, outdir, options, *, input_files, progress_queue):
    progress_queue.put('Synthetic delayed run')
    time.sleep(1.5)
    with open(outdir, 'x', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['filename','synthetic_value'])
        writer.writerows((Path(f).name, 1) for f in input_files)
''')
    app.options['aw'].set(1)
    app.options['mattr'].set(1)
    app.start()
    child = app.child
    assert child is not None
    deadline = time.monotonic() + 6
    while not read_status(paths).get('active') and time.monotonic() < deadline:
        app.root.update()
        time.sleep(.01)
    monkeypatch.setattr(gui.messagebox, 'askyesno', lambda *a, **k: True)
    app.close()
    assert child.poll() is None
    second_root = tk.Tk()
    second = gui.WorkshopApp(second_root, paths)
    try:
        second_root.update()
        assert second.current['active']
        child.wait(timeout=8)
        assert child.returncode == 0
        second.poll()
        assert second.current['state'] == 'complete'
    finally:
        second_root.after_cancel(second.poll_id)
        second_root.destroy()
