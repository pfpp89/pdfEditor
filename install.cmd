@echo off
rem Double-clickable installer: runs install.ps1 (Windows opens .ps1 files in Notepad).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
