# SPDX-License-Identifier: GPL-2.0-or-later
import pytest

from libreprint.decide import best_ipp_uri, decide
from libreprint.models import Device, HplipInfo, Method, ScanMethod

PLAIN = HplipInfo("laserjet_pro_m404", supported=True, plugin=False, scan=False)
PLUGIN = HplipInfo("laserjet_professional_p1102", supported=True, plugin=True, scan=False)
SCANNER = HplipInfo("officejet_pro_8600", supported=True, plugin=False, scan=True)
UNSUPPORTED = HplipInfo("deskjet_1000_j110_series", supported=False, plugin=False, scan=False)


def test_best_ipp_uri_prefers_ipps_and_never_dnssd():
    uris = ["dnssd://x._ipp._tcp.local/", "ipp://a/ipp/print", "ipps://a/ipp/print"]
    assert best_ipp_uri(uris) == "ipps://a/ipp/print"
    assert best_ipp_uri(["dnssd://x._ipp._tcp.local/", "ipp://a/p"]) == "ipp://a/p"
    assert best_ipp_uri(["dnssd://x._ipp._tcp.local/", "usb://HP/x"]) is None


def test_driverless_network_prefers_ipps():
    dev = Device(
        "OfficeJet Pro 9010 series",
        "network",
        uris=["ipp://192.168.1.50:631/ipp/print", "ipps://192.168.1.50:631/ipp/print"],
        ipp_everywhere=True,
        escl=True,
    )
    plan = decide(dev, None, set())
    assert plan.method == Method.DRIVERLESS
    assert plan.ppd == "everywhere"
    assert plan.uri == "ipps://192.168.1.50:631/ipp/print"
    assert plan.scan == ScanMethod.ESCL
    assert plan.packages == ["sane-airscan", "sane-utils"]
    assert plan.queue == "HP_OfficeJet_Pro_9010_series"


def test_driverless_usb_via_ipp_usb():
    dev = Device(
        "LaserJet Pro M404",
        "usb",
        uris=["usb://HP/LaserJet%20Pro%20M404?serial=1", "ipp://localhost:60000/ipp/print"],
        ipp_everywhere=True,
    )
    plan = decide(dev, PLAIN, set())
    assert plan.method == Method.DRIVERLESS
    assert plan.uri == "ipp://localhost:60000/ipp/print"
    assert plan.scan == ScanMethod.NONE
    assert plan.packages == []


def test_dnssd_only_falls_through_to_hplip():
    dev = Device(
        "LaserJet Pro M404",
        "network",
        uris=["dnssd://HP._ipp._tcp.local/", "hp:/net/HP_LaserJet_Pro_M404?ip=10.0.0.9"],
        ipp_everywhere=True,
    )
    plan = decide(dev, PLAIN, set())
    assert plan.method == Method.HPLIP
    assert plan.uri == "hp:/net/HP_LaserJet_Pro_M404?ip=10.0.0.9"


def test_hplip_usb_no_plugin():
    dev = Device(
        "LaserJet Pro M404", "usb", uris=["usb://HP/x", "hp:/usb/HP_LaserJet_Pro_M404?serial=1"]
    )
    plan = decide(dev, PLAIN, set())
    assert plan.method == Method.HPLIP
    assert plan.uri == "hp:/usb/HP_LaserJet_Pro_M404?serial=1"
    assert plan.ppd is None
    assert plan.packages[:2] == ["hplip", "printer-driver-hpcups"]
    assert plan.needs_plugin is False


def test_hplip_plugin():
    dev = Device("LaserJet Professional P1102", "usb", uris=["hp:/usb/HP_LaserJet?serial=1"])
    plan = decide(dev, PLUGIN, set())
    assert plan.method == Method.HPLIP_PLUGIN
    assert plan.needs_plugin is True


def test_hplip_scan_without_escl():
    dev = Device("Officejet Pro 8600", "network", ip="10.0.0.5")
    plan = decide(dev, SCANNER, set())
    assert plan.scan == ScanMethod.HPAIO
    assert "libsane-hpaio" in plan.packages
    assert plan.uri is None


def test_escl_wins_over_hpaio():
    dev = Device("Officejet Pro 8600", "network", ip="10.0.0.5", escl=True)
    plan = decide(dev, SCANNER, set())
    assert plan.scan == ScanMethod.ESCL
    assert plan.packages == ["hplip", "printer-driver-hpcups", "sane-airscan", "sane-utils"]


def test_packages_are_deduplicated_in_order():
    dev = Device("Officejet Pro 8600", "network", ip="10.0.0.5")
    plan = decide(dev, SCANNER, set())
    assert len(plan.packages) == len(set(plan.packages))
    assert plan.packages == ["hplip", "printer-driver-hpcups", "libsane-hpaio", "sane-utils"]


@pytest.mark.parametrize(
    ("info", "reason"),
    [
        (UNSUPPORTED, "HPLIP lists this model as unsupported"),
        (None, "model not found in the installed HPLIP database"),
    ],
)
def test_unsupported(info, reason):
    dev = Device("DeskJet 1000 J110", "usb", uris=["usb://HP/x"])
    plan = decide(dev, info, {"HP_DeskJet_1000_J110"})
    assert plan.method == Method.UNSUPPORTED
    assert plan.queue is None
    assert plan.reason == reason
    assert plan.packages == []


def test_taken_names_get_suffix():
    dev = Device("LaserJet 1020", "usb", uris=["hp:/usb/x"])
    info = HplipInfo("laserjet_1020", True, False, False)
    plan = decide(dev, info, {"HP_LaserJet_1020"})
    assert plan.queue == "HP_LaserJet_1020_2"


def test_other_make_driverless():
    dev = Device(
        model="HL-L2350DW series",
        connection="network",
        uris=["ipp://10.0.0.7:631/ipp/print"],
        ipp_everywhere=True,
        make="Brother",
    )
    plan = decide(dev, None, set())
    assert plan.method is Method.DRIVERLESS
    assert plan.queue == "Brother_HL_L2350DW_series"


def test_other_make_never_uses_hplip():
    dev = Device(model="MG3600 series", connection="usb", uris=["usb://Canon/MG3600"], make="Canon")
    plan = decide(dev, HplipInfo("mg3600_series", supported=True, plugin=False, scan=True), set())
    assert plan.method is Method.UNSUPPORTED
    assert plan.scan is ScanMethod.NONE
    assert "manufacturer's Linux driver" in plan.reason
