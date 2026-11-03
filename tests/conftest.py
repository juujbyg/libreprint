# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path

import pytest

from libreprint.i18n import set_language

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def _english(monkeypatch):
    """Messages are compared in English whatever the language of the machine."""
    monkeypatch.setenv("LIBREPRINT_LANG", "en")
    set_language("en")
