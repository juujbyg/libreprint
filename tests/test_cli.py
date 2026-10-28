# SPDX-License-Identifier: GPL-2.0-or-later
import json
import os
import sys
from contextlib import nullcontext
from types import SimpleNamespace

import pytest
from conftest import fixture

from hpeasy import __version__, cli
from hpeasy import setup as setup_mod
from hpeasy.hplipdb import MODELS_DAT
from hpeasy.plugin import HPLIP_STATE
from hpeasy.runner import FakeRunner
from hpeasy.state import STATE_PATH

DPKG_STATUS = ("dpkg-query", "-W", "-f=${db:Status-Status}")
P1102_LPINFO = (
    "Device: uri = hp:/usb/HP_LaserJet_Professional_P1102?serial=X1\n"
    "        class = direct\n"
    "        make-and-model = HP LaserJet Professional P1102\n"
    "        device-id = MFG:HP;MDL:LaserJet Professional P1102;SN:X1;\n"
)


@pytest.fixture(autouse=True)
def no_real_lock(monkeypatch):
    monkeypatch.setattr(setup_mod, "_locked", lambda: nullcontext())


def make_runner(**kw) -> FakeRunner:
    runner = FakeRunner(**kw)
    runner.on(*DPKG_STATUS, out="installed")
    runner.on("lpinfo", "-m", out=fixture("lpinfo_m.txt"))
    return runner


def set_tty(monkeypatch, value: bool) -> None:
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: value, readline=lambda: ""))


def test_version(capsys):
    assert cli.main(["--version"], make_runner(), euid=1000) == 0
    assert __version__ in capsys.readouterr().out


def test_setup_requires_root_non_tty(monkeypatch, capsys):
    set_tty(monkeypatch, False)
    runner = make_runner()
    assert cli.main(["setup"], runner, euid=1000) == 3
    assert "needs root" in capsys.readouterr().err
    assert runner.calls == []


def test_setup_reexecs_with_sudo_on_tty(monkeypatch):
    set_tty(monkeypatch, True)
    seen = []
    monkeypatch.setattr(os, "execvp", lambda f, a: seen.append((f, a)))
    cli.main(["setup", "--yes"], make_runner(), euid=1000)
    assert seen == [("sudo", ["sudo", sys.executable, "-m", "hpeasy", "setup", "--yes"])]


def test_doctor_fix_requires_root(monkeypatch):
    set_tty(monkeypatch, False)
    assert cli.main(["doctor", "--fix"], make_runner(), euid=1000) == 3
    assert cli.main(["doctor", "--json"], make_runner(), euid=1000) != 3


def test_setup_no_devices_exit_4(capsys):
    assert cli.main(["setup", "--yes"], make_runner(), euid=0) == 4
    assert "no HP device" in capsys.readouterr().err


def test_setup_creates_queue_via_uri(capsys):
    runner = make_runner()
    runner.on("ipptool", out=fixture("ipptool.txt"))
    code = cli.main(["setup", "--yes", "--uri", "ipp://192.168.1.50:631/ipp/print"], runner, euid=0)
    out = capsys.readouterr().out
    assert code == 0
    assert "queue HP_" in out
    assert "(driverless)" in out


def test_setup_needs_plugin_exit_5(capsys):
    runner = make_runner(files={MODELS_DAT: fixture("models.dat")})
    runner.on("lpinfo", "-l", "-v", out=P1102_LPINFO)
    assert cli.main(["setup", "--yes"], runner, euid=0) == 5
    assert "needs the HP plugin: run sudo hpeasy plugin" in capsys.readouterr().out


def test_setup_unsupported_exit_1(capsys):
    runner = make_runner(files={MODELS_DAT: fixture("models.dat")})
    runner.on(
        "lpinfo", "-l", "-v",
        out=P1102_LPINFO.replace("Professional P1102", "Mystery 5000"),
    )  # fmt: skip
    assert cli.main(["setup", "--yes"], runner, euid=0) == 1
    assert "HP LaserJet Mystery 5000" in capsys.readouterr().out


def test_ascii_fallback_for_narrow_stdout(monkeypatch):
    monkeypatch.setattr(sys, "stdout", SimpleNamespace(encoding="ascii"))
    assert cli._symbols()["ok"] == "[ok]"
    monkeypatch.setattr(sys, "stdout", SimpleNamespace(encoding="utf-8"))
    assert cli._symbols()["ok"] == "✔"


