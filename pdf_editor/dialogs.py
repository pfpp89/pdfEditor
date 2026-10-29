"""Native file dialogs (tkinter).

Tk must only be used from the thread that created it, so every dialog runs on
one dedicated thread that owns a hidden Tk root; Flask's worker threads hand
it requests and wait for the answer. (An earlier version started a child
Python process per dialog, which in the single-file .exe would unpack the
whole bundle again each time.)
"""

import queue
import threading
from concurrent.futures import Future


class DialogUnavailable(Exception):
    """tkinter is missing (e.g. python3-tk not installed on Linux)."""


_requests = queue.Queue()
_start_lock = threading.Lock()
_ready = None  # Future: set once the Tk thread is up (or failed to start)


def _worker(ready):
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
    except Exception as e:  # ImportError, or TclError without a display
        ready.set_exception(DialogUnavailable(str(e)))
        return
    ready.set_result(True)
    while True:
        future, show = _requests.get()
        try:
            root.attributes("-topmost", True)  # appear above the editor window
            future.set_result(show(root, filedialog))
        except Exception as e:
            future.set_exception(e)
        finally:
            root.update()  # let Tk finish closing the dialog


def _call(show):
    global _ready
    with _start_lock:
        if _ready is None:
            _ready = Future()
            threading.Thread(target=_worker, args=(_ready,), name="tk-dialogs", daemon=True).start()
    _ready.result()  # raises DialogUnavailable if Tk could not start
    future = Future()
    _requests.put((future, show))
    return future.result()


def _types(pdf_label, all_label):
    return [(pdf_label, "*.pdf"), (all_label, "*.*")]


def ask_open_files(multiple=True, title="Open PDF", pdf_label="PDF files", all_label="All files"):
    """Return a list of selected paths (empty if cancelled)."""
    def show(root, filedialog):
        types = _types(pdf_label, all_label)
        if multiple:
            return list(filedialog.askopenfilenames(parent=root, title=title, filetypes=types))
        path = filedialog.askopenfilename(parent=root, title=title, filetypes=types)
        return [path] if path else []
    return _call(show)


def ask_save_file(initial_name="edited.pdf", title="Save PDF as", pdf_label="PDF files",
                  all_label="All files"):
    """Return the chosen path, or None if cancelled."""
    def show(root, filedialog):
        return filedialog.asksaveasfilename(
            parent=root, title=title, filetypes=_types(pdf_label, all_label),
            defaultextension=".pdf", initialfile=initial_name, confirmoverwrite=True) or None
    return _call(show)
