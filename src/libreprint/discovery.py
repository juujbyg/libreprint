# SPDX-License-Identifier: GPL-2.0-or-later
"""Find printers and scanners via lpinfo (USB), avahi-browse (network) and ipptool."""

from __future__ import annotations

import dataclasses
import re
from urllib.parse import parse_qs, unquote, urlsplit

from libreprint.hplipdb import normalize_model
from libreprint.models import Device
from libreprint.runner import Runner

_HP_PREFIX = re.compile(r"^(hewlett[- ]?packard|hp)(?:\s+|$)", re.IGNORECASE)
# Manufacturer prefixes recognised in model names, in the spelling shown to users.
_MAKES = (
    "Brother", "Canon", "Dell", "Epson", "Fuji Xerox", "FUJIFILM", "Konica Minolta", "Kyocera",
    "Lexmark", "OKI", "Pantum", "Ricoh", "Samsung", "Sharp", "Toshiba", "Xerox",
)  # fmt: skip
_TRAILING_BRACKET = re.compile(r"\s*\[[^\]]*\]\s*$")
_TXT_ITEM = re.compile(r'"((?:[^"\\]|\\.)*)"')
_ESCAPE = re.compile(r"\\(\d{3})")
_IPP_ATTR = re.compile(r"^\s*([\w.-]+) \([^)]*\) = (.*)$")
_RASTER_FORMATS = ("image/pwg-raster", "image/urf")


def split_make(name: str, mfg: str = "") -> tuple[str, str]:
    """Split "HP ENVY 6000 series" into ``("HP", "ENVY 6000 series")``.

    ``mfg`` is a manufacturer reported separately (USB device ID, mDNS ``usb_MFG``); it is used
    when the name itself does not start with a known manufacturer.
    """
    name = name.strip()
    mfg = mfg.strip()
    if _HP_PREFIX.match(name) or _HP_PREFIX.fullmatch(mfg):
        return "HP", _HP_PREFIX.sub("", name).strip()
    for make in (*_MAKES, mfg):
        if make and name.lower().startswith(make.lower()):
            rest = name[len(make) :]
            if not rest or not rest[0].isalnum():
                return (make if make in _MAKES else mfg), rest.strip(" -")
    return mfg, name


def _unescape(text: str) -> str:
    return _ESCAPE.sub(lambda m: chr(int(m.group(1))), text)


# --- lpinfo -----------------------------------------------------------------


