@echo off
rem Double-clickable: builds dist\PdfEditor.exe (see build_exe.ps1).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_exe.ps1" %*
