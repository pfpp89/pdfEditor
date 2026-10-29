"""Start the local PDF editor and open it in its own window.

The editor stops by itself when its last window is closed. Starting it again
while it is running just opens another window.
"""

import argparse
import logging
import secrets
import sys
import threading

from werkzeug.serving import make_server

from pdf_editor import lifecycle

HOST = "127.0.0.1"  # loopback only: nothing is reachable from the network

# pythonw.exe (used by the desktop shortcut) has no console: sys.stdout is None.
HAS_CONSOLE = sys.stdout is not None


def setup_logging():
    if HAS_CONSOLE:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")
    else:
        logging.basicConfig(filename=lifecycle.log_path(), filemode="w", level=logging.INFO,
                            format="%(asctime)s %(levelname)s %(name)s: %(message)s")
        # Without a console nobody reads per-request lines.
        logging.getLogger("werkzeug").setLevel(logging.WARNING)


def main():
    parser = argparse.ArgumentParser(description="Local PDF page editor")
    parser.add_argument("--port", type=int, default=0, help="port to use (default: any free port)")
    parser.add_argument("--no-browser", action="store_true",
                        help="do not open a window (implies --keep-running)")
    parser.add_argument("--browser-tab", action="store_true",
                        help="open in a normal browser tab instead of an app window")
    parser.add_argument("--keep-running", action="store_true",
                        help="do not stop when the last window is closed")
    args = parser.parse_args()
    log = logging.getLogger("pdf-editor")
    prefer_app = not args.browser_tab

    # Only one editor at a time: a second launch opens a window on the first one,
    # waiting for it if it is still starting up.
    lock = lifecycle.acquire_instance_lock()
    if lock is None:
        if args.no_browser:
            raise RuntimeError("PDF Editor is already running.")
        url = lifecycle.wait_for_running_instance()
        if url:
            lifecycle.open_app_window(url, prefer_app=prefer_app)
            return
        raise RuntimeError("PDF Editor seems to be starting already but does not respond.")

    setup_logging()
    token = secrets.token_urlsafe(24)
    # Bind first (port 0 = OS picks a free port) and open the window right away:
    # the browser waits on the listening socket while the heavier libraries load,
    # so the user sees the window at once instead of nothing for a few seconds.
    server = make_server(HOST, args.port, None, threaded=True)
    port = server.socket.getsockname()[1]
    url = f"http://{HOST}:{port}/?t={token}"
    if not args.no_browser:
        threading.Thread(target=lifecycle.open_app_window, args=(url,),
                         kwargs={"prefer_app": prefer_app}, daemon=True).start()

    from pdf_editor.server import create_app  # imports Flask and PyMuPDF (slow on a cold start)

    tracker = lifecycle.ClientTracker()
    server.app = create_app(token, port, tracker)
    lifecycle.register_instance(port, token)
    log.info("PDF editor running at %s", url)
    if args.no_browser or args.keep_running:
        log.info("Press Ctrl+C to stop.")
    else:
        log.info("It stops automatically when its window is closed.")
        # shutdown() must not run on the serving thread, which the watcher isn't.
        tracker.watch(server.shutdown)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        lifecycle.unregister_instance(token)
        lock.close()
        log.info("PDF editor stopped.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # last resort: the user may have no console to see a traceback
        logging.getLogger("pdf-editor").exception("Fatal error")
        detail = f"\n\nDetails: {lifecycle.log_path()}" if not HAS_CONSOLE else ""
        lifecycle.show_error(f"PDF Editor could not start.\n\n{exc}{detail}")
        sys.exit(1)
