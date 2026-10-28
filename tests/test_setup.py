# SPDX-License-Identifier: GPL-2.0-or-later
import json
from contextlib import nullcontext

import pytest
from conftest import fixture

from hpeasy import setup as setup_mod
from hpeasy.hplipdb import MODELS_DAT
from hpeasy.models import Device
from hpeasy.plugin import HPLIP_STATE
from hpeasy.runner import FakeRunner, Result
from hpeasy.setup import Options, run_auto, run_setup, setup_device, watch
from hpeasy.state import STATE_PATH, Config, State
from hpeasy.ui import AutoUI

DPKG_STATUS = ("dpkg-query", "-W", "-f=${db:Status-Status}")
OFFICEJET_URI = "ipp://192.168.1.50:631/ipp/print"
OFFICEJET_UUID = "1c852a4d-b800-1f08-abcd-5065f3abc123"
OFFICEJET_QUEUE = "HP_OfficeJet_Pro_9010_series"


@pytest.fixture(autouse=True)
def no_real_lock(monkeypatch):
    monkeypatch.setattr(setup_mod, "_locked", lambda: nullcontext())


class InteractiveUI:
    interactive = True

    def __init__(self, confirm_plugin: bool = True):
        self.confirm_plugin = confirm_plugin
        self.messages: list[str] = []

    def info(self, msg):
        self.messages.append(msg)

    def warn(self, msg):
        self.messages.append(msg)

    def confirm(self, question, default=True):
        if "plugin" in question:
            return self.confirm_plugin
        return True

    def choose(self, title, items):
        return list(range(len(items)))


def make_runner(*, models_dat: str | None = None, **kw) -> FakeRunner:
    files = {MODELS_DAT: models_dat} if models_dat is not None else {}
    runner = FakeRunner(files=files, **kw)
    runner.on(*DPKG_STATUS, out="installed")
    runner.on("lpinfo", "-m", out=fixture("lpinfo_m.txt"))
    return runner


def officejet(**kw) -> Device:
    base = {
        "model": "OfficeJet Pro 9010 series",
        "connection": "network",
        "uris": [OFFICEJET_URI],
        "uuid": OFFICEJET_UUID,
        "ip": "192.168.1.50",
        "ipp_everywhere": True,
    }
    base.update(kw)
    return Device(**base)


def m404() -> Device:
    return Device(
        model="LaserJet Pro M404",
        connection="usb",
        uris=[
            "usb://HP/LaserJet%20Pro%20M404?serial=PHB1234567",
            "hp:/usb/HP_LaserJet_Pro_M404?serial=PHB1234567",
        ],
        serial="PHB1234567",
    )


def p1102() -> Device:
    return Device(
        model="LaserJet Professional P1102",
        connection="usb",
        uris=["hp:/usb/HP_LaserJet_Professional_P1102?serial=X1"],
        serial="X1",
    )


def setup(runner, device, *, config=None, state=None, ui=None, opts=None):
    state = state if state is not None else State()
    outcome = setup_device(
        runner, device, opts or Options(), config or Config(), state, ui or AutoUI()
    )
    return outcome, state


def lpadmin_creates(runner) -> list[list[str]]:
    return [c for c in runner.calls if c[:2] == ["lpadmin", "-p"]]


def test_setup_driverless_creates_queue():
    runner = make_runner()
    outcome, _ = setup(runner, officejet())
    assert outcome.status == "created"
    assert outcome.queue == OFFICEJET_QUEUE
    assert [
        "lpadmin", "-p", OFFICEJET_QUEUE, "-E", "-v", OFFICEJET_URI,
        "-m", "everywhere", "-o", "printer-is-shared=false",
    ] in runner.calls  # fmt: skip
    assert OFFICEJET_QUEUE in json.loads(runner.files[STATE_PATH])["queues"]
    assert not any(c[0] == "apt-get" for c in runner.calls)


def test_setup_is_idempotent():
    runner = make_runner()
    runner.on(
        "lpstat", "-v",
        out="device for HP_X: dnssd://HP%20OfficeJet._ipp._tcp.local/?uuid=1C852A4D-B800-1F08-ABCD-5065F3ABC123\n",
    )  # fmt: skip
    outcome, _ = setup(runner, officejet())
    assert outcome.status == "exists"
    assert outcome.queue == "HP_X"
    assert not lpadmin_creates(runner)


