#!/usr/bin/env bash
# Removes the PDF Editor shortcuts and its data (see install.sh). Delete this folder afterwards.
exec "$(dirname "$(readlink -f "$0")")/install.sh" --uninstall "$@"
