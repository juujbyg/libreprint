# SPDX-License-Identifier: GPL-2.0-or-later
"""SANE scanner backends: hpaio enablement and scanner lookup."""

from __future__ import annotations

import re

from hpeasy.hplipdb import normalize_model
from hpeasy.runner import Runner

DLL_CONF = "/etc/sane.d/dll.conf"
DLL_D = "/etc/sane.d/dll.d"

_SCANNER_LINE = re.compile(r"^device [`'](.+?)' is a ")


def _has_hpaio(text: str | None) -> bool:
    return text is not None and any(line.strip() == "hpaio" for line in text.splitlines())


def hpaio_enabled(runner: Runner) -> bool:
    if _has_hpaio(runner.read_file(DLL_CONF)):
        return True
    return any(_has_hpaio(runner.read_file(f"{DLL_D}/{name}")) for name in runner.listdir(DLL_D))


def enable_hpaio(runner: Runner) -> None:
    runner.write_file(f"{DLL_D}/hpeasy", "hpaio\n")


def list_scanners(runner: Runner) -> list[str]:
    res = runner.run(["scanimage", "-L"], timeout=60)
    names: list[str] = []
    for line in res.out.splitlines():
        m = _SCANNER_LINE.match(line.strip())
        if m:
            names.append(m.group(1))
    return names


def scanner_for(scanners: list[str], model: str) -> str | None:
    wanted = normalize_model(model)
    needles = {wanted, wanted.removesuffix("_series")} - {""}
    for scanner in scanners:
        haystack = "_" + normalize_model(scanner) + "_"
        if any(f"_{needle}_" in haystack for needle in needles):
            return scanner
    return None
