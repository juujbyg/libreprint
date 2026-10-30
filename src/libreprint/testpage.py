# SPDX-License-Identifier: GPL-2.0-or-later
"""LibrePrint's own test page: colour circles plus the printer's identity and media limits."""

from __future__ import annotations

import math
import os
import re
import tempfile
from dataclasses import dataclass
from urllib.parse import urlsplit

from libreprint.discovery import ipp_attributes
from libreprint.queues import Queue
from libreprint.runner import Runner

FONT = "Liberation Mono"
A4 = (210.0, 297.0)
DEFAULT_MARGIN_MM = 5.0
MM = 72 / 25.4
LEFT_MM = 30.0
CONTENT_MM = 150.0
RING_R, FILL_R, HUB_R = 16.6, 15.0, 4.6
CIRCLES = (
    ("C", (0.0, 0.68, 0.94)),
    ("M", (0.93, 0.0, 0.55)),
    ("Y", (1.0, 0.95, 0.0)),
    ("K", (0.14, 0.12, 0.13)),
    ("R", (1.0, 0.0, 0.0)),
    ("G", (0.0, 1.0, 0.0)),
    ("B", (0.0, 0.0, 1.0)),
)
_MEDIA_SIZE = re.compile(r"_(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)(mm|in)$")
_MEDIA_NAME = re.compile(r"^[a-z]+_([a-z0-9-]+)_")
_MARGIN = re.compile(r"media-(top|bottom|left|right)-margin=(\d+)")
_ADAPTER = re.compile(r"<io:Adapter>.*?</io:Adapter>", re.DOTALL)
_SSID = re.compile(r"<wifi:SSID>([^<]+)</wifi:SSID>")
_CONNECTED = "<dd:IsConnected>true</dd:IsConnected>"


@dataclass(frozen=True)
class Margins:
    top: float
    bottom: float
    left: float
    right: float


@dataclass(frozen=True)
class PageInfo:
    printer: str
    model: str
    queue: str
    connection: str
    wifi: str
    address: str
    paper: str
    size_mm: tuple[float, float]
    margins: Margins


def paper_size(keyword: str) -> tuple[str, tuple[float, float]]:
    """Name and size in mm of a PWG media keyword, e.g. ``iso_a4_210x297mm``; A4 if unknown."""
    m = _MEDIA_SIZE.search(keyword)
    if not m:
        return "A4", A4
    scale = 25.4 if m.group(3) == "in" else 1.0
    size = (round(float(m.group(1)) * scale, 1), round(float(m.group(2)) * scale, 1))
    name = _MEDIA_NAME.match(keyword)
    return (name.group(1).replace("-", " ").title() if name else "Custom"), size


def parse_margins(media_col: str) -> Margins:
    """Margins in mm from ``media-col-default``, whose values are hundredths of a millimetre."""
    found = {side: int(value) / 100 for side, value in _MARGIN.findall(media_col)}
    return Margins(
        *(found.get(side, DEFAULT_MARGIN_MM) for side in ("top", "bottom", "left", "right"))
    )


def parse_hp_ssid(xml: str) -> str | None:
    """Wi-Fi name from HP's ``/IoMgmt/Adapters``, whose SSID is usually hex-encoded."""
    for adapter in _ADAPTER.findall(xml):
        m = _SSID.search(adapter)
        if m and _CONNECTED in adapter:
            try:
                return bytes.fromhex(m.group(1)).decode("utf-8", "replace")
            except ValueError:
                return m.group(1)
    return None


def parse_nmcli_ssid(out: str) -> str | None:
    for line in out.splitlines():
        if line.startswith("yes:"):
            return line[len("yes:") :].replace("\\:", ":") or None
    return None


def _wifi(runner: Runner, attrs: dict[str, str], host: str, model: str) -> str:
    if attrs.get("printer-wifi-ssid"):
        return attrs["printer-wifi-ssid"]
    if model.upper().startswith("HP"):
        xml = runner.fetch(f"http://{host}/IoMgmt/Adapters")
        ssid = parse_hp_ssid(xml) if xml else None
        if ssid:
            return ssid
    ssid = parse_nmcli_ssid(runner.run(["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"]).out)
    return f"not reported by the printer (this computer: {ssid})" if ssid else "not reported"


def collect(runner: Runner, queue: Queue) -> PageInfo:
    parts = urlsplit(queue.uri)
    host = parts.hostname or ""
    is_usb = parts.scheme in ("usb", "hp") or host in ("localhost", "127.0.0.1")
    attrs: dict[str, str] = {}
    if parts.scheme in ("ipp", "ipps"):
        res = runner.run(["ipptool", "-T", "10", "-tv", queue.uri, "get-printer-attributes.test"])
        attrs = ipp_attributes(res.out)
    model = attrs.get("printer-make-and-model") or queue.name.replace("_", " ")
    paper, size = paper_size(attrs.get("media-default", ""))
    return PageInfo(
        printer=attrs.get("printer-name") or queue.name,
        model=model,
        queue=queue.name,
        connection="USB" if is_usb else "Network",
        wifi="" if is_usb else _wifi(runner, attrs, host, model),
        address="" if is_usb else host,
        paper=paper,
        size_mm=size,
        margins=parse_margins(attrs.get("media-col-default", "")),
    )


