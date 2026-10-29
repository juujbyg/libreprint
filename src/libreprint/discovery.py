# SPDX-License-Identifier: GPL-2.0-or-later
"""Find HP printers via lpinfo (USB), avahi-browse (network) and ipptool."""

from __future__ import annotations

import dataclasses
import re
from urllib.parse import parse_qs, unquote, urlsplit

from libreprint.hplipdb import normalize_model
from libreprint.models import Device
from libreprint.runner import Runner

_HP_NAME = re.compile(r"^(hewlett[- ]?packard|hp)(?![a-z0-9])", re.IGNORECASE)
_HP_PREFIX = re.compile(r"^(hewlett[- ]?packard|hp)\s+", re.IGNORECASE)
_TRAILING_BRACKET = re.compile(r"\s*\[[^\]]*\]\s*$")
_TXT_ITEM = re.compile(r'"((?:[^"\\]|\\.)*)"')
_ESCAPE = re.compile(r"\\(\d{3})")
_IPP_ATTR = re.compile(r"^\s*([\w.-]+) \([^)]*\) = (.*)$")
_RASTER_FORMATS = ("image/pwg-raster", "image/urf")


def _strip_hp(name: str) -> str:
    return _HP_PREFIX.sub("", name.strip()).strip()


def _is_hp_name(name: str) -> bool:
    return bool(_HP_NAME.match(name.strip()))


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
        make_model = block.get("make-and-model", "")
        is_hp = (
            did.get("MFG", "").lower() in ("hp", "hewlett-packard")
            or _is_hp_name(make_model)
            or uri.startswith("hp:")
        )
        if not is_hp:
            continue
        model = did.get("MDL") or _strip_hp(make_model)
        if not model:
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


def _avahi_model(txt: dict[str, str], name: str) -> str:
    if txt.get("usb_mdl"):
        return txt["usb_mdl"].strip()
    ty = txt.get("ty") or txt.get("product", "").strip("()") or name
    return _strip_hp(_TRAILING_BRACKET.sub("", ty))


def _avahi_is_hp(txt: dict[str, str]) -> bool:
    if txt.get("usb_mfg", "").strip().lower() in ("hp", "hewlett-packard"):
        return True
    for key in ("ty", "product"):
        if _is_hp_name(txt.get(key, "").strip("() ")):
            return True
    return False


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
        if not _avahi_is_hp(txt):
            continue
        name = _unescape(raw_name)
        model = _avahi_model(txt, name)
        if not model:
            continue
        is_lo = iface == "lo"
        uuid = txt.get("uuid", "").strip().lower() or None
        dev = Device(
            model=model,
            connection="usb" if is_lo else "network",
            uuid=uuid,
            ip=None if is_lo else address,
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
    if not make_model:
        return None
    uuid = attrs.get("printer-uuid", "")
    uuid = uuid.lower().removeprefix("urn:uuid:") or None
    formats = attrs.get("document-format-supported", "").lower()
    host = urlsplit(uri).hostname or ""
    ip = host if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host) else None
    return Device(
        model=_strip_hp(make_model),
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
    """Return ``(model, ip)`` pairs for HP eSCL scanners listed by ``airscan-discover``."""
    found: list[tuple[str, str]] = []
    for line in out.splitlines():
        name, sep, rest = line.strip().partition(" = ")
        if not sep or not rest.endswith(", eSCL") or not _is_hp_name(name):
            continue
        host = urlsplit(rest.split(",")[0].strip()).hostname or ""
        if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host):
            found.append((_strip_hp(_TRAILING_BRACKET.sub("", name)), host))
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
        if dev is not None and re.search(r"printer-make-and-model \([^)]*\) = (HP|Hewlett)", out):
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
        model = _strip_hp(unquote(segments[1]).replace("_", " "))
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