def _parse_device_id(value: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for part in value.split(";"):
        key, sep, val = part.partition(":")
        if sep:
            fields[key.strip().upper()] = val.strip()
    return fields


def _lpinfo_blocks(out: str) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in out.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("Device:"):
            current = {}
            blocks.append(current)
            line = line[len("Device:") :].strip()
        if current is None:
            continue
        key, sep, val = line.partition("=")
        if sep:
            current[key.strip()] = val.strip()
    return blocks


def parse_lpinfo(out: str) -> list[Device]:
    devices: list[Device] = []
    for block in _lpinfo_blocks(out):
        uri = block.get("uri", "")
        if not uri.startswith(("usb://", "hp:/usb/")):
            continue  # implicitclass://, cups-brf:, dnssd:// and others are not handled here
        did = _parse_device_id(block.get("device-id", ""))
        mfg = "HP" if uri.startswith("hp:") else did.get("MFG", "")
        make, model = split_make(block.get("make-and-model", ""), mfg)
        if did.get("MDL"):
            model = split_make(did["MDL"], make)[1]
        if not model or model.lower() == "unknown":
            continue
        query = parse_qs(urlsplit(uri).query)
        serial = (query.get("serial") or [did.get("SN") or None])[0]
        cmds = [c.strip().upper() for c in did.get("CMD", "").split(",") if c.strip()]
        everywhere = any(c == "URF" or c.startswith("PWG") for c in cmds)
        devices.append(
            Device(
                model=model,
                connection="usb",
                uris=[uri],
                serial=serial,
                ipp_everywhere=everywhere,
                make=make,
            )
        )
    return devices


# --- avahi ------------------------------------------------------------------


def _parse_txt(raw: str) -> dict[str, str]:
    txt: dict[str, str] = {}
    for item in _TXT_ITEM.findall(raw):
        key, _, val = item.partition("=")
        txt[key.strip().lower()] = _unescape(val)
    return txt


def _avahi_make_model(txt: dict[str, str], name: str) -> tuple[str, str]:
    ty = txt.get("ty") or txt.get("product", "").strip("()") or name
    make, model = split_make(_TRAILING_BRACKET.sub("", ty), txt.get("usb_mfg", ""))
    if txt.get("usb_mdl"):
        model = split_make(txt["usb_mdl"], make)[1]
    return make, model


def parse_avahi(out: str) -> list[Device]:
    devices: list[Device] = []
    for line in out.splitlines():
        if not line.startswith("="):
            continue
        parts = line.split(";", 9)
        if len(parts) < 10:
            continue
        _, iface, _proto, raw_name, svc, _domain, hostname, address, port, raw_txt = parts
        txt = _parse_txt(raw_txt)
        if "printer-type" in txt:
            continue  # a queue shared by a CUPS server (maybe this one), not a device
        make, model = _avahi_make_model(txt, _unescape(raw_name))
        if not model:
            continue
        is_lo = iface == "lo"
        uuid = txt.get("uuid", "").strip().lower() or None
        dev = Device(
            model=model,
            connection="usb" if is_lo else "network",
            uuid=uuid,
            ip=None if is_lo else address,
            make=make,
        )
        if svc in ("_ipp._tcp", "_ipps._tcp"):
            scheme = "ipps" if svc == "_ipps._tcp" else "ipp"
            host = "localhost" if is_lo else address
            if ":" in host:
                host = f"[{host}]"
            rp = txt.get("rp", "").lstrip("/") or "ipp/print"
            dev.uris = [f"{scheme}://{host}:{port}/{rp}"]
            if not is_lo and hostname.endswith(".local"):
                # queues may have been created with the mDNS name instead of the address
                dev.uris.append(f"{scheme}://{hostname}:{port}/{rp}")
            pdl = txt.get("pdl", "").lower()
            dev.ipp_everywhere = any(fmt in pdl for fmt in _RASTER_FORMATS)
        elif svc == "_uscan._tcp":
            dev.escl = True
        elif svc == "_pdl-datastream._tcp":
            pass
        else:
            continue
        devices.append(dev)
    return devices


# --- ipptool ----------------------------------------------------------------


def ipp_attributes(out: str) -> dict[str, str]:
    """Map attribute name to raw value from ``ipptool -tv`` output (first occurrence wins)."""
    attrs: dict[str, str] = {}
    for line in out.splitlines():
        m = _IPP_ATTR.match(line)
        if m:
            attrs.setdefault(m.group(1), m.group(2).strip())
    return attrs


def parse_ipptool(out: str, uri: str) -> Device | None:
    attrs = ipp_attributes(out)
    make_model = attrs.get("printer-make-and-model")
    if not make_model or "printer-type" in attrs:
        return None  # printer-type is only reported by CUPS queues, not by devices
    uuid = attrs.get("printer-uuid", "")
    uuid = uuid.lower().removeprefix("urn:uuid:") or None
    formats = attrs.get("document-format-supported", "").lower()
    host = urlsplit(uri).hostname or ""
    ip = host if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host) else None
    make, model = split_make(make_model)
    return Device(
        model=model,
        make=make,
        connection="network",
        uris=[uri],
        uuid=uuid,
        ip=ip,
        ipp_everywhere=any(fmt in formats for fmt in _RASTER_FORMATS),
    )


# --- merge ------------------------------------------------------------------


def _same_device(a: Device, b: Device) -> bool:
    if a.connection != b.connection:
        return False
    if a.connection == "network":
        if a.uuid and b.uuid:
            return a.uuid == b.uuid
        return bool(a.ip and b.ip and a.ip == b.ip)
    if a.serial and b.serial:
        return a.serial == b.serial
    return normalize_model(a.model) == normalize_model(b.model)


