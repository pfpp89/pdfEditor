"""Desktop-app behaviour: app window, auto-shutdown, single instance, error reporting."""

import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

APP_NAME = "PDF Editor"


# ---- auto-shutdown -----------------------------------------------------------

class ClientTracker:
    """Tracks open editor pages through heartbeats and decides when to exit.

    - A page that says goodbye (window closed) is dropped at once; the app exits
      after `grace` seconds without any page, which lets a page reload reconnect.
    - A page that just stops beating (crash) is dropped after `stale` seconds.
      This is generous because browsers throttle timers in minimized windows.
    - If no page ever connects, the app exits after `startup` seconds.
    """

    def __init__(self, grace=8.0, stale=180.0, startup=120.0, clock=time.monotonic):
        self.grace, self.stale, self.startup = grace, stale, startup
        self._clock = clock
        self._lock = threading.Lock()
        self._clients = {}  # client id -> last heartbeat time
        self._had_clients = False
        self._empty_since = clock()
        self._last_check = clock()

    def beat(self, client_id):
        with self._lock:
            self._clients[client_id] = self._clock()
            self._had_clients = True
            self._empty_since = None

    def bye(self, client_id):
        with self._lock:
            self._clients.pop(client_id, None)
            if not self._clients and self._empty_since is None:
                self._empty_since = self._clock()

    def should_exit(self):
        now = self._clock()
        with self._lock:
            if now - self._last_check > 15:
                # The computer was asleep: nobody could send heartbeats, so
                # restart every timer instead of treating the pages as gone.
                self._clients = {cid: now for cid in self._clients}
                if self._empty_since is not None:
                    self._empty_since = now
            self._last_check = now

            for cid, seen in list(self._clients.items()):
                if now - seen > self.stale:
                    del self._clients[cid]
            if self._clients:
                return False
            if self._empty_since is None:
                self._empty_since = now
            limit = self.grace if self._had_clients else self.startup
            return now - self._empty_since >= limit

    def watch(self, on_exit, interval=1.0):
        """Call `on_exit` from a background thread once the app should stop."""
        def loop():
            while True:
                time.sleep(interval)
                if self.should_exit():
                    on_exit()
                    return
        threading.Thread(target=loop, name="client-watch", daemon=True).start()


# ---- files -------------------------------------------------------------------

def state_dir():
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        path = os.path.join(base, "PdfEditor")
    else:
        base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
        path = os.path.join(base, "pdf-editor")
    os.makedirs(path, exist_ok=True)
    return path


def log_path():
    return os.path.join(state_dir(), "pdf-editor.log")


def _instance_path():
    return os.path.join(state_dir(), "instance.json")


# ---- settings ----------------------------------------------------------------
# Kept on disk rather than in the browser: the editor's address changes at every
# start (random port), and browser storage is per address.

def load_settings():
    try:
        with open(os.path.join(state_dir(), "settings.json"), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings(**changes):
    data = load_settings()
    data.update(changes)
    path = os.path.join(state_dir(), "settings.json")
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(path + ".tmp", path)
    return data


# ---- single instance ---------------------------------------------------------

def acquire_instance_lock():
    """Take an OS file lock held for the whole life of this process.

    Returns the open lock file (keep a reference to it), or None when another
    editor process already holds it, even one that is still starting up.
    """
    f = open(os.path.join(state_dir(), "instance.lock"), "a+")
    try:
        if sys.platform == "win32":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        return None
    return f


def wait_for_running_instance(timeout=30.0):
    """URL of the instance that holds the lock, once it is ready; None on timeout."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        url = find_running_instance()
        if url:
            return url
        time.sleep(0.5)
    return None


def find_running_instance():
    """Return the URL of an already running editor, or None."""
    try:
        with open(_instance_path(), encoding="utf-8") as f:
            info = json.load(f)
        port, token = int(info["port"]), str(info["token"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    # Bypass any system proxy: this is a loopback request.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(f"http://127.0.0.1:{port}/api/ping", headers={"X-Token": token})
    try:
        with opener.open(req, timeout=2) as res:
            if res.status == 200:
                return f"http://127.0.0.1:{port}/?t={token}"
    except OSError:
        pass
    return None


def register_instance(port, token):
    # Owner-only on Linux; on Windows %LOCALAPPDATA% is already private to the user.
    fd = os.open(_instance_path(), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"port": port, "token": token, "pid": os.getpid()}, f)


def unregister_instance(token):
    """Remove the instance file, but only if it still describes this process."""
    path = _instance_path()
    try:
        with open(path, encoding="utf-8") as f:
            if json.load(f).get("token") != token:
                return
        os.remove(path)
    except (OSError, ValueError):
        pass


# ---- app window --------------------------------------------------------------

def _windows_browser():
    import winreg

    for exe in ("msedge.exe", "chrome.exe"):
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                key = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe}"
                with winreg.OpenKey(hive, key) as k:
                    path = winreg.QueryValue(k, None)
                if path and os.path.isfile(path):
                    return path
            except OSError:
                continue
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"),
                 os.environ.get("LOCALAPPDATA")):
        for rel in (r"Microsoft\Edge\Application\msedge.exe", r"Google\Chrome\Application\chrome.exe"):
            if base and os.path.isfile(os.path.join(base, rel)):
                return os.path.join(base, rel)
    return None


def find_app_browser():
    """A Chromium-based browser that supports --app windows, or None."""
    if sys.platform == "win32":
        return _windows_browser()
    for name in ("microsoft-edge", "microsoft-edge-stable", "google-chrome", "google-chrome-stable",
                 "chromium", "chromium-browser", "brave-browser"):
        path = shutil.which(name)
        if path:
            return path
    return None


def _window_geometry():
    """Size and position for the app window: 90% of the screen, centred."""
    width, height = 1280, 860
    if sys.platform == "win32":
        try:
            import ctypes
            sw = ctypes.windll.user32.GetSystemMetrics(16)  # SM_CXFULLSCREEN
            sh = ctypes.windll.user32.GetSystemMetrics(17)  # SM_CYFULLSCREEN
            if sw > 0 and sh > 0:
                width, height = min(int(sw * 0.9), 1600), int(sh * 0.9)
                return width, height, (sw - width) // 2, (sh - height) // 2
        except (AttributeError, OSError):
            pass
    return width, height, None, None


def open_app_window(url, prefer_app=True):
    """Open the editor in a standalone browser window (no tabs, no address bar)."""
    browser = find_app_browser() if prefer_app else None
    if browser:
        width, height, x, y = _window_geometry()
        args = [browser, f"--app={url}", f"--window-size={width},{height}"]
        if x is not None:
            args.append(f"--window-position={x},{y}")
        try:
            subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, close_fds=True)
            return
        except OSError:
            pass
    webbrowser.open(url)


# ---- errors ------------------------------------------------------------------

def show_error(message):
    """Show an error to a user who may have no console window."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, message, APP_NAME, 0x10)  # MB_ICONERROR
            return
        except (AttributeError, OSError):
            pass
    else:
        for cmd in (["zenity", "--error", "--title", APP_NAME, "--text", message],
                    ["kdialog", "--title", APP_NAME, "--error", message]):
            if shutil.which(cmd[0]):
                subprocess.run(cmd, check=False)
                return
    if sys.stderr:
        print(message, file=sys.stderr)
