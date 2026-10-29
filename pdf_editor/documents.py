"""PDF source management, page rendering and output composition (PyMuPDF)."""

import os
import sys
import tempfile
import threading
import uuid
from collections import OrderedDict

# PyMuPDF 2 installs AI add-ons (layout analysis with ONNX models, Markdown export)
# and loads them on import when present. This editor only copies and renders pages,
# so block them: PyMuPDF skips them on ImportError. That saves startup time, and
# build_exe.ps1 leaves them out of PdfEditor.exe (their model files broke the bundle).
for _optional in ("pymupdf.layout", "pymupdf4llm"):
    sys.modules.setdefault(_optional, None)

import pymupdf  # noqa: E402


# English fallback texts. The UI translates errors by code ("error.<code>" in
# static/locales/*.json) and only shows these when no translation exists.
ERROR_MESSAGES = {
    "read_failed": "Cannot read {path}: {reason}",
    "invalid_pdf": "{name} is not a valid PDF file.",
    "unknown_document": "Unknown document. Please reopen the file.",
    "wrong_password": "Wrong password.",
    "locked": "{name} is password protected.",
    "page_out_of_range": "Page out of range.",
    "no_pages": "The document has no pages.",
    "save_failed": "Could not save to {path}: {reason}",
    "saved_not_found": "The saved file could not be found.",
    "open_failed": "Could not open the file: {reason}",
    "install_failed": "Could not create the shortcuts: {reason}",
}


class PdfError(Exception):
    """A user-facing error, identified by a code so the UI can translate it."""

    def __init__(self, code, **params):
        self.code = code
        self.params = {k: str(v) for k, v in params.items()}
        super().__init__(ERROR_MESSAGES[code].format(**self.params))

    def to_json(self):
        return {"error": str(self), "code": self.code, "params": self.params}


class Source:
    def __init__(self, source_id, name, path, doc):
        self.id = source_id
        self.name = name
        self.path = path
        self.doc = doc

    @property
    def locked(self):
        return self.doc.is_encrypted and self.doc.needs_pass

    @property
    def page_count(self):
        return 0 if self.locked else self.doc.page_count

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "page_count": self.page_count,
            "locked": self.locked,
        }


class SourceRegistry:
    """Holds every PDF opened in the session.

    Files are read fully into memory, so no OS file handle stays open: this lets
    the user save over one of the source files (important on Windows).
    PyMuPDF is not thread-safe, so every document access goes through one lock.
    """

    CACHE_SIZE = 400

    def __init__(self):
        self._sources = {}
        self._lock = threading.RLock()
        self._cache = OrderedDict()

    def clear(self):
        with self._lock:
            for src in self._sources.values():
                src.doc.close()
            self._sources.clear()
            self._cache.clear()

    def add_file(self, path, name=None):
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError as e:
            raise PdfError("read_failed", path=path, reason=e.strerror) from e
        return self.add_bytes(data, name or os.path.basename(path), path)

    def add_bytes(self, data, name, path=None):
        try:
            doc = pymupdf.open(stream=data, filetype="pdf")
        except Exception as e:
            raise PdfError("invalid_pdf", name=name) from e
        if not doc.is_pdf:
            doc.close()
            raise PdfError("invalid_pdf", name=name)
        src = Source(uuid.uuid4().hex[:12], name, path, doc)
        with self._lock:
            self._sources[src.id] = src
        return src

    def get(self, source_id):
        src = self._sources.get(source_id)
        if src is None:
            raise PdfError("unknown_document")
        return src

    def unlock(self, source_id, password):
        with self._lock:
            src = self.get(source_id)
            if not src.locked:
                return src
            if not src.doc.authenticate(password):
                raise PdfError("wrong_password")
            return src

    def render_page(self, source_id, page_no, width):
        """Return a PNG of the page scaled to `width` pixels wide."""
        width = max(50, min(int(width), 2400))
        key = (source_id, page_no, width)
        with self._lock:
            png = self._cache.get(key)
            if png is not None:
                self._cache.move_to_end(key)
                return png
            src = self.get(source_id)
            if src.locked:
                raise PdfError("locked", name=src.name)
            if not 0 <= page_no < src.page_count:
                raise PdfError("page_out_of_range")
            page = src.doc[page_no]
            zoom = width / page.rect.width
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
            png = pix.tobytes("png")
            self._cache[key] = png
            if len(self._cache) > self.CACHE_SIZE:
                self._cache.popitem(last=False)
            return png

    def compose(self, pages):
        """Build a new document from an ordered list of (source_id, page_no)."""
        if not pages:
            raise PdfError("no_pages")
        out = pymupdf.open()
        with self._lock:
            for source_id, start, end in _runs(pages):
                src = self.get(source_id)
                if src.locked:
                    raise PdfError("locked", name=src.name)
                if not (0 <= start < src.page_count and 0 <= end < src.page_count):
                    raise PdfError("page_out_of_range")
                out.insert_pdf(src.doc, from_page=start, to_page=end)
        return out

    def save(self, pages, out_path):
        """Compose `pages` and write them atomically to `out_path`."""
        out = self.compose(pages)
        directory = os.path.dirname(os.path.abspath(out_path))
        fd, tmp_path = tempfile.mkstemp(suffix=".pdf", dir=directory)
        os.close(fd)
        try:
            out.save(tmp_path, garbage=3, deflate=True)
            out.close()
            os.replace(tmp_path, out_path)
        except Exception:
            out.close()
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def to_bytes(self, pages):
        out = self.compose(pages)
        try:
            return out.tobytes(garbage=3, deflate=True)
        finally:
            out.close()


def _runs(pages):
    """Group consecutive ascending pages of the same source: [(src, start, end)]."""
    runs = []
    for source_id, page_no in pages:
        if runs and runs[-1][0] == source_id and runs[-1][2] + 1 == page_no:
            runs[-1][2] = page_no
        else:
            runs.append([source_id, page_no, page_no])
    return [tuple(r) for r in runs]
