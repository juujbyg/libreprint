# SPDX-License-Identifier: GPL-2.0-or-later
from conftest import fixture

from hpeasy import discovery
from hpeasy.runner import FakeRunner


def test_parse_lpinfo_filters_hp():
    devices = discovery.parse_lpinfo(fixture("lpinfo_usb.txt"))
    assert len(devices) == 2
    for dev in devices:
        assert dev.model == "LaserJet Pro M404"
        assert dev.serial == "PHB1234567"
        assert dev.connection == "usb"
        assert dev.ipp_everywhere is True


def test_avahi_unescape_and_model():
    devices = discovery.parse_avahi(fixture("avahi.txt"))
    officejets = [d for d in devices if "OfficeJet" in d.model]
    assert officejets
    assert all(d.model == "OfficeJet Pro 9010 series" for d in officejets)
    assert not any("Brother" in d.model or "HL-L2350" in d.model for d in devices)


def test_avahi_uris():
    devices = discovery.parse_avahi(fixture("avahi.txt"))
    all_uris = [u for d in devices for u in d.uris]
    assert "ipp://192.168.1.50:631/ipp/print" in all_uris
    assert "ipp://[fe80::5265:f3ff:feab:c123]:631/ipp/print" in all_uris
    lo = [d for d in devices if "ipp://localhost:60000/ipp/print" in d.uris]
    assert len(lo) == 1
    assert lo[0].connection == "usb"


def test_merge_ipv4_ipv6_and_uscan():
    merged = discovery.merge(discovery.parse_avahi(fixture("avahi.txt")))
    officejets = [d for d in merged if d.model == "OfficeJet Pro 9010 series"]
    assert len(officejets) == 1
    dev = officejets[0]
    assert dev.escl is True
    assert dev.ipp_everywhere is True
    assert dev.ip == "192.168.1.50"
    assert dev.uuid == "1c852a4d-b800-1f08-abcd-5065f3abc123"
    assert dev.uris[0] == "ipp://192.168.1.50:631/ipp/print"


def test_merge_usb_and_ippusb():
    devices = discovery.parse_lpinfo(fixture("lpinfo_usb.txt")) + discovery.parse_avahi(
        fixture("avahi.txt")
    )
    merged = discovery.merge(devices)
    m404 = [d for d in merged if d.model == "LaserJet Pro M404"]
    assert len(m404) == 1
    assert set(m404[0].uris) == {
        "usb://HP/LaserJet%20Pro%20M404?serial=PHB1234567",
        "hp:/usb/HP_LaserJet_Pro_M404?serial=PHB1234567",
        "ipp://localhost:60000/ipp/print",
    }


def test_pdl_datastream_device():
    devices = discovery.parse_avahi(fixture("avahi.txt"))
    p2055 = [d for d in devices if d.model == "LaserJet P2055dn"]
    assert len(p2055) == 1
    assert p2055[0].ip == "192.168.1.60"
    assert p2055[0].ipp_everywhere is False
    assert p2055[0].uris == []


def test_discover_without_avahi():
    runner = FakeRunner(binaries={"lpinfo"}).on("lpinfo", out=fixture("lpinfo_usb.txt"))
    devices = discovery.discover(runner)
    assert len(devices) == 1


def test_parse_ipptool():
    dev = discovery.parse_ipptool(fixture("ipptool.txt"), "ipp://localhost:8631/ipp/print")
    assert dev is not None
    assert dev.model == "Fake LaserJet"
    assert dev.ipp_everywhere is True
    assert dev.uuid == "0e4c4f3a-1111-2222-3333-444455556666"
    assert dev.uris == ["ipp://localhost:8631/ipp/print"]
    assert dev.connection == "network"


def test_probe_uri_hp_scheme():
    dev = discovery.probe_uri(FakeRunner(), "hp:/net/OfficeJet_Pro_8600?ip=10.0.0.5")
    assert dev is not None
    assert dev.model == "OfficeJet Pro 8600"
    assert dev.ip == "10.0.0.5"
    assert dev.connection == "network"
