@echo off
rem Double-clickable uninstaller: removes the PDF Editor shortcuts and its data
rem (see install.ps1). Delete this folder afterwards.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Uninstall %*