def test_doctor_json_parses(capsys):
    runner = make_runner()
    runner.on("systemctl", "is-active", out="active\n")
    assert cli.main(["doctor", "--json"], runner, euid=1000) == 0
    data = json.loads(capsys.readouterr().out)
    assert {"version", "hplip", "checks", "devices"} <= set(data)
    assert data["version"] == __version__


def test_doctor_text_and_exit_code(capsys):
    runner = make_runner()
    runner.on("systemctl", "is-active", out="inactive\n", code=3)
    assert cli.main(["doctor"], runner, euid=1000) == 1
    out = capsys.readouterr().out
    assert "[FAIL] cups-service" in out
    assert "  fix: sudo systemctl enable --now cups" in out
    assert "[ OK ]" in out or "[SKIP]" in out


def test_list_json(capsys):
    runner = make_runner()
    runner.on("avahi-browse", out=fixture("avahi.txt"))
    assert cli.main(["list", "--json"], runner, euid=1000) == 0
    data = json.loads(capsys.readouterr().out)
    officejet = next(d for d in data if d["model"] == "OfficeJet Pro 9010 series")
    assert officejet["method"] == "driverless"
    assert officejet["queue"] == "-"


def test_list_table(capsys):
    runner = make_runner()
    runner.on("avahi-browse", out=fixture("avahi.txt"))
    runner.on("lpstat", "-v", out="device for HP_Q: ipp://192.168.1.50:631/ipp/print\n")
    assert cli.main(["list"], runner, euid=1000) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].split() == ["MODEL", "CONNECTION", "METHOD", "QUEUE"]
    assert any("HP OfficeJet Pro 9010 series" in ln and "HP_Q" in ln for ln in lines)


def test_list_empty_json(capsys):
    assert cli.main(["list", "--json"], make_runner(), euid=1000) == 0
    assert json.loads(capsys.readouterr().out) == []


def test_bad_args_exit_2(capsys):
    runner = make_runner()
    assert cli.main(["bogus"], runner, euid=0) == 2
    assert cli.main(["setup", "--nope"], runner, euid=0) == 2
    assert cli.main(["auto"], runner, euid=0) == 2
    assert cli.main([], runner, euid=0) == 2
    assert runner.calls == []


def test_auto_usb_and_all():
    runner = make_runner()
    assert cli.main(["auto", "--usb", "1-2"], runner, euid=0) == 0
    assert runner.slept == [2, 4, 8, 16, 30]
    runner = make_runner(files={MODELS_DAT: fixture("models.dat")})
    runner.on("lpinfo", "-l", "-v", out=fixture("lpinfo_usb.txt"))
    assert cli.main(["auto", "--all"], runner, euid=0) == 0
    assert any(c[:2] == ["lpadmin", "-p"] for c in runner.calls)


def test_watch_returns_when_stream_ends():
    assert cli.main(["watch"], make_runner(), euid=0) == 0


def test_plugin_installs_and_sets_up_pending(capsys):
    class PluginRunner(FakeRunner):
        def run(self, argv, **kwargs):
            res = super().run(argv, **kwargs)
            if argv[0] == "hp-plugin":
                self.files[HPLIP_STATE] = "[plugin]\ninstalled=1\nversion=3.23.12\n"
            return res

    runner = PluginRunner(files={MODELS_DAT: fixture("models.dat")})
    runner.on(*DPKG_STATUS, out="installed")
    runner.on("dpkg-query", "-W", "-f=${Version}", "hplip", out="3.23.12-1")
    runner.on("lpinfo", "-m", out=fixture("lpinfo_m.txt"))
    runner.on("lpinfo", "-l", "-v", out=P1102_LPINFO)
    runner.files[STATE_PATH] = json.dumps({"pending_plugin": ["LaserJet Professional P1102"]})
    assert cli.main(["plugin", "--yes"], runner, euid=0) == 0
    assert ["hp-plugin", "-i"] in runner.calls
    assert any(c[:2] == ["lpadmin", "-p"] for c in runner.calls)
    assert json.loads(runner.files[STATE_PATH])["pending_plugin"] == []
    assert "queue HP_LaserJet_Professional_P1102" in capsys.readouterr().out


def test_plugin_failure_exit_1(capsys):
    runner = make_runner()
    assert cli.main(["plugin", "--yes"], runner, euid=0) == 1
    assert "not installed" in capsys.readouterr().err