def test_setup_force_reuses_existing_queue_name():
    runner = make_runner()
    runner.on("lpstat", "-v", out=f"device for HP_X: {OFFICEJET_URI}\n")
    outcome, _ = setup(runner, officejet(), opts=Options(force=True))
    assert outcome.status == "created"
    assert outcome.queue == "HP_X"


def test_setup_hplip_usb_resolves_ppd():
    runner = make_runner(models_dat=fixture("models.dat"))
    outcome, _ = setup(runner, m404())
    assert outcome.status == "created"
    assert lpadmin_creates(runner)[0][7] == "drv:///hpcups.drv/hp-laserjet_pro_m404-m405.ppd"


def test_setup_hplip_usb_finds_uri_when_missing():
    runner = make_runner(models_dat=fixture("models.dat"))
    runner.on(
        "lpinfo", "-v",
        out="direct usb://HP/x\ndirect hp:/usb/HP_LaserJet_Pro_M404?serial=PHB1234567\n",
    )  # fmt: skip
    device = m404()
    device.uris = ["usb://HP/LaserJet%20Pro%20M404?serial=PHB1234567"]
    outcome, _ = setup(runner, device)
    assert outcome.status == "created"
    assert lpadmin_creates(runner)[0][5] == "hp:/usb/HP_LaserJet_Pro_M404?serial=PHB1234567"


def test_setup_sets_default_when_none():
    runner = make_runner()
    runner.on("lpstat", "-d", out="no system default destination\n")
    outcome, _ = setup(runner, officejet())
    assert ["lpadmin", "-d", outcome.queue] in runner.calls

    runner = make_runner()
    runner.on("lpstat", "-d", out="system default destination: Other\n")
    setup(runner, officejet())
    assert not any(c[:2] == ["lpadmin", "-d"] for c in runner.calls)


def test_setup_plugin_auto_without_consent():
    runner = make_runner(models_dat=fixture("models.dat"))
    outcome, state = setup(runner, p1102())
    assert outcome.status == "needs-plugin"
    assert outcome.message == "run: sudo hpeasy plugin"
    assert not any(c[0] == "hp-plugin" for c in runner.calls)
    assert state.pending_plugin == ["LaserJet Professional P1102"]
    assert not lpadmin_creates(runner)
    saved = json.loads(runner.files[STATE_PATH])
    assert saved["pending_plugin"] == ["LaserJet Professional P1102"]


def test_setup_plugin_auto_with_consent():
    class PluginRunner(FakeRunner):
        def run(self, argv, **kwargs):
            res = super().run(argv, **kwargs)
            if argv[0] == "hp-plugin":
                self.files[HPLIP_STATE] = "[plugin]\ninstalled=1\nversion=3.23.12\n"
            return res

    runner = PluginRunner(files={MODELS_DAT: fixture("models.dat")})
    runner.on(*DPKG_STATUS, out="installed")
    runner.on("dpkg-query", "-W", "-f=${Version}", "hplip", out="3.23.12+dfsg0-0ubuntu5")
    runner.on("lpinfo", "-m", out=fixture("lpinfo_m.txt"))
    state = State(pending_plugin=["LaserJet Professional P1102"])
    outcome, state = setup(
        runner, p1102(), config=Config(accept_hp_plugin_license=True), state=state
    )
    assert outcome.status == "created"
    assert "d\ny\n" in runner.inputs
    assert ["hp-plugin", "-i"] in runner.calls
    assert state.pending_plugin == []


def test_setup_plugin_interactive_declined():
    runner = make_runner(models_dat=fixture("models.dat"))
    ui = InteractiveUI(confirm_plugin=False)
    outcome, _ = setup(runner, p1102(), ui=ui)
    assert outcome.status == "needs-plugin"
    assert any("proprietary" in m for m in ui.messages)
    assert not runner.interactive_calls


