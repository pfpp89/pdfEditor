#!/usr/bin/env bash
# Starts the PDF editor on Linux.
# On first run it creates the .venv and installs the dependencies.

set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

# When double-clicked from a file manager there is no terminal, so the editor
# could not be stopped and errors would be invisible. Reopen inside a terminal.
if [ ! -t 1 ] && [ -z "${PDF_EDITOR_IN_TERMINAL:-}" ]; then
    export PDF_EDITOR_IN_TERMINAL=1
    script="$(pwd)/startPdfEditor.sh"
    for term in x-terminal-emulator gnome-terminal konsole xfce4-terminal mate-terminal tilix xterm; do
        if command -v "$term" >/dev/null 2>&1; then
            case "$term" in
                gnome-terminal) exec gnome-terminal --title="PDF Editor" -- "$script" "$@" ;;
                *) exec "$term" -e "$script" "$@" ;;
            esac
        fi
    done
    # No terminal emulator found: carry on without one.
fi

fail() {
    echo
    echo "ERROR: $1"
    read -r -p "Press Enter to close" _ || true
    exit 1
}

venv_python=".venv/bin/python"
marker=".venv/.requirements-installed"

if [ ! -x "$venv_python" ]; then
    command -v python3 >/dev/null 2>&1 || fail "python3 was not found. Install it with your package manager."
    echo "Creating virtual environment (first run only)..."
    python3 -m venv .venv || fail "Could not create the virtual environment. On Debian/Ubuntu: sudo apt install python3-venv"
fi

if [ ! -f "$marker" ] || [ requirements.txt -nt "$marker" ]; then
    echo "Installing dependencies..."
    "$venv_python" -m pip install --disable-pip-version-check -q -r requirements.txt \
        || fail "Could not install the dependencies."
    touch "$marker"
fi

"$venv_python" -c "import tkinter" 2>/dev/null \
    || echo "Note: tkinter is missing, so the browser's file picker is used instead of native dialogs (sudo apt install python3-tk)."

echo "Starting PDF editor. Close this window or press Ctrl+C to stop it."
"$venv_python" app.py "$@" || fail "The editor stopped with an error."
