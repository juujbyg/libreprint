# SPDX-License-Identifier: GPL-2.0-or-later
"""CUPS queue helpers: lpstat parsing, naming, de-duplication and PPD matching."""

from __future__ import annotations

import re
from dataclasses import dataclass

from libreprint.hplipdb import normalize_model
from libreprint.models import Device

_LPSTAT_V = re.compile(r"^device for (\S+?): (\S.*)$")
_DISABLED = re.compile(r"^printer (\S+) disabled since")
_PPD_PREFERENCE = ("drv:///hpcups.drv/", "hplip:", "lsb/usr/HP/")


@dataclass(frozen=True)
class Queue:
    name: str
    uri: str


def parse_lpstat_v(out: str) -> list[Queue]:
    found: list[Queue] = []
    for line in out.splitlines():
        m = _LPSTAT_V.match(line.strip())
        if m:
            found.append(Queue(m.group(1), m.group(2).strip()))
    return found


def queue_name(model: str, taken: set[str]) -> str:
    base = ("HP_" + re.sub(r"[^A-Za-z0-9]+", "_", model).strip("_"))[:100]
    if base not in taken:
        return base
    n = 2
    while f"{base}_{n}" in taken:
        n += 1
    return f"{base}_{n}"


def _contains(uri: str, key: str, value: str, tail: str) -> bool:
    return re.search(re.escape(f"{key}={value}") + tail, uri, re.IGNORECASE) is not None


def find_existing(device: Device, queues: list[Queue]) -> Queue | None:
    for queue in queues:
        uri = queue.uri
        if uri in device.uris:
            return queue
        if device.serial and _contains(uri, "serial", device.serial, r"(?![\w-])"):
            return queue
        if device.uuid and _contains(uri, "uuid", device.uuid, r"(?![\w-])"):
            return queue
        if device.ip:
            if _contains(uri, "ip", device.ip, r"(?![\w.])"):
                return queue
            if re.search(r"//" + re.escape(device.ip) + r"(?![\w.])", uri):
                return queue
    return None


def lpadmin_argv(name: str, uri: str, ppd: str) -> list[str]:
    return ["lpadmin", "-p", name, "-E", "-v", uri, "-m", ppd, "-o", "printer-is-shared=false"]


def find_hpcups_ppd(lpinfo_m_out: str, model: str) -> str | None:
    wanted = normalize_model(model)
    needles = {wanted, wanted.removesuffix("_series")} - {""}
    candidates: list[str] = []
    for line in lpinfo_m_out.splitlines():
        name, _, description = line.strip().partition(" ")
        if not name or not description:
            continue
        haystack = "_" + normalize_model(description) + "_"
        if any(f"_{needle}_" in haystack for needle in needles):
            candidates.append(name)
    for prefix in _PPD_PREFERENCE:
        for name in candidates:
            if name.startswith(prefix):
                return name
    return None


def disabled_queues(lpstat_p_out: str) -> list[str]:
    names: list[str] = []
    for line in lpstat_p_out.splitlines():
        m = _DISABLED.match(line)
        if m:
            names.append(m.group(1))
    return names
