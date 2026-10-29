# PDF Editor

A small local PDF page editor. Open a PDF, append more PDFs, then reorder or delete
pages (multi-select supported) and save the result as a new file.

Everything runs on your machine: a Python server bound to `127.0.0.1` serves the
UI to your browser. No file content is ever sent anywhere else, and the UI loads
no external scripts, fonts or images.

## Quick start

Requires Python 3.10+. The launchers create `.venv` and install the dependencies
on the first run.

- **Windows:** double-click `startPdfEditor.cmd`. It runs `startPdfEditor.ps1`, because
  Windows opens `.ps1` files in Notepad when you double-click them.
- **Linux:** run `chmod +x startPdfEditor.sh` once, then double-click it or run
  `./startPdfEditor.sh`. If your file manager asks, choose "Run". The script reopens
  itself in a terminal window so you can see its output and stop it.

Closing the terminal window stops the editor.

## Manual setup

**Windows** (PowerShell):

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

**Linux**:

```bash
sudo apt install python3-tk      # for the native Open/Save dialogs (Fedora: python3-tkinter)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

Your default browser opens automatically. Stop the editor with `Ctrl+C` in the terminal.

Options: `--port 8000` to use a fixed port, `--no-browser` to not open a browser.

## Usage

| Action | How |
|---|---|
| Open a PDF | **Open** (Ctrl+O) |
| Add PDFs to the end | **Append PDFs**. You can select several files. |
| Select pages | Click a page. Ctrl+click toggles one page, Shift+click selects a range, Ctrl+A selects all, Esc clears. |
| Reorder | Drag the selected pages, or use **Move to start** / **Move to end** |
| Delete | **Delete** button, the Del key, or right-click a page and choose Delete |
| Undo / redo | Ctrl+Z / Ctrl+Y |
| Preview a page | Double-click it (← → to step, Esc to close) |
| Save | **Save As…** (Ctrl+S). Your original files are never modified unless you choose to overwrite them. Afterwards you can open the new file in your default PDF viewer. |

Each page shows a colored bar and a label with the file and page it came from.
Password-protected PDFs ask for their password when you open them.

If tkinter is not available, the editor falls back to the browser's own file
picker and download. Files still only go to the local server.

## Privacy and security

- The server listens on `127.0.0.1` only, so other computers can't reach it.
- Every API call needs a random token created at startup. This stops other websites
  or local programs from using the editor's API. Requests with a foreign `Host`
  header are refused, which guards against DNS rebinding.
- A strict Content-Security-Policy stops the page from loading or sending anything
  to other origins.

## Tests

```bash
python -m pytest
```

## License note

PyMuPDF is licensed under AGPL-3.0 (commercial licenses are also available).
That is fine for personal or internal use. Check its terms before you distribute
this app.
