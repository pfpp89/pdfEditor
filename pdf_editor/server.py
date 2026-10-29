"""Flask app serving the UI and the local JSON API."""

import hmac
import io
import os
import subprocess
import sys

from flask import Flask, Response, abort, jsonify, request, send_file, send_from_directory

from . import dialogs
from .documents import PdfError, SourceRegistry
from . import lifecycle, winsetup
from .lifecycle import ClientTracker

STATIC_DIR = os.path.join(lifecycle.resource_dir(), "static")
MAX_UPLOAD_BYTES = 1024 * 1024 * 1024  # 1 GiB, uploads only come from this machine
LANGUAGES = {"en", "fr", "pt-PT"}  # must match I18N.LANGUAGES in static/i18n.js


def open_with_default_app(path):
    """Open `path` in the operating system's default application for its type."""
    if sys.platform == "win32":
        os.startfile(path)
        return
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    try:
        subprocess.Popen([opener, path], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    except FileNotFoundError as e:
        raise OSError(f"'{opener}' is not available on this system") from e


def create_app(token, port, tracker=None):
    app = Flask(__name__, static_folder=None)
    tracker = tracker or ClientTracker()
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
    registry = SourceRegistry()
    allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
    # Only the file written by the last Save As may be opened, so the API can't be
    # used to launch arbitrary files.
    last_saved = {"path": None}

    @app.before_request
    def check_request():
        # Reject DNS-rebinding attempts: only our own loopback host is accepted.
        if request.host not in allowed_hosts:
            abort(403)
        if request.path.startswith("/api/"):
            supplied = request.headers.get("X-Token") or request.args.get("t") or ""
            if not hmac.compare_digest(supplied, token):
                abort(403)

    @app.after_request
    def security_headers(resp):
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' blob:; style-src 'self'; "
            "script-src 'self'; connect-src 'self'; frame-ancestors 'none'"
        )
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "no-referrer"
        return resp

    @app.errorhandler(PdfError)
    def pdf_error(e):
        return jsonify(e.to_json()), 400

    @app.errorhandler(dialogs.DialogUnavailable)
    def no_dialog(e):
        return jsonify(no_dialog=True, error=str(e)), 501

    # ---- static UI -------------------------------------------------------

    @app.get("/")
    def index():
        return send_from_directory(STATIC_DIR, "index.html")

    @app.get("/static/<path:filename>")
    def static_files(filename):
        return send_from_directory(STATIC_DIR, filename)

    # ---- API -------------------------------------------------------------

    @app.get("/api/ping")
    def ping():
        return jsonify(ok=True)

    def client_id():
        body = request.get_json(force=True, silent=True) or {}
        cid = body.get("id")
        if not isinstance(cid, str) or not cid:
            abort(400)
        return cid[:64]

    @app.get("/api/settings")
    def get_settings():
        return jsonify(lifecycle.load_settings())

    @app.post("/api/settings")
    def set_settings():
        body = request.get_json(force=True, silent=True) or {}
        lang = body.get("lang")
        if lang not in LANGUAGES:
            abort(400)
        return jsonify(lifecycle.save_settings(lang=lang))

    @app.get("/api/install")
    def install_status():
        return jsonify(state=winsetup.install_state())

    @app.post("/api/install")
    def install():
        """Answer to the first-launch offer (PdfEditor.exe on Windows only)."""
        if winsetup.install_state() != "offer":
            abort(409)
        body = request.get_json(force=True, silent=True) or {}
        if not body.get("create"):
            winsetup.decline()
            return jsonify(installed=False)
        try:
            shortcuts = winsetup.install(body.get("name") or lifecycle.APP_NAME)
        except OSError as e:
            raise PdfError("install_failed", reason=e.strerror or e) from e
        return jsonify(installed=True, shortcuts=shortcuts)

    @app.post("/api/heartbeat")
    def heartbeat():
        tracker.beat(client_id())
        return jsonify(ok=True)

    @app.post("/api/bye")
    def bye():
        """Sent with navigator.sendBeacon when an editor window closes."""
        tracker.bye(client_id())
        return "", 204

    def dialog_texts(*keys):
        """Localized dialog strings sent by the UI (e.g. title), length-limited."""
        body = request.get_json(silent=True) or {}
        texts = body.get("dialog") or {}
        return {k: str(texts[k])[:200] for k in keys if isinstance(texts.get(k), str) and texts[k]}

    def load_paths(paths):
        added, errors = [], []
        for path in paths:
            try:
                added.append(registry.add_file(path).to_json())
            except PdfError as e:
                errors.append(e.to_json())
        return jsonify(sources=added, errors=errors)

    @app.post("/api/open")
    def open_file():
        paths = dialogs.ask_open_files(multiple=False, **dialog_texts("title", "pdf_label", "all_label"))
        if not paths:
            return jsonify(cancelled=True)
        registry.clear()
        return load_paths(paths)

    @app.post("/api/append")
    def append_files():
        paths = dialogs.ask_open_files(multiple=True, **dialog_texts("title", "pdf_label", "all_label"))
        if not paths:
            return jsonify(cancelled=True)
        return load_paths(paths)

    @app.post("/api/upload")
    def upload():
        """Fallback when native dialogs are unavailable: files come from <input type=file>."""
        if request.args.get("replace") == "1":
            registry.clear()
        added, errors = [], []
        for f in request.files.getlist("files"):
            try:
                added.append(registry.add_bytes(f.read(), f.filename or "upload.pdf").to_json())
            except PdfError as e:
                errors.append(e.to_json())
        return jsonify(sources=added, errors=errors)

    @app.post("/api/unlock")
    def unlock():
        body = request.get_json(force=True)
        return jsonify(source=registry.unlock(body["id"], body.get("password", "")).to_json())

    @app.get("/api/page/<source_id>/<int:page_no>")
    def page_image(source_id, page_no):
        width = request.args.get("w", 200, type=int)
        png = registry.render_page(source_id, page_no, width)
        return Response(png, mimetype="image/png",
                        headers={"Cache-Control": "private, max-age=3600"})

    def requested_pages():
        body = request.get_json(force=True)
        return [(p["src"], int(p["page"])) for p in body.get("pages", [])], body

    @app.post("/api/save")
    def save():
        pages, body = requested_pages()
        registry.compose(pages).close()  # validate before showing the dialog
        path = dialogs.ask_save_file(body.get("name") or "edited.pdf",
                                     **dialog_texts("title", "pdf_label", "all_label"))
        if not path:
            return jsonify(cancelled=True)
        try:
            registry.save(pages, path)
        except OSError as e:
            raise PdfError("save_failed", path=path, reason=e.strerror) from e
        last_saved["path"] = path
        return jsonify(path=path)

    @app.post("/api/open-saved")
    def open_saved():
        path = last_saved["path"]
        if not path or not os.path.isfile(path):
            raise PdfError("saved_not_found")
        try:
            open_with_default_app(path)
        except OSError as e:
            raise PdfError("open_failed", reason=e.strerror or e) from e
        return jsonify(opened=path)

    @app.post("/api/download")
    def download():
        """Fallback save without native dialogs: the browser saves the bytes."""
        pages, body = requested_pages()
        data = registry.to_bytes(pages)
        return send_file(io.BytesIO(data), mimetype="application/pdf", as_attachment=True,
                         download_name=body.get("name") or "edited.pdf")

    return app