def rows(info: PageInfo) -> list[tuple[str, str]]:
    """The text of the page, as label and value pairs."""
    width, height = info.size_mm
    m = info.margins
    printable = f"{width - m.left - m.right:.1f} x {height - m.top - m.bottom:.1f} mm"
    found = [
        ("Printer", info.printer),
        ("Model", info.model),
        ("Queue", info.queue),
        ("Connection", info.connection),
        ("Wi-Fi", info.wifi),
        ("Address", info.address),
        ("Paper", f"{info.paper} ({width:g} x {height:g} mm)"),
        ("Printable area", printable),
        ("Margins", f"top {m.top:g}, bottom {m.bottom:g}, left {m.left:g}, right {m.right:g} mm"),
    ]
    return [(label, value) for label, value in found if value]


def _circle(ctx, x: float, y: float, radius: float) -> None:
    ctx.new_sub_path()
    ctx.arc(x, y, radius, 0, math.tau)


def _dotted_rule(ctx, x: float, y: float) -> None:
    ctx.set_source_rgb(0.75, 0.75, 0.75)
    for i in range(int(CONTENT_MM)):
        _circle(ctx, x + i, y, 0.09)
        ctx.fill()


def _centred(ctx, text: str, x: float, y: float) -> None:
    extents = ctx.text_extents(text)
    ctx.move_to(x - extents.width / 2 - extents.x_bearing, y + extents.height / 2)
    ctx.show_text(text)


def _colour_circle(ctx, name: str, rgb: tuple[float, float, float], x: float, y: float) -> None:
    ctx.set_source_rgb(*rgb)
    ctx.set_line_width(0.15)
    _circle(ctx, x, y, RING_R)
    ctx.stroke()
    ctx.new_path()
    ctx.move_to(x, y - FILL_R)
    ctx.arc_negative(x, y, FILL_R, -math.pi / 2, math.pi / 2)
    ctx.close_path()
    ctx.fill()
    steps = int(FILL_R)
    for ix in range(1, steps + 1):
        for iy in range(-steps, steps + 1):
            distance = math.hypot(ix, iy)
            if HUB_R + 0.8 < distance < FILL_R:
                _circle(ctx, x + ix, y + iy, 0.09)
                ctx.fill()
    ctx.set_source_rgb(1, 1, 1)
    _circle(ctx, x, y, HUB_R)
    ctx.fill()
    ctx.set_source_rgb(*rgb)
    _centred(ctx, name, x, y)


def _grey_wheel(ctx, x: float, y: float) -> None:
    sectors = 12
    for i in range(sectors):
        grey = i * 0.95 / (sectors - 1)
        ctx.set_source_rgb(grey, grey, grey)
        start = -math.pi / 2 + i * math.tau / sectors
        ctx.new_path()
        ctx.move_to(x, y)
        ctx.arc(x, y, FILL_R, start, start + math.tau / sectors)
        ctx.close_path()
        ctx.fill()
    ctx.set_source_rgb(1, 1, 1)
    _circle(ctx, x, y, HUB_R + 1)
    ctx.fill()
    ctx.set_source_rgb(0.8, 0.8, 0.8)
    ctx.set_line_width(0.15)
    _circle(ctx, x, y, RING_R)
    ctx.stroke()


def render(info: PageInfo, path: str) -> None:
    import cairo

    width, height = info.size_mm
    m = info.margins
    surface = cairo.PDFSurface(path, width * MM, height * MM)
    ctx = cairo.Context(surface)
    ctx.scale(MM, MM)

    # Media limits: this line is the edge of what the printer can reach.
    ctx.set_source_rgb(0, 0, 0)
    ctx.set_line_width(0.1)
    ctx.rectangle(
        m.left + 0.2, m.top + 0.2, width - m.left - m.right - 0.4, height - m.top - m.bottom - 0.4
    )
    ctx.stroke()

    x = LEFT_MM + (width - A4[0]) / 2
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(6)
    ctx.move_to(x, 44)
    ctx.show_text("LibrePrint test page")
    _dotted_rule(ctx, x, 60)

    ctx.set_font_size(4)
    positions = [(x + RING_R + i * 39, y) for y in (82.4, 121.5) for i in range(4)]
    for (name, rgb), (cx, cy) in zip(CIRCLES, positions, strict=False):
        _colour_circle(ctx, name, rgb, cx, cy)
    _grey_wheel(ctx, *positions[-1])
    _dotted_rule(ctx, x, 148)

    y = 160.0
    ctx.set_source_rgb(0, 0, 0)
    ctx.set_font_size(3.5)
    for label, value in rows(info):
        ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.move_to(x, y)
        ctx.show_text(label)
        ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        ctx.move_to(x + 42, y)
        ctx.show_text(value)
        y += 7.5

    _dotted_rule(ctx, x, y + 2)
    ctx.set_source_rgb(0, 0, 0)
    ctx.set_font_size(2.8)
    ctx.move_to(x, y + 10)
    ctx.show_text("The thin outer line marks the printable area.")
    ctx.move_to(x, y + 15)
    ctx.show_text("It should be visible on all four sides.")
    surface.finish()


def create(runner: Runner, queue: Queue) -> str | None:
    """Write the test page to a temporary PDF; ``None`` when pycairo is not installed."""
    try:
        import cairo  # noqa: F401
    except ImportError:
        return None
    info = collect(runner, queue)
    fd, path = tempfile.mkstemp(prefix="libreprint-test-", suffix=".pdf")
    os.close(fd)
    try:
        render(info, path)
    except Exception:
        os.unlink(path)
        raise
    return path
