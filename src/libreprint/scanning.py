# SPDX-License-Identifier: GPL-2.0-or-later
"""SANE scanner backends: hpaio enablement and scanner lookup."""

from __future__ import annotations

import re

from libreprint.hplipdb import normalize_model
from libreprint.runner import Runner

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
    runner.write_file(f"{DLL_D}/libreprint", "hpaio\n")


def disable_escl_backend(runner: Runner) -> bool:
    """Comment out sane-backends' ``escl`` in dll.conf; sane-airscan drives the same scanners.

    With both enabled every scanner shows up twice, and some ``escl`` versions dump the
    printer's gzipped web page to stdout during ``scanimage -L``.
    """
    text = runner.read_file(DLL_CONF)
    if text is None or not any(line.strip() == "escl" for line in text.splitlines()):
        return False
    note = "#escl  # disabled by LibrePrint: sane-airscan handles eSCL"
    lines = [note if line.strip() == "escl" else line for line in text.splitlines()]
    runner.write_file(DLL_CONF, "\n".join(lines) + "\n")
    return True


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
