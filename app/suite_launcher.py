"""Peer-tool entry surface, started by LXQt after its window manager."""
from pathlib import Path
import os
import tempfile
import subprocess
import tkinter as tk
from tkinter import font, messagebox, ttk

SUPPORT = Path(__file__).resolve().parents[1]
LAUNCH = SUPPORT / "bin/workshop-launch"


def main():
    root = tk.Tk()
    root.title("Hemma Research Workstation")
    width = min(700, max(620, root.winfo_screenwidth() - 64))
    height = min(680, max(600, root.winfo_screenheight() - 110))
    root.geometry(f"{width}x{height}+32+42")
    root.minsize(620, 600)
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        font.nametofont(name, root=root).configure(size=12)
    ttk.Style(root).configure("TButton", padding=(12, 7))
    frame = ttk.Frame(root, padding=24)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="Hemma Research Workstation",
              font=("TkDefaultFont", 19, "bold")).pack(anchor="w")
    ttk.Label(frame, text="Research workstation on Hemma", font=("TkDefaultFont", 12)).pack(anchor="w", pady=(2, 22))

    status = tk.StringVar(value="Choose an analysis tool or browse Hemma Home.")
    children = []

    def collect(child, log, action):
        # UI bookkeeping only: no relaunch, recovery policy or synchronous wait.
        code = child.poll()
        if code is None:
            root.after(150, collect, child, log, action)
            return
        log.seek(0, 2)
        size = log.tell()
        log.seek(max(0, size - 4096))
        message = log.read().decode("utf-8", errors="replace").strip()
        log.close()
        children.remove((child, log))
        if code:
            messagebox.showerror("Launcher status — " + action.upper(),
                                 message or f"The launcher exited with status {code}.", parent=root)
        elif action == "jasp":
            status.set(message or "JASP launch requested; verify its desktop window.")

    def launch(action):
        log = tempfile.TemporaryFile()
        try:
            child = subprocess.Popen([str(LAUNCH), action], stdin=subprocess.DEVNULL,
                                     stdout=log, stderr=log, start_new_session=True)
        except OSError as exc:
            log.close()
            messagebox.showerror("Could not launch", str(exc), parent=root)
            return
        children.append((child, log))
        root.after(0, collect, child, log, action)

    tools = ttk.LabelFrame(frame, text="Analysis tools", padding=12)
    tools.pack(fill="x")
    for text, action in (("TAALED · lexical diversity", "taaled"),
                         ("TAALES · lexical sophistication", "taales"),
                         ("JASP · statistics", "jasp")):
        ttk.Button(tools, text=text, command=lambda value=action: launch(value)).pack(fill="x", pady=4)
    files = ttk.LabelFrame(frame, text="Files", padding=12)
    files.pack(fill="x", pady=14)
    for text, action in (("Hemma Home", "files"), ("Dataset shortcuts and service output", "data"),
                         ("Terminal", "terminal")):
        ttk.Button(files, text=text, command=lambda value=action: launch(value)).pack(fill="x", pady=4)
    browse_root = os.environ.get("FEATURE_BROWSE_ROOT", "/hemma-home")
    ttk.Label(frame, text=f"Hemma Home: {browse_root}. Dataset shortcuts are optional.",
              wraplength=540, justify="left").pack(anchor="w")
    ttk.Label(frame, textvariable=status, wraplength=540, justify="left").pack(anchor="w", pady=(6, 0))
    root.mainloop()


if __name__ == "__main__":
    main()
