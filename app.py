"""Start the local PDF editor and open it in the default browser."""

import argparse
import secrets
import threading
import webbrowser

from werkzeug.serving import make_server

from pdf_editor.server import create_app

HOST = "127.0.0.1"  # loopback only: nothing is reachable from the network


def main():
    parser = argparse.ArgumentParser(description="Local PDF page editor")
    parser.add_argument("--port", type=int, default=0, help="port to use (default: any free port)")
    parser.add_argument("--no-browser", action="store_true", help="do not open a browser")
    args = parser.parse_args()

    token = secrets.token_urlsafe(24)
    # Bind first (port 0 = OS picks a free port), then build the app for that port.
    server = make_server(HOST, args.port, None, threaded=True)
    port = server.socket.getsockname()[1]
    server.app = create_app(token, port)

    url = f"http://{HOST}:{port}/?t={token}"
    print(f"PDF editor running at {url}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    if not args.no_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
