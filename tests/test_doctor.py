# SPDX-License-Identifier: GPL-2.0-or-later
import json

from conftest import fixture

from hpeasy import __version__, doctor
from hpeasy.hplipdb import MODELS_DAT
from hpeasy.models import Device
from hpeasy.plugin import HPLIP_STATE
from hpeasy.runner import FakeRunner
from hpeasy.state import STATE_PATH

DPKG_STATUS = ("dpkg-query", "-W", "-f=${db:Status-Status}")


def healthy(**kw) -> FakeRunner:
    runner = FakeRunner(**kw)
    runner.on("systemctl", "is-active", out="active\n")
    runner.on(*DPKG_STATUS, out="installed")
    runner.on("id", "-nG", out="user lpadmin sudo\n")
    return runner


def by_id(checks, check_id):
    return next(c for c in checks if c.id == check_id)


def usb_device() -> Device:
    return Device(model="LaserJet Pro M404", connection="usb", serial="S1", ipp_everywhere=True)


def test_all_healthy_has_no_failures():
    checks = doctor.run_checks(healthy(), [])
    assert not [c for c in checks if c.status in ("fail", "warn")]


def test_service_checks():
    runner = healthy()
    runner.on("systemctl", "is-active", "cups", out="inactive\n", code=3)
    check = by_id(doctor.run_checks(runner, []), "cups-service")
    assert check.status == "fail"
    assert check.fix == "sudo systemctl enable --now cups"
    assert check.fix_argv == ("systemctl", "enable", "--now", "cups")
    assert by_id(doctor.run_checks(runner, []), "avahi-service").status == "ok"

    runner.on("systemctl", "is-active", "avahi-daemon", out="failed\n", code=3)
    check = by_id(doctor.run_checks(runner, []), "avahi-service")
    assert check.fix_argv == ("systemctl", "enable", "--now", "avahi-daemon")


def test_nss_mdns():
    runner = healthy()
    assert by_id(doctor.run_checks(runner, []), "nss-mdns").status == "ok"
    runner.on(*DPKG_STATUS, "libnss-mdns", code=1)
    check = by_id(doctor.run_checks(runner, []), "nss-mdns")
    assert check.status == "fail"
    assert check.fix == "sudo apt-get install libnss-mdns"
    assert check.fix_argv == ("apt-get", "install", "-y", "libnss-mdns")


def test_ipp_usb_only_with_hp_usb_device():
    runner = healthy()
    assert by_id(doctor.run_checks(runner, []), "ipp-usb").status == "skip"

    runner.on("lsusb", "-d", "03f0:", out="Bus 001 Device 004: ID 03f0:2a17 HP, Inc\n")
    assert by_id(doctor.run_checks(runner, []), "ipp-usb").status == "ok"

    runner.on(*DPKG_STATUS, "ipp-usb", code=1)
    check = by_id(doctor.run_checks(runner, []), "ipp-usb")
    assert check.status == "fail"
    assert check.fix_argv == ("apt-get", "install", "-y", "ipp-usb")


def test_ipp_usb_uses_discovered_usb_devices_when_lsusb_missing():
    runner = healthy(binaries={"systemctl", "dpkg-query", "id"})
    runner.on(*DPKG_STATUS, "ipp-usb", code=1)
    check = by_id(doctor.run_checks(runner, [usb_device()]), "ipp-usb")
    assert check.status == "fail"


def test_firewall_mdns():
    runner = healthy()
    assert by_id(doctor.run_checks(runner, []), "firewall-mdns").status == "ok"  # ufw inactive

    runner.on("ufw", "status", out="Status: inactive\n")
    assert by_id(doctor.run_checks(runner, []), "firewall-mdns").status == "ok"

    runner.on("ufw", "status", out="Status: active\n\n22/tcp ALLOW Anywhere\n")
    check = by_id(doctor.run_checks(runner, []), "firewall-mdns")
    assert check.status == "fail"
    assert check.fix == "sudo ufw allow 5353/udp"
    assert check.fix_argv == ("ufw", "allow", "5353/udp")

    runner.on("ufw", "status", out="Status: active\n\n5353/udp ALLOW Anywhere\n")
    assert by_id(doctor.run_checks(runner, []), "firewall-mdns").status == "ok"


def test_disabled_queues_one_check_each():
    runner = healthy()
    runner.on(
        "lpstat",
        "-p",
        out=(
            "printer HP_A disabled since Mon 01 Jan 2026 - Paused\n"
            "printer HP_B disabled since Mon 01 Jan 2026 - Paused\n"
            "printer Other disabled since Mon 01 Jan 2026 - Paused\n"
            "printer HP_C is idle.  enabled since Mon 01 Jan 2026\n"
        ),
    )
    checks = doctor.run_checks(runner, [])
    failing = [c for c in checks if c.id.startswith("queue-enabled:")]
    assert [c.id for c in failing] == ["queue-enabled:HP_A", "queue-enabled:HP_B"]
    assert failing[0].fix_argv == ("cupsenable", "HP_A")
    assert all(c.status == "fail" for c in failing)
    assert not any(c.id == "queues-enabled" for c in checks)


def test_queues_enabled_ok_when_none_disabled():
    assert by_id(doctor.run_checks(healthy(), []), "queues-enabled").status == "ok"


def test_duplicate_queues_warn():
    runner = healthy()
    runner.on(
        "lpstat",
        "-v",
        out="device for HP_A: ipp://10.0.0.5/ipp/print\ndevice for HP_A_2: ipp://10.0.0.5/ipp/print\n"
        "device for Other: ipp://10.0.0.9/ipp/print\n",
    )
    check = by_id(doctor.run_checks(runner, []), "queues-duplicate")
    assert check.status == "warn"
    assert "HP_A" in check.message and "HP_A_2" in check.message
    assert check.fix_argv is None


