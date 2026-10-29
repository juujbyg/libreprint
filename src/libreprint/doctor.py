# SPDX-License-Identifier: GPL-2.0-or-later
"""Diagnostics for the common failure modes of printing and scanning on Linux."""

from __future__ import annotations

import json
import re
from dataclasses import asdict

from libreprint import __version__, deps, hplipdb, plugin, scanning
from libreprint.discovery import discover
from libreprint.models import Check, Device
from libreprint.queues import disabled_queues, parse_lpstat_v
from libreprint.runner import Runner
from libreprint.state import load_state

USB_PRINTER_CLASS = re.compile(r"bInterfaceClass\s+7\b")  # in lsusb -v, for any make
SCANNER_PACKAGES = ["sane-airscan", "libsane-hpaio"]


def _apt_install(*packages: str) -> tuple[str, tuple[str, ...]]:
    return (
        "sudo apt-get install " + " ".join(packages),
        ("apt-get", "install", "-y", *packages),
    )


def _service(runner: Runner, check_id: str, unit: str) -> Check:
    if not runner.which("systemctl"):
        return Check(check_id, "skip", f"systemctl not available; cannot check {unit}")
    if runner.run(["systemctl", "is-active", unit]).out.strip() == "active":
        return Check(check_id, "ok", f"{unit} is running")
    return Check(
        check_id,
        "fail",
        f"{unit} is not running",
        fix=f"sudo systemctl enable --now {unit}",
        fix_argv=("systemctl", "enable", "--now", unit),
    )


def _package(runner: Runner, check_id: str, package: str, why: str) -> Check:
    if not runner.which("dpkg-query"):
        return Check(check_id, "skip", f"dpkg-query not available; cannot check {package}")
    if deps.is_installed(runner, package):
        return Check(check_id, "ok", f"{package} is installed")
    fix, argv = _apt_install(package)
    return Check(check_id, "fail", f"{package} is not installed ({why})", fix=fix, fix_argv=argv)


def _check_ipp_usb(runner: Runner, devices: list[Device]) -> Check:
    has_usb = any(d.connection == "usb" for d in devices)
    if not has_usb and runner.which("lsusb"):
        has_usb = USB_PRINTER_CLASS.search(runner.run(["lsusb", "-v"]).out) is not None
    if not has_usb:
        return Check("ipp-usb", "skip", "no USB printer attached")
    return _package(runner, "ipp-usb", "ipp-usb", "needed for driverless USB printing")


def _check_firewall(runner: Runner) -> Check:
    if not runner.which("ufw"):
        return Check("firewall-mdns", "skip", "ufw is not installed")
    res = runner.run(["ufw", "status"])
    if not res.ok:
        return Check("firewall-mdns", "skip", "cannot read ufw status (needs root)")
    if "Status: active" not in res.out:
        return Check("firewall-mdns", "ok", "ufw is inactive")
    if any("5353" in line for line in res.out.splitlines()):
        return Check("firewall-mdns", "ok", "ufw allows mDNS (5353/udp)")
    return Check(
        "firewall-mdns",
        "fail",
        "ufw is active and does not allow mDNS (5353/udp); network printers will not be found",
        fix="sudo ufw allow 5353/udp",
        fix_argv=("ufw", "allow", "5353/udp"),
    )


def _check_queues(runner: Runner) -> list[Check]:
    if not runner.which("lpstat"):
        return [
            Check("queues-enabled", "skip", "lpstat not available (install cups-client)"),
            Check("queues-duplicate", "skip", "lpstat not available (install cups-client)"),
        ]
    checks: list[Check] = []
    disabled = disabled_queues(runner.run(["lpstat", "-p"]).out)
    if disabled:
        checks.extend(
            Check(
                f"queue-enabled:{name}",
                "fail",
                f"queue {name} is disabled",
                fix=f"sudo cupsenable {name}",
                fix_argv=("cupsenable", name),
            )
            for name in disabled
        )
    else:
        checks.append(Check("queues-enabled", "ok", "no queue is disabled"))

    by_uri: dict[str, list[str]] = {}
    for queue in parse_lpstat_v(runner.run(["lpstat", "-v"]).out):
        by_uri.setdefault(queue.uri, []).append(queue.name)
    dupes = {uri: names for uri, names in by_uri.items() if len(names) > 1}
    if dupes:
        detail = "; ".join(f"{', '.join(names)} -> {uri}" for uri, names in dupes.items())
        checks.append(
            Check(
                "queues-duplicate",
                "warn",
                f"several queues point to the same device ({detail}); remove the extras "
                "with: lpadmin -x NAME",
            )
        )
    else:
        checks.append(Check("queues-duplicate", "ok", "no duplicate queues"))
    return checks


