# SPDX-License-Identifier: GPL-2.0-or-later
import pytest

from libreprint import status, testpage
from libreprint.queues import Queue
from libreprint.runner import FakeRunner

URI = "ipps://HPFAKE.local:631/ipp/print"
QUEUE = Queue("HP_ENVY_6000_series", URI)
IPP = (
    "    printer-name (nameWithoutLanguage) = HP27647F\n"
    "    printer-make-and-model (textWithoutLanguage) = HP ENVY 6000 series\n"
    "    media-default (keyword) = iso_a4_210x297mm\n"
    "    media-col-default (collection) = {media-size={x-dimension=21000 y-dimension=29700} "
    "media-top-margin=296 media-bottom-margin=296 media-left-margin=296 media-right-margin=296}\n"
)
ADAPTERS = (
    "<io:Adapters><io:Adapter><wifi:SSID>{ssid}</wifi:SSID>"
    "<dd:IsConnected>{connected}</dd:IsConnected></io:Adapter>"
    "<io:Adapter><dd:IsConnected>false</dd:IsConnected></io:Adapter></io:Adapters>"
)


def runner():
    return FakeRunner().on("ipptool", out=IPP)


def test_paper_size():
    assert testpage.paper_size("iso_a4_210x297mm") == ("A4", (210.0, 297.0))
    assert testpage.paper_size("na_letter_8.5x11in") == ("Letter", (215.9, 279.4))
    assert testpage.paper_size("") == ("A4", (210.0, 297.0))


def test_parse_margins_defaults_when_missing():
    assert testpage.parse_margins("media-top-margin=296 media-left-margin=0").top == 2.96
    assert testpage.parse_margins("media-top-margin=296 media-left-margin=0").left == 0
    assert testpage.parse_margins("").bottom == testpage.DEFAULT_MARGIN_MM


def test_parse_hp_ssid():
    hex_name = b"OFFICE".hex()
    assert testpage.parse_hp_ssid(ADAPTERS.format(ssid=hex_name, connected="true")) == "OFFICE"
    assert testpage.parse_hp_ssid(ADAPTERS.format(ssid="Plain name", connected="true")) == (
        "Plain name"
    )
    assert testpage.parse_hp_ssid(ADAPTERS.format(ssid=hex_name, connected="false")) is None


def test_collect_uses_the_printers_own_wifi():
    fake = runner()
    fake.urls["http://hpfake.local/IoMgmt/Adapters"] = ADAPTERS.format(
        ssid=b"OFFICE".hex(), connected="true"
    )
    info = testpage.collect(fake, QUEUE)
    assert info.wifi == "OFFICE"
    assert info.printer == "HP27647F"
    assert info.model == "HP ENVY 6000 series"
    assert info.margins.right == 2.96


def test_collect_prefers_the_ipp_attribute():
    fake = FakeRunner().on("ipptool", out=IPP + "    printer-wifi-ssid (name) = Lab\n")
    assert testpage.collect(fake, QUEUE).wifi == "Lab"


def test_wifi_fallback_is_labelled_as_the_computers():
    fake = runner().on("nmcli", out="no:Other\nyes:Home\\:5G\n")
    assert testpage.collect(fake, QUEUE).wifi == (
        "not reported by the printer (this computer: Home:5G)"
    )
    assert testpage.collect(runner(), QUEUE).wifi == "not reported"


def test_usb_printer_has_no_wifi_row():
    info = testpage.collect(FakeRunner(), Queue("Canon_MG3600", "usb://Canon/MG3600?serial=1"))
    labels = [label for label, _ in testpage.rows(info)]
    assert info.connection == "USB"
    assert "Wi-Fi" not in labels and "Address" not in labels
    assert info.model == "Canon MG3600"


def test_rows_keep_media_limits_and_no_dates():
    text = str(testpage.rows(testpage.collect(runner(), QUEUE)))
    assert "A4 (210 x 297 mm)" in text
    assert "204.1 x 291.1 mm" in text
    assert "Created" not in text and "Printed" not in text


def test_render_writes_a_pdf(tmp_path):
    pytest.importorskip("cairo")
    target = tmp_path / "page.pdf"
    testpage.render(testpage.collect(runner(), QUEUE), str(target))
    assert target.read_bytes().startswith(b"%PDF")


def test_print_argv_actual_size():
    assert "print-scaling=none" in status.print_argv("Q", "a.pdf", actual_size=True)
    assert "print-scaling=none" not in status.print_argv("Q", "a.pdf")
