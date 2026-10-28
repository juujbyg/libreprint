# SPDX-License-Identifier: GPL-2.0-or-later
"""Parsing and lookup of the HPLIP model database (models.dat)."""

from __future__ import annotations

import configparser
import re

from hpeasy.models import HplipInfo
from hpeasy.runner import Runner

MODELS_DAT = "/usr/share/hplip/data/models/models.dat"

_PREFIX = re.compile(r"^(hewlett[-\s]?packard|hp)(?![a-z0-9])")


def normalize_model(name: str) -> str:
    n = name.lower().strip()
    n = _PREFIX.sub("", n)
    return re.sub(r"[^a-z0-9]+", "_", n).strip("_")


def load(text: str) -> dict[str, dict[str, str]]:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.read_string(text)
    return {section: dict(parser[section]) for section in parser.sections()}


def _candidates(n: str) -> list[str]:
    base = n.removesuffix("_series")
    keys: list[str] = []
    for stem in (n, base, base + "_series"):
        for key in (stem, "hp_" + stem):
            if key not in keys:
                keys.append(key)
    return keys


def lookup(db: dict[str, dict[str, str]], model: str) -> HplipInfo | None:
    for key in _candidates(normalize_model(model)):
        section = db.get(key)
        if section is None:
            continue
        return HplipInfo(
            name=key,
            supported=section.get("support-type", "1") != "0",
            plugin=section.get("plugin", "0") == "1",
            scan=section.get("scan-type", "0") not in ("", "0"),
        )
    return None


def load_from(runner: Runner) -> dict[str, dict[str, str]] | None:
    text = runner.read_file(MODELS_DAT)
    if text is None:
        return None
    try:
        return load(text)
    except configparser.Error:
        return None
