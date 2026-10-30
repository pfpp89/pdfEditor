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

There are two ways to install the editor:

| | **`PdfEditor.exe`** (recommended for other people's PCs) | **Python version** |
|---|---|---|
| Needs Python on the PC | no | yes |
| Needs internet when installing | no | once |
| What you copy | one file (~33 MB) | the project folder |
| Updating | send a new `PdfEditor.exe` | copy the files, run `install.cmd` |
| Uninstalling | Settings > Apps, like any program | `uninstall.cmd`, then delete the folder |
| Systems | Windows | Windows and Linux |

### Option A: `PdfEditor.exe` (Windows)

**On your PC:** build it by double-clicking `build_exe.cmd` (see
[Building PdfEditor.exe](#building-pdfeditorexe)). The result is `dist\PdfEditor.exe`.

**Sending it:** most e-mail services (Gmail, Outlook.com…) refuse `.exe` files, even
inside a `.zip`. Share a **OneDrive / Google Drive / Dropbox link** instead, or use a
USB stick.

**On the other PC:**

1. **Save `PdfEditor.exe` in a permanent folder**, e.g. *Documents*. Don't run it
   straight from the e-mail or the browser's download bar. If it's opened from a
   temporary folder, the editor asks to save it first and installs nothing.
2. **Double-click it.** The first time, Windows may show a blue box, *"Windows
   protected your PC"*. Click **More info → Run anyway**. This happens because the
   file isn't signed with a paid certificate, and again for each new version.
3. **The editor opens and asks "Add PDF Editor to this computer?"**
   - **Yes, create the icons:** creates **PDF Editor** icons on the Desktop and in the
     Start menu, named in the editor's language, e.g. *Editor de PDF* in Portuguese.
     It also adds PDF Editor to **Settings > Apps** so it can be uninstalled like
     any other program. No administrator rights are needed.
   - **No, thanks:** nothing is installed, and the question isn't asked again for
     this file. The `.exe` still works when double-clicked.
   - **Esc / closing the box:** "not now". The question comes back at the next start.

The editor's language follows Windows' language the first time. If it should be
another one, change it with the language button. The icons keep the name they were
created with.

### Option B: Python version (Windows)

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
and recreates the shortcuts. This version doesn't add an entry to Settings > Apps.

### Linux

```bash
sudo apt install python3-venv python3-tk   # Fedora: python3-tkinter
./install.sh                               # or: ./install.sh --name "Editor de PDF"
```

This adds PDF Editor to the application menu and puts an icon on the Desktop.
On GNOME, if the Desktop icon doesn't start, right-click it and choose
*Allow Launching*.

## Updating to a new version

### `PdfEditor.exe`

1. Raise the version in `pdf_editor/__init__.py` and build a new `PdfEditor.exe`.
2. On the other PC: close the editor and **replace the old file with the new one, in
   the same folder and with the same name**. The icons keep working, and nothing
   else is needed.

If the new file is saved somewhere else instead, the editor offers to add itself
again when it starts. Answering Yes moves the icons and the Settings > Apps entry
to the new file. Delete the old file afterwards.

### Python version

1. Close the editor.
2. Replace the files in the project folder with the new version (or `git pull`).
   Keep the `.venv` folder.
3. Run `install.cmd` (Linux: `./install.sh`) again. This installs any new
   dependencies. The desktop shortcut starts the editor directly and does **not**
   check for them.

## Uninstalling

### `PdfEditor.exe`

1. **Close the editor** if it is open (wait a few seconds after closing its window).
2. Open **Settings > Apps > Installed apps**, find **PDF Editor** (or the name it was
   installed with), click **⋯ > Uninstall** and confirm. On Windows 10 the path is
   **Settings > Apps > Apps & features**.
3. A message confirms that PDF Editor has been removed. It has removed:
   - the Desktop and Start menu icons;
   - the Settings > Apps entry;
   - the data folder `%LOCALAPPDATA%\PdfEditor` (settings and log);
   - **`PdfEditor.exe` itself**, a few seconds after the message is closed.

If the editor is still open, a message says so and nothing is removed.

The same can be done from a command prompt: `PdfEditor.exe --uninstall`.

If the icons were never created (you answered *No*), there's nothing in Settings >
Apps: just delete `PdfEditor.exe` and, optionally, `%LOCALAPPDATA%\PdfEditor`.

### Python version (Windows)

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
| *"Windows protected your PC"* when starting `PdfEditor.exe` | Click **More info → Run anyway**. Expected for an unsigned program, once per new version. |
| The antivirus quarantines or deletes `PdfEditor.exe` | A false alarm that is common for unsigned programs built with PyInstaller. Restore the file from the antivirus' quarantine and mark it as allowed. |
| The e-mail with `PdfEditor.exe` can't be sent or arrives without it | E-mail services block `.exe` files. Share a cloud-storage link or use a USB stick. |
| `PdfEditor.exe` says "Save PDF Editor first" | It was opened from a temporary folder (e-mail, download bar). Save it in *Documents* and open it from there. |
| The uninstall says PDF Editor is still open | Close all PDF Editor windows, wait a few seconds and try again. If it persists, end `PdfEditor.exe` (or `pythonw.exe` for the Python version) in Task Manager. |
| Need to see what the server is doing | Run `.venv\Scripts\python.exe app.py` in a console: it prints every request. |

## How it works

**Starting.** The shortcut runs `PdfEditor.exe` or, for the Python version,
`.venv\Scripts\pythonw.exe app.py`. Neither shows a console window. `app.py` then:
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

**The single `.exe`.** `PdfEditor.exe` is built by PyInstaller in "one file" mode. It
contains Python, Flask, PyMuPDF, tkinter, our code and `static/`. At each start it
unpacks itself into a hidden temporary folder (`%TEMP%\_MEI…`), runs `app.py` from
there, and deletes that folder when it exits. Nothing that must survive is
stored there: settings and logs are in `%LOCALAPPDATA%\PdfEditor`, as for the Python
version. `pdf_editor/winsetup.py` handles self-installation:
- **"Add to this computer"** creates the `.lnk` shortcuts with PowerShell's
  `WScript.Shell`. It then writes the "Installed apps" entry under
  `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\PdfEditor`
  (per user, no admin rights): `DisplayName`, `DisplayIcon`, `DisplayVersion`,
  `UninstallString` = `"…\PdfEditor.exe" --uninstall`, plus our own `ExePath` and
  `Shortcuts` values.
- **The offer** is shown when the running `.exe` isn't the registered one, isn't
  in a temporary folder, and wasn't declined for that path (`install_declined` in
  `settings.json`).
- **`--uninstall`** refuses while the editor runs, because it can't take the
  instance lock. Otherwise it removes the shortcuts listed in the registry, the
  registry key and the data folder, shows a message, then starts a hidden
  `cmd.exe` that deletes the `.exe` a few seconds later. A running `.exe` can't
  delete itself.

Message boxes (start-up error, uninstall) use the language saved in `settings.json`
(`NATIVE_TEXTS` in `pdf_editor/lifecycle.py`).

**Files on the computer**

| What | Windows | Linux |
|---|---|---|
| Program (`.exe` version) | `PdfEditor.exe` where it was saved; unpacked to `%TEMP%\_MEI…` while running | n/a |
| Program (Python version) | the project folder (`.venv` inside) | the project folder |
| "Installed apps" entry (`.exe` version) | `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\PdfEditor` | n/a |
| Shortcuts | Desktop and Start menu `PDF Editor.lnk`; recorded in the registry entry (`.exe`) or in `.installed-shortcuts.txt` (Python version) | `~/.local/share/applications/pdf-editor.desktop` and on the Desktop |
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
| `build_exe.cmd` → `build_exe.ps1` | run the tests and build `dist\PdfEditor.exe` (`-SkipTests` to skip the tests) |
| `startPdfEditor.cmd` → `startPdfEditor.ps1` | start without installing; sets up `.venv` on first run (`-SetupOnly` is used by the installer) |
| `install.sh`, `uninstall.sh`, `startPdfEditor.sh` | the Linux equivalents |

The `.cmd` files exist because Windows opens `.ps1` files in Notepad when they're
double-clicked, and often blocks running them.

## Development

**Setup:**

```powershell
py -3 -m venv .venv                                   # Linux: python3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt  # + pytest, PyInstaller
.\.venv\Scripts\python.exe app.py                     # console with request logs
```

**`app.py` options:**

| Option | Effect |
|---|---|
| `--browser-tab` | open in a normal tab of the default browser instead of an app window |
| `--keep-running` | don't stop when the last window closes (stop with Ctrl+C) |
| `--no-browser` | don't open any window; implies `--keep-running` |
| `--port 8000` | use a fixed port |
| `--uninstall` | `PdfEditor.exe` only: uninstall (what Settings > Apps runs) |

**Tests:** `.\.venv\Scripts\python.exe -m pytest`

`requirements.txt` lists what the editor needs to run, and is what `install.cmd`
installs. `requirements-dev.txt` adds the test and build tools.

### Building PdfEditor.exe

Double-click `build_exe.cmd`, or run `build_exe.cmd -SkipTests`. It:
1. sets up `.venv` and installs `requirements-dev.txt`;
2. runs the tests and stops if any fail;
3. writes the version resource from `pdf_editor/__init__.py` (`__version__`), shown
   in the file's *Properties > Details*;
4. runs PyInstaller: one file, no console, our icon, `static/` bundled. Output goes
   to `dist\PdfEditor.exe` and intermediate files to `build\`, both ignored by git.

It must be built on Windows, and it runs on 64-bit Windows 10 and 11.

PyMuPDF 2 depends on AI add-ons (`pymupdf_layout` with ONNX models, `pymupdf4llm`,
`onnxruntime`, `numpy`…) that the editor doesn't use. `pdf_editor/documents.py`
blocks them before importing PyMuPDF, and the build excludes them, which keeps the
`.exe` at ~33 MB instead of ~57 MB. Bundling them also broke the `.exe`, because
their model files weren't included.

**Testing a built `.exe`:** copy it to a normal folder (not `%TEMP%`, where it
refuses to install) and run it. Answering *Yes* creates real shortcuts and a real
Settings > Apps entry; uninstall afterwards with `PdfEditor.exe --uninstall`. The
log is in `%LOCALAPPDATA%\PdfEditor\pdf-editor.log`.

**Project layout:**

| Path | Contents |
|---|---|
| `app.py` | entry point: single instance, window, server, automatic stop |
| `pdf_editor/server.py` | Flask app and JSON API (token and Host checks) |
| `pdf_editor/documents.py` | PDF handling with PyMuPDF; error codes |
| `pdf_editor/dialogs.py` | native Open/Save dialogs (tkinter in a child process) |
| `pdf_editor/lifecycle.py` | heartbeat tracking, app window, instance lock, error box |
| `pdf_editor/winsetup.py` | `PdfEditor.exe` self-installation: shortcuts, "Installed apps" entry, uninstall |
| `static/` | UI: `index.html`, `app.js`, `i18n.js`, `style.css`, `locales/`, icons |
| `build_exe.cmd`, `build_exe.ps1`, `tools/write_version_info.py` | build `dist\PdfEditor.exe` |
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

## License

PDF Editor is licensed under the GNU Affero General Public License v3.0
(AGPL-3.0). See [`LICENSE`](LICENSE).

It uses PyMuPDF, which is also licensed under AGPL-3.0 (commercial licenses are
available). Anyone who receives `PdfEditor.exe` can get the source code from this
repository.