def test_hp_plugin_pending_and_mismatch():
    runner = healthy()
    assert by_id(doctor.run_checks(runner, []), "hp-plugin").status == "ok"

    runner.files[STATE_PATH] = json.dumps({"pending_plugin": ["LaserJet P1102"]})
    check = by_id(doctor.run_checks(runner, []), "hp-plugin")
    assert check.status == "fail"
    assert check.fix == "sudo hpeasy plugin"
    assert check.fix_argv is None

    runner = healthy()
    runner.on("dpkg-query", "-W", "-f=${Version}", "hplip", out="3.23.12+dfsg0-0ubuntu5")
    runner.files[HPLIP_STATE] = "[plugin]\ninstalled=1\nversion=3.22.10\n"
    check = by_id(doctor.run_checks(runner, []), "hp-plugin")
    assert check.status == "fail"
    assert "3.22.10" in check.message and "3.23.12" in check.message

    runner.files[HPLIP_STATE] = "[plugin]\ninstalled=1\nversion=3.23.12\n"
    assert by_id(doctor.run_checks(runner, []), "hp-plugin").status == "ok"


def test_hplip_model_unknown_warns():
    runner = healthy(files={MODELS_DAT: fixture("models.dat")})
    runner.on("dpkg-query", "-W", "-f=${Version}", "hplip", out="3.23.12-1")
    unknown = Device(model="Mystery Writer 5000", connection="usb")
    known = Device(model="LaserJet Pro M404", connection="usb")
    driverless = Device(model="Other 9", connection="network", ipp_everywhere=True)
    check = by_id(doctor.run_checks(runner, [unknown, known, driverless]), "hplip-model")
    assert check.status == "warn"
    assert "Mystery Writer 5000" in check.message
    assert "3.23.12" in check.message
    assert "M404" not in check.message and "Other 9" not in check.message

    assert by_id(doctor.run_checks(runner, [known]), "hplip-model").status == "ok"
    assert by_id(doctor.run_checks(healthy(), [unknown]), "hplip-model").status == "skip"


def test_scanner_check():
    escl = Device(model="OfficeJet Pro 9010 series", connection="network", escl=True)
    runner = healthy()
    check = by_id(doctor.run_checks(runner, [escl]), "scanner")
    assert check.status == "warn"
    assert check.fix == "sudo apt-get install sane-airscan libsane-hpaio"
    assert check.fix_argv == ("apt-get", "install", "-y", "sane-airscan", "libsane-hpaio")

    runner.on("scanimage", "-L", out="device `airscan:e0:x' is a eSCL x ip=1.2.3.4\n")
    assert by_id(doctor.run_checks(runner, [escl]), "scanner").status == "ok"
    assert by_id(doctor.run_checks(runner, []), "scanner").status == "skip"


def test_user_groups():
    runner = healthy()
    assert by_id(doctor.run_checks(runner, []), "user-groups").status == "ok"
    runner.on("id", "-nG", out="user sudo\n")
    check = by_id(doctor.run_checks(runner, []), "user-groups")
    assert check.status == "warn"
    assert check.fix == "sudo usermod -aG lpadmin $USER"
    assert check.fix_argv is None


def test_doctor_without_systemctl():
    runner = FakeRunner(binaries={"lpstat"})
    checks = doctor.run_checks(runner, [])
    assert by_id(checks, "cups-service").status == "skip"
    assert by_id(checks, "avahi-service").status == "skip"
    assert "systemctl" in by_id(checks, "cups-service").message
    assert by_id(checks, "nss-mdns").status == "skip"
    assert by_id(checks, "firewall-mdns").status == "skip"


def test_doctor_in_bare_container_does_not_raise():
    checks = doctor.run_checks(FakeRunner(binaries=set()), [usb_device()])
    assert checks
    assert all(c.status in ("ok", "skip", "warn", "fail") for c in checks)
    assert not [c for c in checks if c.status == "fail"]


def test_apply_fixes_runs_only_failed_fix_argv():
    runner = healthy()
    runner.on("systemctl", "is-active", "cups", out="inactive\n", code=3)
    runner.on(*DPKG_STATUS, "libnss-mdns", code=1)
    runner.on("id", "-nG", out="user sudo\n")  # warn without fix_argv
    checks = doctor.run_checks(runner, [])
    runner.calls.clear()
    doctor.apply_fixes(runner, checks)
    fixes = [c for c in runner.calls if c[:2] in (["systemctl", "enable"], ["apt-get", "install"])]
    assert fixes == [
        ["systemctl", "enable", "--now", "cups"],
        ["apt-get", "install", "-y", "libnss-mdns"],
    ]


def test_apply_fixes_returns_rechecked_list():
    runner = healthy()
    checks = doctor.run_checks(runner, [])
    rerun = doctor.apply_fixes(runner, checks)
    assert [c.id for c in rerun] == [c.id for c in checks]


def test_to_json_valid():
    checks = doctor.run_checks(healthy(), [])
    device = Device(model="LaserJet Pro M404", connection="usb", uris=["usb://HP/x"])
    data = json.loads(doctor.to_json(checks, [device], hplip="3.23.12"))
    assert data["version"] == __version__
    assert data["hplip"] == "3.23.12"
    assert {c["id"] for c in data["checks"]} >= {"cups-service", "user-groups"}
    assert data["devices"][0]["model"] == "LaserJet Pro M404"