def test_setup_installs_missing_packages_non_interactive():
    device = officejet(escl=True)
    runner = make_runner()
    runner.on(*DPKG_STATUS, "sane-airscan", code=1)
    outcome, _ = setup(runner, device)
    assert ["apt-get", "install", "-y", "sane-airscan"] in runner.calls
    assert outcome.status == "created"

    runner = make_runner()
    runner.on(*DPKG_STATUS, "sane-airscan", code=1)
    outcome, _ = setup(runner, device, config=Config(install_packages=False))
    assert outcome.status == "failed"
    assert "sane-airscan" in outcome.message
    assert not any(c[0] == "apt-get" for c in runner.calls)


def test_setup_apt_failure_is_a_failed_outcome():
    runner = make_runner()
    runner.on(*DPKG_STATUS, "sane-airscan", code=1)
    runner.on("apt-get", "install", code=100, err="E: Could not resolve 'archive.ubuntu.com'")
    outcome, _ = setup(runner, officejet(escl=True))
    assert outcome.status == "failed"
    assert "archive.ubuntu.com" in outcome.message
    assert not lpadmin_creates(runner)


def test_setup_unsupported():
    runner = make_runner(models_dat=fixture("models.dat"))
    device = Device(model="Mystery Writer 5000", connection="usb", uris=["usb://HP/x"])
    outcome, _ = setup(runner, device)
    assert outcome.status == "unsupported"
    assert outcome.message
    assert not lpadmin_creates(runner)


def test_setup_hpmakeuri_for_network_hplip():
    db = fixture("models.dat") + "\n[laserjet_p2055dn]\nsupport-type=2\nplugin=0\nscan-type=0\n"
    runner = make_runner(models_dat=db)
    runner.on(
        "lpinfo", "-m",
        out=fixture("lpinfo_m.txt")
        + "drv:///hpcups.drv/hp-laserjet_p2055dn.ppd HP LaserJet P2055dn, hpcups 3.23.12\n",
    )  # fmt: skip
    runner.on(
        "hp-makeuri", "-c", "192.168.1.60",
        out="CUPS URI: hp:/net/HP_LaserJet_P2055dn?ip=192.168.1.60\n",
    )  # fmt: skip
    device = Device(model="LaserJet P2055dn", connection="network", ip="192.168.1.60")
    outcome, _ = setup(runner, device)
    assert outcome.status == "created"
    assert ["hp-makeuri", "-c", "192.168.1.60"] in runner.calls
    assert lpadmin_creates(runner)[0][5] == "hp:/net/HP_LaserJet_P2055dn?ip=192.168.1.60"


def test_setup_command_failures_become_outcomes():
    runner = make_runner()
    runner.on("lpadmin", "-p", code=1, err="lpadmin: Bad device-uri")
    outcome, state = setup(runner, officejet())
    assert outcome.status == "failed"
    assert "Bad device-uri" in outcome.message
    assert state.queues == {}

    runner = make_runner(binaries={"dpkg-query"})
    outcome, _ = setup(runner, officejet())
    assert outcome.status == "failed"
    assert "lpstat" in outcome.message


def test_setup_enables_hpaio_and_finds_scanner():
    runner = make_runner(models_dat=fixture("models.dat"))
    runner.on(
        "scanimage", "-L",
        out="device `hpaio:/net/officejet_pro_8600?ip=10.0.0.5' is a Hewlett-Packard Officejet_Pro_8600 all-in-one\n",
    )  # fmt: skip
    device = Device(
        model="Officejet Pro 8600",
        connection="network",
        ip="10.0.0.5",
        uris=["hp:/net/Officejet_Pro_8600?ip=10.0.0.5"],
    )
    outcome, _ = setup(runner, device)
    assert outcome.status == "created"
    assert runner.files["/etc/sane.d/dll.d/hpeasy"] == "hpaio\n"
    assert outcome.scanner == "hpaio:/net/officejet_pro_8600?ip=10.0.0.5"


