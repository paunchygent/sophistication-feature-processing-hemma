"""Route card for the opaque TAALES binary. Does not pretend to set its pickers."""
import os
from pathlib import Path
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk

from workshop_common import Paths, new_run_id


def main():
    os.umask(0o077)
    paths = Paths.environment()
    binary = paths.workspace / "tools/taales_2.2/TAALES_2.2"
    window_launcher = Path(__file__).resolve().parents[2] / "bin/launch-taales-window"
    root = tk.Tk()
    root.title("TAALES 2.2 · Input and results")
    width, height = min(980, root.winfo_screenwidth() - 80), min(480, root.winfo_screenheight() - 110)
    root.geometry(f"{max(400, width)}x{max(300, height)}+24+32")
    footer = ttk.Frame(root, padding=12)
    footer.pack(side="bottom", fill="x")
    middle = ttk.Frame(root)
    middle.pack(fill="both", expand=True)
    canvas = tk.Canvas(middle, highlightthickness=0)
    scroll = ttk.Scrollbar(middle, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    box = ttk.Frame(canvas, padding=16)
    body = canvas.create_window((0, 0), window=box, anchor="nw")
    box.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(body, width=e.width))
    root.bind("<Button-4>", lambda e: canvas.yview_scroll(-3, "units"))
    root.bind("<Button-5>", lambda e: canvas.yview_scroll(3, "units"))
    destination = paths.output / "taales" / new_run_id()
    child = None
    input_path = tk.StringVar(value=str(paths.browse_root))
    output_path = tk.StringVar(value=str(destination / "taales-"))
    status = tk.StringVar(value="The binary's input and output pickers must be set manually.")

    def copy(value):
        root.clipboard_clear()
        root.clipboard_append(value.get())
        root.update_idletasks()

    def field(label, value):
        frame = ttk.LabelFrame(box, text=label, padding=8)
        frame.pack(fill="x", pady=6)
        ttk.Entry(frame, textvariable=value, state="readonly").pack(fill="x")
        ttk.Button(frame, text="Copy path", command=lambda: copy(value)).pack(anchor="w", pady=(6, 0))

    field("1. Input folder — select inside TAALES", input_path)
    presets = ttk.Frame(box)
    presets.pack(fill="x")
    for label, path in (("ELLIPSE train", paths.ellipse_train), ("ELLIPSE test", paths.ellipse_test),
                        ("Private cohort", paths.private_cohort), ("Workshop texts", paths.input),
                        ("Smoke input", paths.workspace / "smoke-input")):
        ttk.Button(presets, text=label, command=lambda value=path: input_path.set(str(value))).pack(side="left", padx=(0, 6))
    field("2. Results filename — select inside TAALES", output_path)

    def launch():
        nonlocal child
        if child is not None:
            return
        try:
            if not binary.is_file() or not os.access(binary, os.X_OK):
                raise OSError("The local TAALES executable is absent or not executable")
            if not Path(input_path.get()).is_dir():
                raise OSError("The selected input folder is absent")
            destination.mkdir(parents=True, exist_ok=False)
            (destination / "RUN-NOTES.txt").write_text(
                "TAALES launch folder, NOT a completion receipt.\n"
                "Select the input folder and the taales- output prefix manually in TAALES.\n"
                "TAALES appends output names such as results.\n"
                "Use a new filename for any additional analysis.\n"
                "After TAALES reports completion, verify CSV header, expected file identities, "
                "row count and requested diagnostic output.\n", encoding="utf-8")
            with (destination / "launcher.log").open("x", encoding="utf-8") as log:
                child = subprocess.Popen([str(window_launcher), str(binary)], cwd=binary.parent,
                                         stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                         start_new_session=True)
            launch_button.state(["disabled"])
            status.set("TAALES launched. Copy these paths into its pickers. Keep this card open for copying.")
        except OSError as exc:
            messagebox.showerror("TAALES could not launch", str(exc), parent=root)

    launch_button = ttk.Button(footer, text="Launch TAALES", command=launch)
    launch_button.pack(anchor="w", pady=8)
    label = ttk.Label(footer, textvariable=status, wraplength=750)
    label.pack(fill="x")
    footer.bind("<Configure>", lambda e: label.configure(wraplength=max(250, e.width - 40)))
    ttk.Label(footer, text="Closing this card does not close TAALES. No completion or restart guarantee is inferred from the opaque binary.",
              wraplength=750).pack(fill="x", pady=8)
    root.mainloop()


if __name__ == "__main__":
    main()
