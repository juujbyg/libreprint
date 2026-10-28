# SPDX-License-Identifier: GPL-2.0-or-later
from conftest import fixture

from hpeasy import queues
from hpeasy.models import Device
from hpeasy.queues import Queue

UUID_URI = (
    "dnssd://HP%20OfficeJet._ipp._tcp.local/?uuid=1C852A4D-B800-1F08-ABCD-5065F3ABC123"
)


def test_parse_lpstat_v():
    out = (
        "device for HP_A: ipp://192.168.1.50:631/ipp/print\n"
        "device for HP_B: " + UUID_URI + "\n"
        "garbage line\n"
        "\n"
    )
    assert queues.parse_lpstat_v(out) == [
        Queue("HP_A", "ipp://192.168.1.50:631/ipp/print"),
        Queue("HP_B", UUID_URI),
    ]


def test_queue_name_basic():
    assert queues.queue_name("OfficeJet Pro 9010 series", set()) == "HP_OfficeJet_Pro_9010_series"


def test_queue_name_collision():
    taken = {"HP_LaserJet_1020", "HP_LaserJet_1020_2"}
    assert queues.queue_name("LaserJet 1020", taken) == "HP_LaserJet_1020_3"


def test_find_existing_by_uri():
    dev = Device("X", "network", uris=["ipp://10.0.0.5:631/ipp/print"])
    q = Queue("HP_X", "ipp://10.0.0.5:631/ipp/print")
    assert queues.find_existing(dev, [Queue("Other", "ipp://1.1.1.1/x"), q]) == q


def test_find_existing_by_uuid_in_dnssd_uri():
    dev = Device("OfficeJet", "network", uuid="1c852a4d-b800-1f08-abcd-5065f3abc123")
    q = Queue("HP_OfficeJet", UUID_URI)
    assert queues.find_existing(dev, [q]) == q


def test_find_existing_by_serial():
    dev = Device("LaserJet Pro M404", "usb", serial="PHB1234567")
    q = Queue("HP_M404", "hp:/usb/HP_LaserJet_Pro_M404?serial=phb1234567")
    assert queues.find_existing(dev, [q]) == q


def test_find_existing_by_ip():
    dev = Device("P2055dn", "network", ip="192.168.1.60")
    q1 = Queue("HP_A", "hp:/net/HP_LaserJet_P2055dn?ip=192.168.1.60")
    q2 = Queue("HP_B", "socket://192.168.1.60:9100")
    assert queues.find_existing(dev, [q1]) == q1
    assert queues.find_existing(dev, [q2]) == q2
    assert queues.find_existing(dev, [Queue("HP_C", "hp:/net/X?ip=192.168.1.600")]) is None


def test_find_existing_none():
    dev = Device("X", "network", uris=["ipp://10.0.0.5/ipp/print"], serial="S1", ip="10.0.0.5")
    assert queues.find_existing(dev, [Queue("HP_Y", "ipp://10.0.0.9/ipp/print")]) is None


def test_lpadmin_argv():
    assert queues.lpadmin_argv("HP_X", "ipp://h/p", "everywhere") == [
        "lpadmin", "-p", "HP_X", "-E", "-v", "ipp://h/p", "-m", "everywhere",
        "-o", "printer-is-shared=false",
    ]  # fmt: skip


def test_find_hpcups_ppd():
    out = fixture("lpinfo_m.txt")
    assert (
        queues.find_hpcups_ppd(out, "LaserJet Pro M404")
        == "drv:///hpcups.drv/hp-laserjet_pro_m404-m405.ppd"
    )
    assert (
        queues.find_hpcups_ppd(out, "Officejet Pro 8600")
        == "drv:///hpcups.drv/hp-officejet_pro_8600.ppd"
    )
    assert queues.find_hpcups_ppd(out, "DeskJet 9999") is None


def test_find_hpcups_ppd_never_hpijs_only():
    out = "drv:///hpijs.drv/hp-foo.ppd HP LaserJet Foo hpijs\n"
    assert queues.find_hpcups_ppd(out, "LaserJet Foo") is None


def test_disabled_queues():
    out = (
        "printer HP_A disabled since Tue 28 Oct 2026 10:00:00 -\n"
        "\treason unknown\n"
        "printer HP_B is idle.  enabled since Tue 28 Oct 2026 10:00:00\n"
    )
    assert queues.disabled_queues(out) == ["HP_A"]
