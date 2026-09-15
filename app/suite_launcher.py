"""Small Openbox home surface for the research workstation."""
from pathlib import Path
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk

SUPPORT = Path(__file__).resolve().parents[1]
LAUNCH = SUPPORT / "bin/workshop-launch"


def main():
    root = tk.Tk()
    root.title("Sophistication Feature Processing")
    root.geometry("620x500+32+42")
    root.minsize(520, 420)
    frame = ttk.Frame(root, padding=24)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="Sophistication Feature Processing",
              font=("TkDefaultFont", 19, "bold")).pack(anchor="w")
    ttk.Label(frame, text="Research workstation on Hemma", font=("TkDefaultFont", 12)).pack(anchor="w", pady=(2, 22))

    def launch(action):
        try:
            child = subprocess.Popen([str(LAUNCH), action], stdin=subprocess.DEVNULL,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            if action == "jasp":
                _, error = child.communicate(timeout=5)
                if child.returncode:
                    messagebox.showerror("JASP runtime gap", error.strip(), parent=root)
        except subprocess.TimeoutExpired:
            return
        except OSError as exc:
            messagebox.showerror("Could not launch", str(exc), parent=root)

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
    ttk.Label(frame, text="File pickers start at /hemma-home. Dataset shortcuts are conveniences, not a restricted workflow.",
              wraplength=540, justify="left").pack(anchor="w")
    root.mainloop()


if __name__ == "__main__":
    main()
