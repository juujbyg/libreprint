# SPDX-License-Identifier: GPL-2.0-or-later
"""Translations for user-facing messages.

Messages are written in English and wrapped in ``_()``. A language is a flat module
``lang_<code>.py`` next to this file that defines ``MESSAGES``, a dict mapping the English
text to its translation. A message without a translation is shown in English. Placeholders
(``{name}``) and Pango markup must be kept as they are in the English text.

To add a language: copy ``lang_es.py`` to ``lang_<code>.py``, translate the values and add the code
to ``LANGUAGES``.
"""

from __future__ import annotations

import importlib
import os
from collections.abc import Mapping

LANGUAGES = ("es", "de", "fr", "nl")

_messages: dict[str, str] = {}
_current = "en"


def detect(env: Mapping[str, str] | None = None) -> str:
    """Language code for the environment (LIBREPRINT_LANG, LANGUAGE, LC_ALL, LC_MESSAGES, LANG)."""
    source: Mapping[str, str] = os.environ if env is None else env
    for var in ("LIBREPRINT_LANG", "LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        for part in source.get(var, "").split(":"):
            code = part.split(".")[0].split("@")[0].split("_")[0].lower()
            if code in ("c", "posix"):
                return "en"
            if code == "en" or code in LANGUAGES:
                return code
    return "en"


def set_language(code: str | None = None) -> str:
    """Select the language (default: detect it). Returns the code actually in use."""
    global _messages, _current
    code = detect() if code is None else code
    _messages = {}
    _current = "en"
    if code in LANGUAGES:
        module = importlib.import_module(f"libreprint.lang_{code}")
        _messages = module.MESSAGES
        _current = code
    return _current


def current() -> str:
    return _current


def _(text: str) -> str:
    return _messages.get(text, text)
