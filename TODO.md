# TODO

## Planned

- [ ] **Multi-language support (i18n)**: translate the UI (toolbar, status bar,
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
