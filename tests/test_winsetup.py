import os
import sys

import pytest

from pdf_editor import lifecycle, winsetup
from pdf_editor.server import create_app

HEADERS = {"Host": "127.0.0.1:5000", "X-Token": "tok"}


@pytest.fixture
def frozen_exe(tmp_path, monkeypatch):
    """Pretend to be PdfEditor.exe on Windows, saved in a normal folder.

    pytest's tmp_path itself lives in the system temp folder, so the "temporary
    locations" are redirected to sub-folders of it.
    """
    monkeypatch.setattr(winsetup.tempfile, "gettempdir", lambda: str(tmp_path / "Temp"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    exe = tmp_path / "Documents" / "PdfEditor.exe"
    exe.parent.mkdir()
    exe.write_bytes(b"MZ")
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setattr(lifecycle, "state_dir", lambda: str(state))
    monkeypatch.setattr(lifecycle, "FROZEN", True)
    # Windows paths are case-insensitive, also when the tests run on Linux.
    # Checked before sys.platform is faked below.
    if sys.platform != "win32":
        monkeypatch.setattr(winsetup.os.path, "normcase", str.lower)
    monkeypatch.setattr(winsetup.sys, "platform", "win32")
    monkeypatch.setattr(winsetup, "exe_path", lambda: str(exe))
    monkeypatch.setattr(winsetup, "registered_exe", lambda: None)
    return exe


def test_not_offered_when_running_from_python(monkeypatch):
    monkeypatch.setattr(lifecycle, "FROZEN", False)
    assert winsetup.install_state() == "none"


def test_offered_on_first_launch(frozen_exe):
    assert winsetup.install_state() == "offer"


def test_not_offered_once_installed_here(frozen_exe, monkeypatch):
    monkeypatch.setattr(winsetup, "registered_exe", lambda: str(frozen_exe).upper())
    assert winsetup.install_state() == "none"


def test_offered_again_when_exe_moved(frozen_exe, monkeypatch):
    monkeypatch.setattr(winsetup, "registered_exe", lambda: r"C:\old\place\PdfEditor.exe")
    assert winsetup.install_state() == "offer"


def test_declining_is_remembered_for_this_exe(frozen_exe, monkeypatch):
    winsetup.decline()
    assert winsetup.install_state() == "none"
    monkeypatch.setattr(winsetup, "exe_path", lambda: r"C:\elsewhere\PdfEditor.exe")
    assert winsetup.install_state() == "offer"


def test_temporary_location_detected(frozen_exe, monkeypatch):
    for folder in (winsetup.tempfile.gettempdir(),
                   os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Windows", "INetCache")):
        attachment = os.path.join(folder, "Content.Outlook", "PdfEditor.exe")
        monkeypatch.setattr(winsetup, "exe_path", lambda: attachment)
        assert winsetup.install_state() == "temporary"


def test_install_endpoint_records_no(frozen_exe):
    client = create_app("tok", 5000).test_client()
    assert client.get("/api/install", headers=HEADERS).get_json() == {"state": "offer"}
    assert client.post("/api/install", json={"create": False}, headers=HEADERS).status_code == 200
    assert client.get("/api/install", headers=HEADERS).get_json() == {"state": "none"}
    # Nothing left to answer.
    assert client.post("/api/install", json={"create": True}, headers=HEADERS).status_code == 409


def test_install_endpoint_creates(frozen_exe, monkeypatch):
    calls = []
    monkeypatch.setattr(winsetup, "install", lambda name: calls.append(name) or ["a.lnk"])
    client = create_app("tok", 5000).test_client()
    res = client.post("/api/install", json={"create": True, "name": "Editor de PDF"}, headers=HEADERS)
    assert res.get_json() == {"installed": True, "shortcuts": ["a.lnk"]}
    assert calls == ["Editor de PDF"]


def test_shortcut_names_are_sanitized():
    assert winsetup._safe_name('Editor: "PDF"/?') == "Editor PDF"
    assert winsetup._safe_name("   ") == lifecycle.APP_NAME


def test_uninstall_refuses_outside_the_exe(monkeypatch):
    shown = []
    monkeypatch.setattr(lifecycle, "FROZEN", False)
    monkeypatch.setattr(lifecycle, "show_error", shown.append)
    assert winsetup.uninstall() == 1
    assert "uninstall.cmd" in shown[0]


def test_native_texts_complete():
    keys = set(lifecycle.NATIVE_TEXTS["en"])
    for code, texts in lifecycle.NATIVE_TEXTS.items():
        assert set(texts) == keys, code


def test_native_text_follows_chosen_language(tmp_path, monkeypatch):
    monkeypatch.setattr(lifecycle, "state_dir", lambda: str(tmp_path))
    assert lifecycle.native_text("details") == "Details"
    lifecycle.save_settings(lang="pt-PT")
    assert lifecycle.native_text("details") == "Detalhes"
