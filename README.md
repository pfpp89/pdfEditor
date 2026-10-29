# PDF Editor

A small local PDF page editor. Open a PDF, append more PDFs, then reorder or delete
pages (multi-select supported) and save the result as a new file.

Everything runs on your machine: a Python server bound to `127.0.0.1` serves the
UI to a browser window. No file content is ever sent anywhere else, and the UI loads
no external scripts, fonts or images.

Contents: [Using the editor](#using-the-editor) ·
[Installing on a computer](#installing-on-a-computer) ·
[Updating](#updating-to-a-new-version) · [Uninstalling](#uninstalling) ·
[Troubleshooting](#troubleshooting) · [How it works](#how-it-works) ·
[Development](#development) · [Privacy and security](#privacy-and-security)

## Using the editor

1. **Double-click the PDF Editor icon** on the Desktop or in the Start menu. The
   editor opens in its own window (Microsoft Edge or Chrome in "app mode": no
   tabs, no address bar). On a cold start it takes a few seconds to appear in
   that window.
2. **Work on the pages** (see below), then **Save As…**.
3. **Close the window.** The editor stops by itself a few seconds later. If there
   are unsaved changes, you're asked first.

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
| Change language | Language button at the right of the toolbar: English, Français, Português |

Each page shows a colored bar and a label with the file and page it came from.
Password-protected PDFs ask for their password when you open them. Double-clicking
the icon while the editor is already open just opens another window.

## Installing on a computer

### Windows

1. **Install Python 3.10 or newer** from [python.org](https://www.python.org/downloads/)
   (the default installer options are fine). This only has to be done once per computer.
2. **Copy this project folder somewhere permanent**, for example
   `C:\Users\<name>\Documents\PdfEditor`. The shortcuts point into this folder, so
   don't move or rename it after installing. If you do, run the installer again.
3. **Double-click `install.cmd`.** A console window shows the progress. The first
   time it creates `.venv` and downloads the dependencies, which takes about a minute
   and needs internet access once. It then creates a **PDF Editor** icon on the
   Desktop and in the Start menu. Press Enter to close the window.

To use another name for the icon (e.g. in Portuguese), run this in a command prompt
in the folder: `install.cmd -Name "Editor de PDF"`.

Running `install.cmd` again is always safe: it just repairs or updates the setup
and recreates the shortcuts.

### Linux

```bash
sudo apt install python3-venv python3-tk   # Fedora: python3-tkinter
./install.sh                               # or: ./install.sh --name "Editor de PDF"
```

This adds PDF Editor to the application menu and puts an icon on the Desktop.
On GNOME, if the Desktop icon doesn't start, right-click it and choose
*Allow Launching*.

## Updating to a new version

1. Close the editor.
2. Replace the files in the project folder with the new version (or `git pull`).
   Keep the `.venv` folder.
3. Run `install.cmd` (Linux: `./install.sh`) again. This installs any new
   dependencies. The desktop shortcut starts the editor directly and does **not**
   check for them.

## Uninstalling

### Windows

1. **Close the editor** if it is open (wait a few seconds after closing its window).
2. **Double-click `uninstall.cmd`** in the project folder. It removes:
   - the Desktop and Start menu shortcuts, including ones created with `-Name`;
   - the editor's data folder `%LOCALAPPDATA%\PdfEditor` (log, lock, settings and state files).

   If the editor is still open, it says so and changes nothing. Close the window
   and run it again.
3. **Delete the project folder.** The uninstaller can't delete the folder it runs
   from, so this step is manual.
4. *(Optional)* Uninstall Python from **Settings > Apps** if nothing else needs it.

Just deleting the Desktop icon is **not** an uninstall: the Start menu shortcut,
the program folder and the data folder would all stay behind.

`uninstall.cmd` is the same as `install.cmd -Uninstall`.

### Linux

```bash
./uninstall.sh      # same as ./install.sh --uninstall
```

Then delete the project folder. This removes the menu entry, the Desktop icon and
`~/.local/state/pdf-editor`.

## Troubleshooting

| Problem | What to do |
|---|---|
| Double-clicking the icon shows an error box | It explains why the editor couldn't start. Details are in the log: `%LOCALAPPDATA%\PdfEditor\pdf-editor.log` (Linux: `~/.local/state/pdf-editor/pdf-editor.log`). |
| "Python 3 was not found" when installing | Install Python from python.org, then run `install.cmd` again. |
| The icon does nothing after the folder was moved | Run `install.cmd` again from the new location. |
| The window says "PDF Editor has stopped" | The editor was closed, e.g. by the computer shutting down. Close the window and start it again from the icon. |
| The editor opens in a normal browser tab | Neither Edge nor Chrome/Chromium was found, so the default browser is used. Everything still works, and closing the tab stops the editor. |
| Open/Save use the browser's file picker instead of the system dialogs | tkinter is missing (Linux: `sudo apt install python3-tk`). |
| `uninstall.cmd` says the editor is still open | Close all PDF Editor windows, wait a few seconds and try again. If it persists, end `pythonw.exe` in Task Manager. |
| Need to see what the server is doing | Run `.venv\Scripts\python.exe app.py` in a console: it prints every request. |

## How it works

**Starting.** The shortcut runs `.venv\Scripts\pythonw.exe app.py`. `pythonw` has
no console window. `app.py` then:
1. takes an OS file lock (`instance.lock`). If another editor already holds it,
   even one still starting, it waits for that editor and opens a window on it
   instead of starting a second copy;
2. opens a listening socket on `127.0.0.1` on a free port and **immediately**
   opens the window, so the user sees something at once. The browser waits on the
   socket while Flask and PyMuPDF load;
3. writes `instance.json` (port, access token, process id) and starts serving.

**Stopping.** Each editor window sends a heartbeat every 5 seconds and a goodbye
(`navigator.sendBeacon`) when it is closed. The server stops when no window is
left:
- 8 seconds after the last goodbye (a page reload reconnects within that time);
- 3 minutes after the last heartbeat if a window vanished without a goodbye
  (generous because browsers slow timers down in minimized windows);
- 2 minutes after starting if no window ever connected.

Sleep and hibernation are detected and don't count as missing heartbeats.
`--keep-running` and `--no-browser` disable the automatic stop.

**Files on the computer**

| What | Windows | Linux |
|---|---|---|
| Program and its Python environment | the project folder (`.venv` inside) | the project folder |
| Shortcuts | Desktop and Start menu `PDF Editor.lnk`, recorded in `.installed-shortcuts.txt` | `~/.local/share/applications/pdf-editor.desktop` and on the Desktop |
| Log (rewritten at each start) | `%LOCALAPPDATA%\PdfEditor\pdf-editor.log` | `~/.local/state/pdf-editor/pdf-editor.log` |
| Running instance (port, token, pid) | `%LOCALAPPDATA%\PdfEditor\instance.json` | `~/.local/state/pdf-editor/instance.json` |
| Single-instance lock | `%LOCALAPPDATA%\PdfEditor\instance.lock` | `~/.local/state/pdf-editor/instance.lock` |
| Settings (chosen language) | `%LOCALAPPDATA%\PdfEditor\settings.json` | `~/.local/state/pdf-editor/settings.json` |

The settings are stored on disk and not in the browser, because the editor's address
(its port) changes at every start, and browser storage is tied to the address.

**Launcher scripts**

| Script | Purpose |
|---|---|
| `install.cmd` → `install.ps1` | set up `.venv` and create shortcuts (`-Name`, `-Uninstall`) |
| `uninstall.cmd` | `install.ps1 -Uninstall` |
| `startPdfEditor.cmd` → `startPdfEditor.ps1` | start without installing; sets up `.venv` on first run (`-SetupOnly` is used by the installer) |
| `install.sh`, `uninstall.sh`, `startPdfEditor.sh` | the Linux equivalents |

The `.cmd` files exist because Windows opens `.ps1` files in Notepad when they're
double-clicked, and often blocks running them.

## Development

**Setup:**

```powershell
py -3 -m venv .venv                                   # Linux: python3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py                     # console with request logs
```

**`app.py` options:**

| Option | Effect |
|---|---|
| `--browser-tab` | open in a normal tab of the default browser instead of an app window |
| `--keep-running` | don't stop when the last window closes (stop with Ctrl+C) |
| `--no-browser` | don't open any window; implies `--keep-running` |
| `--port 8000` | use a fixed port |

**Tests:** `.\.venv\Scripts\python.exe -m pytest`

**Project layout:**

| Path | Contents |
|---|---|
| `app.py` | entry point: single instance, window, server, automatic stop |
| `pdf_editor/server.py` | Flask app and JSON API (token and Host checks) |
| `pdf_editor/documents.py` | PDF handling with PyMuPDF; error codes |
| `pdf_editor/dialogs.py` | native Open/Save dialogs (tkinter in a child process) |
| `pdf_editor/lifecycle.py` | heartbeat tracking, app window, instance lock, error box |
| `static/` | UI: `index.html`, `app.js`, `i18n.js`, `style.css`, `locales/`, icons |
| `tools/make_icon.py` | regenerates `static/icon.svg`, `icon.png` and `icon.ico` from one SVG |
| `tests/` | pytest suite |

**Adding a language:** copy `static/locales/en.json` to `static/locales/<code>.json`,
translate the values (keep the `{placeholders}`; `one`/`other` are plural forms),
then add the code and an SVG flag to `LANGUAGES` and `FLAGS` in `static/i18n.js`.
`tests/test_locales.py` checks that every language has the same keys and
placeholders. Server errors are sent as codes (`ERROR_MESSAGES` in
`pdf_editor/documents.py`) and translated in the UI under `error.<code>`.

**Changing the icon:** edit the SVG in `tools/make_icon.py`, run
`.\.venv\Scripts\python.exe tools\make_icon.py`, then run `install.cmd` again to
refresh the shortcuts.

## Privacy and security

- The server listens on `127.0.0.1` only, so other computers can't reach it.
- Every API call needs a random token created at startup. This stops other websites
  or local programs from using the editor's API. Requests with a foreign `Host`
  header are refused, which guards against DNS rebinding.
- A strict Content-Security-Policy stops the page from loading or sending anything
  to other origins.
- While it runs, the editor stores its port and access token in `instance.json`,
  readable only by your user account, so a second launch can open a window on it.
- `/api/open-saved` only opens the file written by the last Save As, never a path
  sent by the page.

## License note

PyMuPDF is licensed under AGPL-3.0 (commercial licenses are also available).
That is fine for personal or internal use. Check its terms before you distribute
this app.
