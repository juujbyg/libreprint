# SPDX-License-Identifier: GPL-2.0-or-later
import ast
import importlib
import re
from pathlib import Path

import pytest

from libreprint import i18n

SRC = Path(__file__).parent.parent / "src" / "libreprint"
PLACEHOLDER = re.compile(r"\{\w+\}")


def _msgids() -> set[str]:
    ids: set[str] = set()
    for path in SRC.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "_"
                and node.args
                and isinstance(node.args[0], ast.Constant)
            ):
                ids.add(node.args[0].value)
    return ids


@pytest.mark.parametrize("code", i18n.LANGUAGES)
def test_catalog_is_complete_and_keeps_placeholders(code):
    messages = importlib.import_module(f"libreprint.lang_{code}").MESSAGES
    ids = _msgids()
    assert not ids - set(messages), f"untranslated: {sorted(ids - set(messages))}"
    assert not set(messages) - ids, f"stale: {sorted(set(messages) - ids)}"
    for english, text in messages.items():
        assert sorted(PLACEHOLDER.findall(english)) == sorted(PLACEHOLDER.findall(text)), english


def test_detect():
    assert i18n.detect({"LANG": "de_DE.UTF-8"}) == "de"
    assert i18n.detect({"LANGUAGE": "fr:en", "LANG": "es_ES.UTF-8"}) == "fr"
    assert i18n.detect({"LIBREPRINT_LANG": "es", "LANG": "de_DE"}) == "es"
    assert i18n.detect({"LANG": "C.UTF-8"}) == "en"
    assert i18n.detect({"LANG": "zh_CN.UTF-8"}) == "en"


def test_untranslated_falls_back_to_english():
    try:
        assert i18n.set_language("es") == "es"
        assert i18n._("no such message") == "no such message"
    finally:
        i18n.set_language("en")