def _pick_ip(a: str | None, b: str | None) -> str | None:
    if a is None:
        return b
    if b is None:
        return a
    if ":" in a and ":" not in b:
        return b
    return a


def _combine(a: Device, b: Device) -> Device:
    uris = list(a.uris)
    uris.extend(u for u in b.uris if u not in uris)
    return dataclasses.replace(
        a,
        uris=uris,
        serial=a.serial or b.serial,
        uuid=a.uuid or b.uuid,
        ip=_pick_ip(a.ip, b.ip),
        ipp_everywhere=a.ipp_everywhere or b.ipp_everywhere,
        escl=a.escl or b.escl,
    )


def merge(devices: list[Device]) -> list[Device]:
    result = [dataclasses.replace(d, uris=list(d.uris)) for d in devices]
    changed = True
    while changed:
        changed = False
        for i in range(len(result)):
            for j in range(i + 1, len(result)):
                if _same_device(result[i], result[j]):
                    result[i] = _combine(result[i], result[j])
                    del result[j]
                    changed = True
                    break
            if changed:
                break
    return result


# --- runner-backed entry points ---------------------------------------------


def parse_airscan(out: str) -> list[tuple[str, str]]:
    """Return ``(model, ip)`` pairs for the eSCL scanners listed by ``airscan-discover``."""
    found: list[tuple[str, str]] = []
    for line in out.splitlines():
        name, sep, rest = line.strip().partition(" = ")
        if not sep or not rest.endswith(", eSCL"):
            continue
        host = urlsplit(rest.split(",")[0].strip()).hostname or ""
        if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host):
            found.append((split_make(_TRAILING_BRACKET.sub("", name))[1], host))
    return found


def _discover_without_avahi(runner: Runner) -> list[Device]:
    """Network discovery through ippfind/ipptool when avahi-browse is not installed."""
    res = runner.run(["ippfind", "-T", "5", "_ipp._tcp", "_ipps._tcp"], timeout=20)
    devices: list[Device] = []
    for uri in dict.fromkeys(line.strip() for line in res.out.splitlines()):
        if not uri.startswith(("ipp://", "ipps://")):
            continue
        out = runner.run(["ipptool", "-T", "10", "-tv", uri, "get-printer-attributes.test"]).out
        dev = parse_ipptool(out, uri)
        if dev is not None:
            devices.append(dev)
    devices = merge(devices)
    scanners = parse_airscan(runner.run(["airscan-discover"], timeout=30).out)
    for dev in devices:
        for model, ip in scanners:
            if normalize_model(model) == normalize_model(dev.model):
                dev.escl = True
                dev.ip = dev.ip or ip
    return devices


def discover(runner: Runner) -> list[Device]:
    found: list[Device] = []
    found.extend(parse_lpinfo(runner.run(["lpinfo", "-l", "-v"], timeout=60).out))
    # -k keeps raw service types (_ipp._tcp); without it avahi prints "Internet Printer"
    avahi = runner.run(["avahi-browse", "-a", "-r", "-p", "-k", "-t"], timeout=15)
    if avahi.code == 127:
        found.extend(_discover_without_avahi(runner))
    else:
        found.extend(parse_avahi(avahi.out))
    return merge(found)


def probe_uri(runner: Runner, uri: str) -> Device | None:
    parts = urlsplit(uri)
    if parts.scheme in ("ipp", "ipps"):
        res = runner.run(["ipptool", "-T", "10", "-tv", uri, "get-printer-attributes.test"])
        return parse_ipptool(res.out, uri)
    if parts.scheme == "hp":
        segments = [s for s in parts.path.split("/") if s]
        if len(segments) < 2 or segments[0] not in ("usb", "net"):
            return None
        model = split_make(unquote(segments[1]).replace("_", " "), "HP")[1]
        if not model:
            return None
        query = parse_qs(parts.query)
        if segments[0] == "usb":
            return Device(
                model=model,
                connection="usb",
                uris=[uri],
                serial=(query.get("serial") or [None])[0],
            )
        return Device(
            model=model,
            connection="network",
            uris=[uri],
            ip=(query.get("ip") or [None])[0],
        )
    return None