def _check_plugin(runner: Runner) -> Check:
    pending = load_state(runner).pending_plugin
    if pending:
        return Check(
            "hp-plugin",
            "fail",
            f"the HP plugin is required for: {', '.join(pending)}",
            fix="sudo libreprint plugin",
        )
    have, want = plugin.plugin_version(runner), plugin.hplip_version(runner)
    if have is not None and want is not None and have != want:
        return Check(
            "hp-plugin",
            "fail",
            f"HP plugin version {have} does not match HPLIP {want}",
            fix="sudo libreprint plugin",
        )
    return Check("hp-plugin", "ok", "no HP plugin problem detected")


def _check_hplip_model(runner: Runner, devices: list[Device]) -> Check:
    no_driver = [d.display_name for d in devices if not d.is_hp and not d.ipp_everywhere]
    if no_driver:
        return Check(
            "hplip-model",
            "warn",
            "no driverless (IPP Everywhere) support, install the manufacturer's Linux driver: "
            + ", ".join(no_driver),
        )
    db = hplipdb.load_from(runner)
    if db is None:
        return Check("hplip-model", "skip", "HPLIP model database not found (hplip not installed)")
    unknown = [
        d.display_name
        for d in devices
        if not d.ipp_everywhere and hplipdb.lookup(db, d.model) is None
    ]
    if not unknown:
        return Check("hplip-model", "ok", "all detected models are known to HPLIP or driverless")
    version = plugin.hplip_version(runner) or "unknown version"
    return Check(
        "hplip-model",
        "warn",
        f"not in the installed HPLIP database (HPLIP {version}): {', '.join(unknown)}",
    )


def _check_scanner(runner: Runner, devices: list[Device]) -> Check:
    db = hplipdb.load_from(runner)

    def scans(device: Device) -> bool:
        info = hplipdb.lookup(db, device.model) if db and device.is_hp else None
        return device.escl or (info is not None and info.scan)

    if not any(scans(d) for d in devices):
        return Check("scanner", "skip", "no scan-capable device detected")
    if not runner.which("scanimage"):
        return Check("scanner", "skip", "scanimage not available (install sane-utils)")
    if scanning.list_scanners(runner):
        return Check("scanner", "ok", "scanimage sees at least one scanner")
    fix, argv = _apt_install(*SCANNER_PACKAGES)
    return Check(
        "scanner",
        "warn",
        "scanimage -L lists no scanner although a scan-capable device was detected",
        fix=fix,
        fix_argv=argv,
    )


def _check_groups(runner: Runner) -> Check:
    if not runner.which("id"):
        return Check("user-groups", "skip", "id not available")
    groups = runner.run(["id", "-nG"]).out.split()
    if "lpadmin" in groups:
        return Check("user-groups", "ok", "current user is in the lpadmin group")
    return Check(
        "user-groups",
        "warn",
        "current user is not in the lpadmin group (cannot administer printers without sudo)",
        fix="sudo usermod -aG lpadmin $USER",
    )


def run_checks(runner: Runner, devices: list[Device] | None = None) -> list[Check]:
    if devices is None:
        devices = discover(runner)
    checks: list[Check] = [
        _service(runner, "cups-service", "cups"),
        _service(runner, "avahi-service", "avahi-daemon"),
        _package(runner, "nss-mdns", "libnss-mdns", "needed to resolve .local printer names"),
        _check_ipp_usb(runner, devices),
        _check_firewall(runner),
        *_check_queues(runner),
        _check_plugin(runner),
        _check_hplip_model(runner, devices),
        _check_scanner(runner, devices),
        _check_groups(runner),
    ]
    return checks


def apply_fixes(runner: Runner, checks: list[Check]) -> list[Check]:
    """Run ``fix_argv`` of failing checks (and warnings that carry one), then re-check."""
    for check in checks:
        if check.status in ("fail", "warn") and check.fix_argv:
            runner.run(list(check.fix_argv), timeout=900)
    return run_checks(runner)


def to_json(checks: list[Check], devices: list[Device], hplip: str | None = None) -> str:
    """Serialize a report; ``hplip`` is the installed HPLIP version, when known."""
    return json.dumps(
        {
            "version": __version__,
            "hplip": hplip,
            "checks": [asdict(c) for c in checks],
            "devices": [asdict(d) for d in devices],
        },
        indent=2,
    )
