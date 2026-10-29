# TODO

## Planned

- [x] **Multi-language support (i18n)**: translate the UI (toolbar, status bar,
      dialogs, error messages) and pick the language from the browser/OS locale,
      with a manual override. Server error messages in `pdf_editor/` need
      translating too.
- [x] **Offer to open the saved file**: right after a successful Save As, ask the
      user whether to open the new PDF in the system's default PDF application.
      The server would launch it (`os.startfile` on Windows, `xdg-open` on Linux)
      through a new API endpoint that only accepts the path just saved.
- [x] **Right-click context menu**: right-clicking a page shows a custom context
      menu with **Delete** for the current selection. Right-clicking a page that
      isn't selected first selects only that page. Other actions (Move to
      start/end, Preview) could be added to the same menu later.
- [x] **Undo/Redo icons**: add the classic curved-arrow icons (↶ undo, ↷ redo) to
      the Undo and Redo buttons. Use inline SVG so nothing is loaded from outside
      and the icons follow the light/dark theme.
- [x] **Open button icon**: add a small gray folder icon to the left of the "Open"
      text. Use inline SVG, like the Undo/Redo icons.
- [x] **Delete button style**: make the Delete button red (it stays faded while
      disabled, i.e. when nothing is selected) and add a small icon of a page with
      an "x" to the left of the text. Use inline SVG.
- [x] **Single .exe (optional)**: bundle Python and the dependencies with PyInstaller
      so the editor runs on a PC without Python installed. Done: `build_exe.cmd` builds
      `dist\PdfEditor.exe` (~33 MB). Antivirus software may still flag it, since it's unsigned.
- [x] **Entry in Windows "Installed apps" for `PdfEditor.exe`**: done in
      `pdf_editor/winsetup.py`. It's offered on first launch, and Uninstall removes
      everything, including the .exe itself.
- [ ] **Entry in Windows "Installed apps" for the Python version** (optional): have `install.ps1` register PDF Editor under
      `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\PdfEditor` (no admin
      rights needed), with DisplayName, DisplayIcon (`static\icon.ico`), Publisher and an
      UninstallString that runs `uninstall.cmd`. Uninstalling from Settings > Apps should
      then also delete the program folder once the editor has closed, which
      `uninstall.cmd` can't do for its own folder. `-Uninstall` must remove the
      registry entry.
- [ ] **Test `PdfEditor.exe` on another PC** (ideally the parent's, or a clean Windows
      user account): SmartScreen "Windows protected your PC" → Run anyway; antivirus
      reaction; first-launch offer → Yes (icons named in the chosen language, entry in
      Settings > Apps); open/append/reorder/delete/save; close the window → the process
      ends; double-click twice → one editor; uninstall **from the Settings app** →
      icons, entry, data folder and the .exe all removed; opening the .exe straight
      from an e-mail/download → "Save PDF Editor first".
