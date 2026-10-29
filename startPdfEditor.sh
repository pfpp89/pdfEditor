#!/usr/bin/env bash
# Starts the PDF editor on Linux.
# On first run it creates the .venv and installs the dependencies.
#   --setup-only   only prepare the .venv (used by install.sh)
# Other arguments are passed to app.py (e.g. --browser-tab).

set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

venv_python=".venv/bin/python"
marker=".venv/.requirements-installed"

needs_setup() {
    [ ! -x "$venv_python" ] || [ ! -f "$marker" ] || [ requirements.txt -nt "$marker" ]
}

fail() {
    echo
    echo "ERROR: $1"
    if [ -t 0 ]; then read -r -p "Press Enter to close" _ || true; fi
    exit 1
}

setup() {
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
}

if [ "${1:-}" = "--setup-only" ]; then
    setup
    exit 0
fi

# Setup prints progress and may fail: when double-clicked (no terminal),
# reopen in a terminal window so the user can see it.
if needs_setup && [ ! -t 1 ] && [ -z "${PDF_EDITOR_IN_TERMINAL:-}" ]; then
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
fi

setup
# The editor opens its own window and stops when that window is closed.
exec "$venv_python" app.py "$@"