def test_test_page_only_interactive():
    runner = make_runner()
    setup(runner, officejet(), ui=InteractiveUI())
    assert ["lp", "-d", OFFICEJET_QUEUE, setup_mod.TEST_PAGE] in runner.calls

    runner = make_runner()
    setup(runner, officejet(), ui=AutoUI())
    assert not any(c[0] == "lp" for c in runner.calls)

    runner = make_runner()
    setup(runner, officejet(), ui=InteractiveUI(), opts=Options(test_page=False))
    assert not any(c[0] == "lp" for c in runner.calls)


def test_run_setup_with_uri_and_no_device():
    runner = make_runner()
    runner.on("ipptool", out=fixture("ipptool.txt"))
    outcomes = run_setup(runner, Options(uri=OFFICEJET_URI), Config(), AutoUI())
    assert [o.status for o in outcomes] == ["created"]

    assert run_setup(make_runner(), Options(), Config(), AutoUI()) == []
    assert run_setup(make_runner(), Options(uri="bogus://x"), Config(), AutoUI()) == []


def test_setup_usb_everywhere_without_ipp_uri_installs_hplip():
    runner = make_runner()
    runner.on(*DPKG_STATUS, "hplip", code=1)
    device = m404()
    device.ipp_everywhere = True  # IPP-over-USB capable, but no ipp-usb endpoint known
    setup(runner, device)
    assert ["apt-get", "install", "-y", "hplip"] in runner.calls


def test_run_auto_waits_for_ipp_usb_endpoint():
    runner = make_runner(models_dat=fixture("models.dat"))
    runner.on("lpinfo", "-l", "-v", out=fixture("lpinfo_usb.txt"))
    runner.on_seq(
        "avahi-browse",
        results=[Result(0), Result(0, fixture("avahi.txt"))],
    )
    outcomes = run_auto(runner, Config(), usb_only=True)
    assert runner.slept == [2]
    assert [o.status for o in outcomes] == ["created"]
    assert outcomes[0].plan.uri == "ipp://localhost:60000/ipp/print"
    assert outcomes[0].plan.ppd == "everywhere"


def test_run_auto_retries_until_device():
    runner = make_runner(models_dat=fixture("models.dat"))
    runner.on(*DPKG_STATUS, "ipp-usb", code=1)  # no ipp-usb: nothing else to wait for
    runner.on_seq(
        "lpinfo", "-l", "-v",
        results=[Result(0), Result(0), Result(0, fixture("lpinfo_usb.txt"))],
    )  # fmt: skip
    outcomes = run_auto(runner, Config(), usb_only=True)
    assert runner.slept == [2, 4]
    assert len(outcomes) == 1
    assert outcomes[0].status == "created"


def test_run_auto_gives_up_after_six_tries():
    runner = make_runner()
    assert run_auto(runner, Config(), usb_only=True) == []
    assert runner.slept == [2, 4, 8, 16, 30]


def test_run_auto_respects_config_usb_off():
    runner = make_runner(models_dat=fixture("models.dat"))
    runner.on("lpinfo", "-l", "-v", out=fixture("lpinfo_usb.txt"))
    assert run_auto(runner, Config(usb=False), usb_only=True) == []
    assert not lpadmin_creates(runner)
    assert runner.slept == []


def test_run_auto_network_off_ignores_network_devices():
    runner = make_runner()
    runner.on("avahi-browse", out=fixture("avahi.txt"))
    assert run_auto(runner, Config(network="off"), usb_only=False, network_only=True) == []
    assert not lpadmin_creates(runner)


def test_watch_triggers_once_per_device():
    lines = fixture("avahi.txt").splitlines()
    ipv4 = next(ln for ln in lines if ln.startswith("=;eth0;IPv4") and "_ipp._tcp" in ln)
    uscan = next(ln for ln in lines if "_uscan._tcp" in ln)
    runner = make_runner()
    runner.on("avahi-browse", "-a", "-r", "-p", "-t", out=fixture("avahi.txt"))
    runner.stream_lines[("avahi-browse", "-a", "-r", "-p", "-k")] = [
        "+;eth0;IPv4;ignored;_ipp._tcp;local",
        ipv4,
        ipv4,
        uscan,
    ]
    watch(runner, Config())
    assert len(lpadmin_creates(runner)) == 1
    assert runner.slept == [5]
