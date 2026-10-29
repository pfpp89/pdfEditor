import pymupdf
import pytest

from pdf_editor.documents import PdfError, SourceRegistry, _runs
from pdf_editor.server import create_app


def make_pdf(path, label, pages, password=None):
    doc = pymupdf.open()
    for i in range(pages):
        doc.new_page().insert_text((72, 72), f"{label}{i}")
    if password:
        doc.save(path, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw=password, owner_pw=password)
    else:
        doc.save(path)
    doc.close()
    return str(path)


def page_texts(path):
    with pymupdf.open(path) as doc:
        return [page.get_text().strip() for page in doc]


@pytest.fixture
def registry():
    reg = SourceRegistry()
    yield reg
    reg.clear()


def test_runs_groups_consecutive_pages():
    pages = [("a", 0), ("a", 1), ("a", 2), ("b", 0), ("a", 5), ("a", 4)]
    assert _runs(pages) == [("a", 0, 2), ("b", 0, 0), ("a", 5, 5), ("a", 4, 4)]


def test_reorder_delete_and_mix_sources(tmp_path, registry):
    a = registry.add_file(make_pdf(tmp_path / "a.pdf", "A", 4))
    b = registry.add_file(make_pdf(tmp_path / "b.pdf", "B", 3))
    order = [(b.id, 2), (a.id, 0), (a.id, 1), (b.id, 0), (a.id, 3)]  # A2 and B1 deleted
    out = tmp_path / "out.pdf"
    registry.save(order, str(out))
    assert page_texts(out) == ["B2", "A0", "A1", "B0", "A3"]


def test_save_over_source_file(tmp_path, registry):
    path = make_pdf(tmp_path / "a.pdf", "A", 3)
    a = registry.add_file(path)
    registry.save([(a.id, 2), (a.id, 0)], path)
    assert page_texts(path) == ["A2", "A0"]


def test_empty_document_rejected(registry):
    with pytest.raises(PdfError):
        registry.compose([])


def test_invalid_file_rejected(tmp_path, registry):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a pdf at all")
    with pytest.raises(PdfError):
        registry.add_file(str(bad))


def test_encrypted_pdf_unlock(tmp_path, registry):
    src = registry.add_file(make_pdf(tmp_path / "e.pdf", "E", 2, password="secret"))
    assert src.locked and src.page_count == 0
    with pytest.raises(PdfError):
        registry.unlock(src.id, "wrong")
    registry.unlock(src.id, "secret")
    assert not src.locked and src.page_count == 2
    out = tmp_path / "out.pdf"
    registry.save([(src.id, 1)], str(out))
    assert page_texts(out) == ["E1"]


def test_render_page_png(tmp_path, registry):
    a = registry.add_file(make_pdf(tmp_path / "a.pdf", "A", 1))
    png = registry.render_page(a.id, 0, 200)
    assert png.startswith(b"\x89PNG")
    with pytest.raises(PdfError):
        registry.render_page(a.id, 5, 200)


def test_api_requires_token_and_local_host(tmp_path):
    client = create_app("tok", 5000).test_client()
    host = {"Host": "127.0.0.1:5000"}
    assert client.post("/api/download", json={"pages": []}, headers=host).status_code == 403
    assert client.post("/api/download", json={"pages": []},
                       headers={"Host": "evil.example:5000", "X-Token": "tok"}).status_code == 403
    assert client.get("/", headers=host).status_code == 200

    pdf = make_pdf(tmp_path / "a.pdf", "A", 2)
    with open(pdf, "rb") as f:
        res = client.post("/api/upload", data={"files": (f, "a.pdf")},
                          headers={**host, "X-Token": "tok"})
    src = res.get_json()["sources"][0]
    res = client.post("/api/download", json={"pages": [{"src": src["id"], "page": 1}]},
                      headers={**host, "X-Token": "tok"})
    assert res.status_code == 200
    out = tmp_path / "dl.pdf"
    out.write_bytes(res.data)
    assert page_texts(out) == ["A1"]


def test_open_saved_only_opens_last_saved_file(tmp_path, monkeypatch):
    from pdf_editor import server

    opened = []
    out = tmp_path / "out.pdf"
    monkeypatch.setattr(server, "open_with_default_app", opened.append)
    monkeypatch.setattr(server.dialogs, "ask_save_file", lambda *a, **k: str(out))
    client = server.create_app("tok", 5000).test_client()
    headers = {"Host": "127.0.0.1:5000", "X-Token": "tok"}

    # Nothing saved yet: refused.
    assert client.post("/api/open-saved", headers=headers).status_code == 400
    assert opened == []

    with open(make_pdf(tmp_path / "a.pdf", "A", 2), "rb") as f:
        src = client.post("/api/upload", data={"files": (f, "a.pdf")},
                          headers=headers).get_json()["sources"][0]
    res = client.post("/api/save", json={"pages": [{"src": src["id"], "page": 1}]}, headers=headers)
    assert res.get_json()["path"] == str(out)

    assert client.post("/api/open-saved", headers=headers).status_code == 200
    assert opened == [str(out)]
