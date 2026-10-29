import json
import re
from pathlib import Path

import pytest

from pdf_editor.documents import ERROR_MESSAGES

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
LANGUAGES = ["en", "fr", "pt-PT"]
PLACEHOLDER = re.compile(r"\{(\w+)\}")


def load(code):
    return json.loads((STATIC / "locales" / f"{code}.json").read_text(encoding="utf-8"))


def placeholders(value):
    texts = value.values() if isinstance(value, dict) else [value]
    return {name for text in texts for name in PLACEHOLDER.findall(text)}


@pytest.mark.parametrize("code", LANGUAGES[1:])
def test_same_keys_and_placeholders_as_english(code):
    en, other = load("en"), load(code)
    assert set(other) == set(en), "missing/extra keys"
    for key, value in en.items():
        assert type(other[key]) is type(value), key
        if isinstance(value, dict):
            assert set(other[key]) == set(value) == {"one", "other"}, key
        assert placeholders(other[key]) == placeholders(value), key


def test_every_ui_key_exists():
    en = load("en")
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    js = (STATIC / "app.js").read_text(encoding="utf-8")
    used = set(re.findall(r'data-i18n(?:-title)?="([\w.]+)"', html))
    used |= set(re.findall(r'\bt\("([\w.]+)"', js))
    used |= set(re.findall(r'dialogTexts\("([\w.]+)"\)', js))
    assert used, "no keys found"
    assert used - set(en) == set()


def test_every_server_error_code_is_translated():
    en = load("en")
    assert {f"error.{code}" for code in ERROR_MESSAGES} <= set(en)
