"""Native file dialogs.

tkinter must own the main thread of its process, which Flask's worker threads
cannot provide, so each dialog runs in a short-lived child Python process that
prints the result as JSON.
"""

import json
import subprocess
import sys

_SCRIPT = r"""
import json, sys
import tkinter as tk
from tkinter import filedialog

mode, title, initial, pdf_label, all_label = sys.argv[1:6]
root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)
types = [(pdf_label, "*.pdf"), (all_label, "*.*")]
if mode == "open":
    result = list(filedialog.askopenfilenames(parent=root, title=title, filetypes=types))
elif mode == "open1":
    path = filedialog.askopenfilename(parent=root, title=title, filetypes=types)
    result = [path] if path else []
else:
    result = filedialog.asksaveasfilename(
        parent=root, title=title, filetypes=types, defaultextension=".pdf",
        initialfile=initial, confirmoverwrite=True) or None
root.destroy()
print(json.dumps(result))
"""


class DialogUnavailable(Exception):
    """tkinter is missing (e.g. python3-tk not installed on Linux)."""


def _run(mode, title, initial="", pdf_label="PDF files", all_label="All files"):
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _SCRIPT, mode, title, initial, pdf_label, all_label],
            capture_output=True, text=True, encoding="utf-8",
        )
    except OSError as e:
        raise DialogUnavailable(str(e)) from e
    if proc.returncode != 0:
        raise DialogUnavailable(proc.stderr.strip().splitlines()[-1:] or "dialog failed")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def ask_open_files(multiple=True, title="Open PDF", pdf_label="PDF files", all_label="All files"):
    """Return a list of selected paths (empty if cancelled)."""
    return _run("open" if multiple else "open1", title, "", pdf_label, all_label)


def ask_save_file(initial_name="edited.pdf", title="Save PDF as", pdf_label="PDF files",
                  all_label="All files"):
    """Return the chosen path, or None if cancelled."""
    return _run("save", title, initial_name, pdf_label, all_label)
