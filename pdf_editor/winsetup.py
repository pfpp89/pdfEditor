"""Self-installation of the single-file PdfEditor.exe on Windows (per user, no admin rights).

- On first launch the UI offers to create Desktop and Start menu shortcuts. Accepting
  also registers the app in Windows "Installed apps" (Settings > Apps).
- "Uninstall" there runs `PdfEditor.exe --uninstall`, which removes the shortcuts, the
  registry entry, the data folder and finally the .exe itself.
"""

import datetime
import os
import shutil
import subprocess
import sys
import tempfile

from . import __version__, lifecycle

UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\PdfEditor"
CREATE_NO_WINDOW = 0x08000000

# Creates one shortcut in each folder and prints the paths it wrote.
# Values come in through environment variables to avoid any quoting problems.
_SHORTCUT_PS = r"""
$shell = New-Object -ComObject WScript.Shell
foreach ($folder in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))) {
    $path = Join-Path $folder ($env:PDFED_NAME + '.lnk')
    $lnk = $shell.CreateShortcut($path)
    $lnk.TargetPath = $env:PDFED_TARGET
    $lnk.WorkingDirectory = $env:PDFED_WORKDIR
    $lnk.IconLocation = $env:PDFED_TARGET + ',0'
    $lnk.Description = $env:PDFED_DESC
    $lnk.Save()
    Write-Output $path
}
"""


def exe_path():
    return os.path.abspath(sys.executable)


def _winreg():
    import winreg
    return winreg


def registered_exe():
    """The .exe path recorded in "Installed apps", or None."""
    if sys.platform != "win32":
        return None
    winreg = _winreg()
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as key:
            return winreg.QueryValueEx(key, "ExePath")[0]
    except OSError:
        return None


def _is_temporary(path):
    """True for e-mail attachments opened directly and similar throw-away locations."""
    folders = [tempfile.gettempdir()]
    local = os.environ.get("LOCALAPPDATA")
    if local:
        folders.append(os.path.join(local, "Microsoft", "Windows", "INetCache"))  # Outlook
    path = os.path.normcase(os.path.abspath(path))
    for folder in folders:
        folder = os.path.normcase(os.path.abspath(folder))
        if path == folder or path.startswith(folder + os.sep):
            return True
    return False


def install_state():
    """What the UI should propose: "offer", "temporary" or "none"."""
    if not lifecycle.FROZEN or sys.platform != "win32":
        return "none"
    exe = exe_path()
    registered = registered_exe()
    if registered and os.path.normcase(registered) == os.path.normcase(exe):
        return "none"
    if _is_temporary(exe):
        return "temporary"
    if lifecycle.load_settings().get("install_declined") == exe:
        return "none"
    return "offer"


def decline():
    lifecycle.save_settings(install_declined=exe_path())


def install(name):
    """Create the shortcuts and the "Installed apps" entry for the running .exe."""
    exe = exe_path()
    env = dict(os.environ, PDFED_NAME=_safe_name(name), PDFED_TARGET=exe,
               PDFED_WORKDIR=os.path.dirname(exe), PDFED_DESC="Open, reorder and delete PDF pages")
    proc = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-Command", _SHORTCUT_PS],
        env=env, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW,
    )
    if proc.returncode != 0:
        raise OSError(proc.stderr.strip() or "could not create the shortcuts")
    shortcuts = [line.strip() for line in proc.stdout.splitlines() if line.strip()]

    # A previous install from another location: drop its shortcuts if renamed.
    for old in _registered_shortcuts():
        if old not in shortcuts and os.path.isfile(old):
            os.remove(old)

    winreg = _winreg()
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as key:
        values = {
            "DisplayName": _safe_name(name),
            "DisplayIcon": f"{exe},0",
            "DisplayVersion": __version__,
            "Publisher": "PDF Editor",
            "InstallLocation": os.path.dirname(exe),
            "InstallDate": datetime.date.today().strftime("%Y%m%d"),
            "UninstallString": f'"{exe}" --uninstall',
            "ExePath": exe,
            "Shortcuts": "|".join(shortcuts),
        }
        for k, v in values.items():
            winreg.SetValueEx(key, k, 0, winreg.REG_SZ, v)
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, os.path.getsize(exe) // 1024)
    lifecycle.save_settings(install_declined=None)
    return shortcuts


def _registered_shortcuts():
    if sys.platform != "win32":
        return []
    winreg = _winreg()
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as key:
            return [p for p in winreg.QueryValueEx(key, "Shortcuts")[0].split("|") if p]
    except OSError:
        return []


def _safe_name(name):
    name = "".join(c for c in str(name) if c not in '<>:"/\\|?*').strip()
    return name[:60] or lifecycle.APP_NAME


def uninstall():
    """Run by `PdfEditor.exe --uninstall` (Settings > Apps > Uninstall). Returns an exit code."""
    if not lifecycle.FROZEN:
        lifecycle.show_error(lifecycle.native_text("not_installable"))
        return 1
    lock = lifecycle.acquire_instance_lock()
    if lock is None:
        lifecycle.show_error(lifecycle.native_text("still_open"))
        return 1
    message = lifecycle.native_text("uninstalled")  # read before the settings are deleted
    problems = []

    for path in _registered_shortcuts():
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError as e:
            problems.append(f"{path}: {e.strerror}")
    winreg = _winreg()
    exe = registered_exe() or exe_path()
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY)
    except FileNotFoundError:
        pass
    except OSError as e:
        problems.append(f"registry: {e.strerror}")

    lock.close()
    shutil.rmtree(lifecycle.state_dir(), ignore_errors=True)

    if problems:
        lifecycle.show_error(lifecycle.native_text("uninstall_failed") + "\n\n" + "\n".join(problems))
    else:
        lifecycle.show_info(message)
    # Last: the .exe is in use until this process (and the bundle's launcher) exits.
    _delete_after_exit(exe)
    return 1 if problems else 0


def _delete_after_exit(exe):
    """A running .exe can't delete itself: a hidden cmd.exe does it a few seconds later."""
    if not (exe.lower().endswith(".exe") and os.path.isfile(exe)):
        return
    subprocess.Popen(f'cmd.exe /d /c ping -n 6 127.0.0.1 >nul & del /f /q "{exe}"',
                     creationflags=CREATE_NO_WINDOW, close_fds=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
