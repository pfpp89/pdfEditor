#!/usr/bin/env bash
# Installs PDF Editor for the current Linux user: prepares the .venv and adds
# an application-menu entry and a Desktop icon.
#
#   ./install.sh                       install
#   ./install.sh --name "Editor de PDF"  choose the shortcut name
#   ./install.sh --uninstall           remove the shortcuts and the editor's data
#                                      (same as ./uninstall.sh); then delete the folder

set -euo pipefail
root="$(dirname "$(readlink -f "$0")")"
name="PDF Editor"
uninstall=0

while [ $# -gt 0 ]; do
    case "$1" in
        --name) name="$2"; shift 2 ;;
        --uninstall) uninstall=1; shift ;;
        *) echo "Unknown option: $1"; exit 2 ;;
    esac
done

apps_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
desktop_dir="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
entries=("$apps_dir/pdf-editor.desktop" "$desktop_dir/pdf-editor.desktop")

data_dir="${XDG_STATE_HOME:-$HOME/.local/state}/pdf-editor"

if [ "$uninstall" = 1 ]; then
    if [ -f "$data_dir/instance.json" ]; then
        pid="$(sed -n 's/.*"pid": *\([0-9]*\).*/\1/p' "$data_dir/instance.json")"
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "PDF Editor is still open. Close its window, wait a few seconds, then run the uninstall again."
            exit 1
        fi
    fi
    for f in "${entries[@]}"; do
        if [ -f "$f" ]; then
            rm -f "$f"
            echo "Removed shortcut $f"
        fi
    done
    if [ -d "$data_dir" ]; then
        rm -rf "$data_dir"
        echo "Removed data folder $data_dir"
    fi
    echo
    echo "PDF Editor has been uninstalled. To finish, delete this folder:"
    echo "    $root"
    exit 0
fi

"$root/startPdfEditor.sh" --setup-only

mkdir -p "$apps_dir"
for f in "${entries[@]}"; do
    [ -d "$(dirname "$f")" ] || continue
    cat > "$f" <<EOF
[Desktop Entry]
Type=Application
Name=$name
Comment=Open, reorder and delete PDF pages
Exec="$root/.venv/bin/python" "$root/app.py"
Path=$root
Icon=$root/static/icon.png
Terminal=false
Categories=Office;Viewer;
EOF
    chmod +x "$f"
    # GNOME only launches Desktop icons marked as trusted.
    gio set "$f" metadata::trusted true 2>/dev/null || true
    echo "Created $f"
done

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$apps_dir" 2>/dev/null || true
echo
echo "Done. Start PDF Editor from the application menu or the '$name' icon on the Desktop."
