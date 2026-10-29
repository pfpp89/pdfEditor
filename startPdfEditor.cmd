@echo off
rem Double-clickable launcher: Windows opens .ps1 files in Notepad by default,
rem so this runs startPdfEditor.ps1 with PowerShell instead.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0startPdfEditor.ps1" %*
