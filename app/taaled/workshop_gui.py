"""Responsive TAALED GUI; the legacy engine remains the calculation owner."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, font, messagebox, ttk

from workshop_common import (GROUPS, INDICES, OPTION_KEYS, Paths, atomic_json,
                             input_snapshot, load_json, new_run_id, read_status,
                             validate_options, validate_output_root)


class WorkshopApp:
    def __init__(self, root: tk.Tk, paths: Paths | None = None):
        self.root, self.paths = root, paths or Paths.environment()
        self.paths.state.mkdir(parents=True, exist_ok=True)
        self.preferences_path = self.paths.state / "preferences.json"
        try:
            prefs = load_json(self.preferences_path)
        except (OSError, ValueError):
            prefs = {}  # Never overwrite a malformed file until an explicit user action.
        self.child = None
        self.pending_id = None
        self.launch_error = ""
        self.current = {}
        self.controls = []
        self.analysis_controls = []
        self.reflow_groups = []
        self.wrap_labels = []
        self.input_buttons = []
        self.root.title("TAALED 1.4.1 · Sophistication Feature Processing")
        self.system_scaling = float(root.tk.call("tk", "scaling"))
        self.scale = tk.StringVar(value=str(prefs.get("scale", "System")))
        if self.scale.get() not in ("System", "96", "120", "144", "168", "192"):
            self.scale.set("System")
        self._set_fonts()
        self.input = tk.StringVar(value=prefs.get("input", ""))
        self.output = tk.StringVar(value=prefs.get("output", str(self.paths.taaled_output)))
        self.basic_only = tk.BooleanVar(value=bool(prefs.get("basic_only", False)))
        saved_options = prefs.get("options", {})
        if not isinstance(saved_options, dict):
            saved_options = {}
        self.options = {k: tk.IntVar(value=int(saved_options.get(k, 0) == 1)) for k in OPTION_KEYS}
        self.status = tk.StringVar(value="Ready")
        self.count_text = tk.StringVar()

        header = ttk.Frame(root, padding=12)
        header.pack(fill="x")
        ttk.Label(header, text="TAALED · Lexical Diversity", font="WorkshopHeading").pack(anchor="w")
        toolbar = ttk.Frame(header)
        toolbar.pack(fill="x", pady=(8, 0))
        ttk.Button(toolbar, text="Hemma Home", command=lambda: self.open_folder(self.paths.browse_root)).pack(side="left")
        ttk.Button(toolbar, text="Data and results", command=lambda: self.open_folder(self.paths.navigation)).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Instructions", command=self.instructions).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Fit window", command=self.fit_window).pack(side="right")
        scale_row = ttk.Frame(header)
        scale_row.pack(fill="x", pady=(6, 0))
        ttk.Label(scale_row, text="Text DPI:").pack(side="left", padx=(0, 3))
        scale_box = ttk.Combobox(scale_row, textvariable=self.scale, width=7,
                                values=("System", "96", "120", "144", "168", "192"), state="readonly")
        scale_box.pack(side="left")
        scale_box.bind("<<ComboboxSelected>>", self.apply_scale)

        footer = ttk.Frame(root, padding=12)
        footer.pack(side="bottom", fill="x")
        row = ttk.Frame(footer)
        row.pack(fill="x")
        self.run_button = ttk.Button(row, text="Run analysis", command=self.start)
        self.run_button.pack(side="left")
        ttk.Button(row, text="Open run folder", command=self.open_run).pack(side="left", padx=8)
        self.status_label = ttk.Label(footer, textvariable=self.status, wraplength=700, justify="left")
        self.status_label.pack(fill="x", pady=(8, 0))
        footer.bind("<Configure>", lambda e: self.status_label.configure(wraplength=max(200, e.width - 30)))

        middle = ttk.Frame(root)
        middle.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(middle, highlightthickness=0)
        scroll = ttk.Scrollbar(middle, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        body = ttk.Frame(self.canvas, padding=(12, 4, 12, 12))
        self.body_window = self.canvas.create_window((0, 0), window=body, anchor="nw")
        self.body = body
        body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self.reflow)
        root.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-3, "units"))
        root.bind("<Button-5>", lambda e: self.canvas.yview_scroll(3, "units"))
        root.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units"))
        root.bind("<FocusIn>", self.reveal_focus, add="+")
        root.bind("<Control-Home>", lambda e: self.canvas.yview_moveto(0))
        root.bind("<Control-End>", lambda e: self.canvas.yview_moveto(1))

        input_frame = ttk.LabelFrame(body, text="1. Input texts", padding=10)
        input_frame.pack(fill="x", pady=5)
        self.path_entry(input_frame, self.input)
        input_buttons = ttk.Frame(input_frame)
        input_buttons.pack(fill="x", pady=(8, 0))
        for label, command in (("ELLIPSE train", lambda: self.choose_input(self.paths.ellipse_train)),
                               ("ELLIPSE test", lambda: self.choose_input(self.paths.ellipse_test)),
                               ("Private cohort", lambda: self.choose_input(self.paths.private_cohort)),
                               ("Workshop texts", lambda: self.choose_input(self.paths.input)),
                               ("Smoke input", lambda: self.choose_input(self.paths.workspace / "smoke-input")),
                               ("Choose folder…", self.browse_input)):
            button = ttk.Button(input_buttons, text=label, command=command)
            button.grid(row=0, column=len(self.input_buttons), sticky="w", padx=(0, 6), pady=3)
            self.input_buttons.append(button)
            self.controls.append(button)
        count_label = ttk.Label(input_frame, textvariable=self.count_text, wraplength=560)
        count_label.pack(anchor="w", pady=(8, 0))
        self.wrap_labels.append(count_label)

        output_frame = ttk.LabelFrame(body, text="2. Results", padding=10)
        output_frame.pack(fill="x", pady=5)
        self.path_entry(output_frame, self.output)
        ttk.Label(output_frame, text="Each run gets a new folder containing taaled.csv. Existing results are never reused.",
                  wraplength=560).pack(anchor="w", pady=6)
        choose_output = ttk.Button(output_frame, text="Choose results parent…", command=self.browse_output)
        choose_output.pack(anchor="w")
        self.controls.append(choose_output)

        options_frame = ttk.LabelFrame(body, text="3. Options and index selection", padding=10)
        options_frame.pack(fill="x", pady=5)
        mode = ttk.Checkbutton(options_frame, text="Basic counts/density only",
                               variable=self.basic_only, command=self.update_controls)
        mode.pack(anchor="w", pady=(0, 8))
        self.controls.append(mode)
        group = ttk.LabelFrame(options_frame, text="Word analysis options", padding=8)
        group.pack(fill="x", pady=4)
        group_widgets = []
        for i, (key, label) in enumerate(GROUPS):
            button = ttk.Checkbutton(group, text=label, variable=self.options[key])
            button.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 16), pady=4)
            self.analysis_controls.append(button)
            group_widgets.append(button)
        self.reflow_groups.append(group_widgets)
        indices = ttk.LabelFrame(options_frame, text="Index selection", padding=8)
        indices.pack(fill="x", pady=4)
        index_widgets = []
        for i, (key, label) in enumerate(INDICES):
            button = ttk.Checkbutton(indices, text=label, variable=self.options[key])
            button.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 18), pady=4)
            self.analysis_controls.append(button)
            index_widgets.append(button)
        self.reflow_groups.append(index_widgets)
        diagnostics = ttk.Checkbutton(options_frame, text="Individual item output",
                                      variable=self.options["indout"])
        diagnostics.pack(anchor="w", pady=8)
        self.controls.append(diagnostics)
        ttk.Label(options_frame, text="Individual item output contains processed token/type diagnostics.",
                  wraplength=560).pack(anchor="w", pady=(0, 6))
        ttk.Label(options_frame, text="Basic counts and lexical density are always included. No index preset has been selected for you.",
                  wraplength=560).pack(anchor="w")
        self.refresh_count()
        self.fit_window()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.poll_id = self.root.after(0, self.poll)

    def reflow(self, event):
        self.canvas.itemconfigure(self.body_window, width=event.width)
        text_font = font.nametofont("TkDefaultFont", root=self.root)
        for widgets in self.reflow_groups:
            needed = max(text_font.measure(str(w.cget("text"))) for w in widgets) + 60
            columns = 2 if event.width >= 2 * needed + 80 else 1
            for index, widget in enumerate(widgets):
                widget.grid_configure(row=index // columns, column=index % columns)
        if self.input_buttons:
            needed = max(text_font.measure(str(w.cget("text"))) for w in self.input_buttons) + 34
            columns = max(1, min(3, (event.width - 70) // needed))
            for index, widget in enumerate(self.input_buttons):
                widget.grid_configure(row=index // columns, column=index % columns)
        for label in self.wrap_labels:
            label.configure(wraplength=max(200, event.width - 70))

    def _set_fonts(self):
        value = self.scale.get()
        self.root.tk.call("tk", "scaling", self.system_scaling if value == "System" else int(value) / 72.0)
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            font.nametofont(name, root=self.root).configure(size=12)
        if "WorkshopHeading" not in font.names(root=self.root):
            self.heading = font.Font(root=self.root, name="WorkshopHeading", exists=False,
                                     family=font.nametofont("TkDefaultFont", root=self.root).actual("family"),
                                     size=19, weight="bold")
        else:
            font.nametofont("WorkshopHeading", root=self.root).configure(size=19)

    def apply_scale(self, event=None):
        self._set_fonts()
        self.root.update_idletasks()
        self.reflow(type("Size", (), {"width": self.canvas.winfo_width()})())
        self.save_preferences()

    def fit_window(self):
        width = max(320, self.root.winfo_screenwidth() - 80)
        height = max(300, self.root.winfo_screenheight() - 110)
        self.root.minsize(min(620, width), min(430, height))
        self.root.geometry(f"{min(1080, width)}x{min(840, height)}+24+32")

    def path_entry(self, parent, variable):
        entry = ttk.Entry(parent, textvariable=variable, state="readonly")
        entry.pack(fill="x")
        return entry

    def reveal_focus(self, event):
        # Tab navigation also scrolls focused options into view on small screens.
        widget = event.widget
        if str(widget).startswith(str(self.body) + "."):
            self.root.update_idletasks()
            y = widget.winfo_rooty() - self.body.winfo_rooty()
            top = self.canvas.canvasy(0)
            bottom = top + self.canvas.winfo_height()
            if y < top or y + widget.winfo_height() > bottom:
                self.canvas.yview_moveto(max(0, y - 20) / max(1, self.body.winfo_height()))

    def choose_input(self, path):
        self.input.set(str(path))
        self.refresh_count()

    def browse_input(self):
        initial = self.paths.browse_root if self.paths.browse_root.is_dir() else self.paths.workspace
        choice = filedialog.askdirectory(parent=self.root, initialdir=str(initial), mustexist=True,
                                         title="Select the folder containing the .txt files")
        if choice:  # Cancel preserves the previous selection.
            self.choose_input(Path(choice))

    def browse_output(self):
        initial = self.paths.browse_root if self.paths.browse_root.is_dir() else self.paths.output
        choice = filedialog.askdirectory(parent=self.root, initialdir=str(initial), mustexist=True,
                                         title="Select a results parent under Hemma Home or service output")
        if choice:
            try:
                self.output.set(str(validate_output_root(Path(choice), self.paths)))
            except ValueError as exc:
                messagebox.showerror("Results folder", str(exc), parent=self.root)

    def refresh_count(self):
        try:
            count = len(input_snapshot(Path(self.input.get())))
            self.count_text.set(f"{count} visible .txt files · this folder only, not subfolders")
        except (OSError, ValueError) as exc:
            self.count_text.set("Input needs attention: " + str(exc))

    def save_preferences(self):
        try:
            atomic_json(self.preferences_path, {"input": self.input.get(), "output": self.output.get(),
                        "options": {k: v.get() for k, v in self.options.items()},
                        "basic_only": self.basic_only.get(), "scale": self.scale.get()})
        except OSError as exc:
            messagebox.showwarning("Settings not saved", str(exc), parent=self.root)

    def update_controls(self):
        busy = bool(self.current.get("active")) or (self.child is not None and self.child.poll() is None)
        self.run_button.state(["disabled"] if busy else ["!disabled"])
        for widget in self.controls:
            widget.state(["disabled"] if busy else ["!disabled"])
        for widget in self.analysis_controls:
            widget.state(["disabled"] if busy or self.basic_only.get() else ["!disabled"])

    def start(self):
        if self.child is not None and self.child.poll() is None:
            return
        try:
            current = read_status(self.paths)
            if current.get("active"):
                self.status.set("Another TAALED analysis is running. This window will show its status.")
                return
            input_snapshot(Path(self.input.get()))
            options = validate_options({k: v.get() for k, v in self.options.items()}, self.basic_only.get())
            output = validate_output_root(Path(self.output.get()), self.paths)
            self.save_preferences()
            run_id = new_run_id()
            command = [sys.executable, str(Path(__file__).with_name("workshop_worker.py")),
                       "--input", self.input.get(), "--output-parent", str(output),
                       "--options", json.dumps(options), "--run-id", run_id]
            if self.basic_only.get():
                command.append("--basic-only")
            launch_log = self.paths.state / f"launch-{run_id}.log"
            environment = dict(os.environ)
            environment.update(WORKSHOP_ROOT=str(self.paths.workspace), WORKSHOP_HOME=str(self.paths.home))
            # The worker needs no X session and must never create a Tk dialog.
            environment.pop("DISPLAY", None)
            with launch_log.open("x", encoding="utf-8") as log:
                os.chmod(launch_log, 0o600)
                self.child = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                              stdout=log, stderr=log, env=environment,
                                              start_new_session=True, close_fds=True)
            self.pending_id = run_id
            self.launch_error = ""
            self.status.set("Starting analysis…")
            self.update_controls()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Cannot start analysis", str(exc), parent=self.root)

    def poll(self):
        try:
            self.current = read_status(self.paths)
            if self.child is not None and self.child.poll() is not None:
                code = self.child.returncode
                if code not in (0, 75) and self.current.get("run_id") != self.pending_id:
                    self.launch_error = f"Could not start analysis. See {self.paths.state}/launch-{self.pending_id}.log locally."
                self.child = None
                self.pending_id = None
            starting = self.child is not None and self.current.get("run_id") != self.pending_id
            self.status.set(self.launch_error or ("Starting analysis…" if starting else self.current.get("message", "Ready")))
            self.update_controls()
        except (OSError, ValueError, KeyError) as exc:
            self.status.set("Cannot read run state: " + str(exc))
            self.current = {"active": True}  # Fail closed; do not bypass the lock/status problem.
            self.update_controls()
        self.poll_id = self.root.after(250, self.poll)

    def open_folder(self, path):
        path = Path(path)
        if not path.is_dir():
            messagebox.showinfo("Folder unavailable", f"This folder is not present: {path}", parent=self.root)
            return
        try:
            subprocess.Popen(["pcmanfm-qt", str(path)], stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError as exc:
            messagebox.showerror("File manager", str(exc), parent=self.root)

    def open_run(self):
        self.open_folder(self.current.get("run_directory", self.output.get()))

    def instructions(self):
        messagebox.showinfo("TAALED instructions",
            "1. Select any folder of .txt files. Hemma Home is the default browsing root; dataset buttons are optional shortcuts.\n\n"
            "2. Results go into a new run folder under the selected parent.\n\n"
            "3. Choose the required word groups and indices, or explicitly choose basic counts only.\n\n"
            "4. Run analysis. Only a completed run folder is a completed result.\n\n"
            "Closing this window does not stop its worker. Reopen TAALED to view status. A container restart "
            "can interrupt processing; preserve .incomplete output and start a new run.\n\n"
            "The current spaCy/model environment is recorded. Equality with supplied historical reference "
            "results has not been established.", parent=self.root)

    def close(self):
        if self.current.get("active") or (self.child is not None and self.child.poll() is None):
            if not messagebox.askyesno("Close the window?",
                "Analysis continues independently of this window while its worker/container stays running. "
                "Reopen TAALED to see status. Close this window?", parent=self.root):
                return
        self.save_preferences()
        self.root.after_cancel(self.poll_id)
        self.root.destroy()


def main():
    os.umask(0o077)
    root = tk.Tk()
    WorkshopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
