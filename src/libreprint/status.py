# SPDX-License-Identifier: GPL-2.0-or-later
"""Printer status, supplies, jobs and print/scan command lines (backend of ``libreprint gui``)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from libreprint.discovery import ipp_attributes
from libreprint.queues import Queue, parse_lpstat_v
from libreprint.runner import Result, Runner

LOW_LEVEL = 10  # percent; below this a supply is shown as low even if the printer disagrees

SIDES = ("one-sided", "two-sided-long-edge", "two-sided-short-edge")
QUALITY = {"draft": "3", "normal": "4", "best": "5"}
SCAN_MODES = ("Color", "Gray")

_JOB_LINE = re.compile(r"^(\S+)-(\d+)\s+(\S+)\s+(\d+)\s+(.*)$")


@dataclass(frozen=True)
class Supply:
    name: str
    level: int  # percent, -1 when unknown
    colors: tuple[str, ...]  # "#RRGGBB" values; several for tri-color cartridges
    low_level: int = 0

    @property
    def low(self) -> bool:
        return 0 <= self.level <= max(self.low_level, LOW_LEVEL)


@dataclass(frozen=True)
class PrinterStatus:
    model: str
    state: str  # "idle" | "processing" | "stopped" | "unknown"
    reasons: tuple[str, ...]
    message: str
    supplies: tuple[Supply, ...]
    firmware: str


@dataclass(frozen=True)
class Job:
    id: str  # "QUEUE-123", as accepted by cancel(1)
    user: str
    size: int
    submitted: str


def _split(value: str) -> list[str]:
    return [v.strip() for v in value.split(",")] if value else []


def _int(value: str, default: int = -1) -> int:
    try:
        return int(value)
    except ValueError:
        return default


def parse_status(out: str) -> PrinterStatus | None:
    attrs = ipp_attributes(out)
    model = attrs.get("printer-make-and-model")
    if not model:
        return None
    names = _split(attrs.get("marker-names", ""))
    levels = _split(attrs.get("marker-levels", ""))
    colors = _split(attrs.get("marker-colors", ""))
    lows = _split(attrs.get("marker-low-levels", ""))
    supplies = tuple(
        Supply(
            name=name,
            level=_int(levels[i]) if i < len(levels) else -1,
            colors=tuple("#" + c for c in colors[i].split("#") if c) if i < len(colors) else (),
            low_level=_int(lows[i], 0) if i < len(lows) else 0,
        )
        for i, name in enumerate(names)
    )
    reasons = tuple(r for r in _split(attrs.get("printer-state-reasons", "")) if r != "none")
    return PrinterStatus(
        model=model,
        state=attrs.get("printer-state", "unknown"),
        reasons=reasons,
        message=attrs.get("printer-state-message", ""),
        supplies=supplies,
        firmware=attrs.get("printer-firmware-string-version", ""),
    )


def fetch_status(runner: Runner, uri: str) -> PrinterStatus | None:
    res = runner.run(["ipptool", "-T", "10", "-tv", uri, "get-printer-attributes.test"], timeout=30)
    return parse_status(res.out)


def printer_queues(lpstat_v_out: str) -> list[Queue]:
    """Queues with a real device URI (cups-browsed ``implicitclass://`` duplicates are skipped)."""
    return [q for q in parse_lpstat_v(lpstat_v_out) if not q.uri.startswith("implicitclass:")]


def parse_jobs(lpstat_o_out: str) -> list[Job]:
    jobs: list[Job] = []
    for line in lpstat_o_out.splitlines():
        m = _JOB_LINE.match(line.strip())
        if m:
            jobs.append(Job(f"{m.group(1)}-{m.group(2)}", m.group(3), int(m.group(4)), m.group(5)))
    return jobs


def web_url(uri: str) -> str | None:
    """The printer's embedded web server, for ``ipp``/``ipps`` queues."""
    parts = urlsplit(uri)
    if parts.scheme not in ("ipp", "ipps") or not parts.hostname:
        return None
    if parts.hostname in ("localhost", "127.0.0.1"):
        return None  # ipp-usb exposes the web server on the same port as IPP
    host = f"[{parts.hostname}]" if ":" in parts.hostname else parts.hostname
    return f"https://{host}/"


def print_argv(
    queue: str,
    path: str,
    *,
    copies: int = 1,
    sides: str = "one-sided",
    color: bool = True,
    quality: str = "normal",
    pages: str = "",
    reverse: bool = True,
) -> list[str]:
    if sides not in SIDES:
        raise ValueError(f"unknown sides value: {sides}")
    argv = ["lp", "-d", queue, "-n", str(max(1, copies)), "-o", f"sides={sides}"]
    argv += ["-o", f"print-color-mode={'color' if color else 'monochrome'}"]
    argv += ["-o", f"print-quality={QUALITY[quality]}"]
    pages = pages.replace(" ", "")
    if pages:
        if not re.fullmatch(r"\d+(-\d+)?(,\d+(-\d+)?)*", pages):
            raise ValueError(f"invalid page range: {pages}")
        argv += ["-o", f"page-ranges={pages}"]
    if reverse:
        # face-up output tray: last page first leaves the stack in reading order
        argv += ["-o", "outputorder=reverse"]
    return [*argv, "--", path]


def scan_argv(
    device: str, out_path: str, *, resolution: int = 300, mode: str = "Color"
) -> list[str]:
    if mode not in SCAN_MODES:
        raise ValueError(f"unknown scan mode: {mode}")
    return [
        "scanimage",
        "-d",
        device,
        "--resolution",
        str(resolution),
        "--mode",
        mode,
        "--format=png",
        "-o",
        out_path,
    ]


def scanner_label(device: str) -> str:
    """Readable name for a SANE device string, e.g. "HP ENVY 6000 series (eSCL)"."""
    backend, _, rest = device.partition(":")
    if backend == "airscan":
        name = rest.partition(":")[2] or rest
        return f"{name.split(' [')[0]} (eSCL)"
    if backend == "hpaio":
        model = rest.lstrip("/").split("/")[1].split("?")[0] if rest.count("/") > 1 else rest
        return f"HP {model.replace('_', ' ').title().replace('Hp ', '')} (HPLIP)"
    return device


def run_scan(runner: Runner, argv: list[str], attempts: int = 3) -> Result:
    """Run ``scanimage``, retrying when opening a network scanner fails transiently."""
    res = Result(1)
    for attempt in range(attempts):
        if attempt:
            runner.sleep(2)
        res = runner.run(argv, timeout=600)
        if res.ok or "open of device" not in res.err:
            break
    return res


def parse_job_id(lp_out: str) -> str | None:
    m = re.search(r"request id is (\S+)", lp_out)
    return m.group(1) if m else None
