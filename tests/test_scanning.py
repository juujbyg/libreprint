# SPDX-License-Identifier: GPL-2.0-or-later
from libreprint import scanning
from libreprint.runner import FakeRunner

SCANIMAGE = (
    "device `airscan:e0:HP OfficeJet Pro 9010' is a eSCL HP OfficeJet Pro 9010 ip=192.168.1.50\n"
    "device `hpaio:/net/officejet_pro_8600?ip=10.0.0.5' is a Hewlett-Packard "
    "Officejet_Pro_8600 all-in-one\n"
)


def test_hpaio_enabled_in_dll_d():
    files = {scanning.DLL_CONF: "net\n#hpaio\n", scanning.DLL_D + "/hpaio": "hpaio\n"}
    assert scanning.hpaio_enabled(FakeRunner(files=files)) is True


def test_hpaio_enabled_in_dll_conf():
    assert scanning.hpaio_enabled(FakeRunner(files={scanning.DLL_CONF: "net\nhpaio\n"})) is True


def test_hpaio_commented_out():
    assert scanning.hpaio_enabled(FakeRunner(files={scanning.DLL_CONF: "#hpaio\n"})) is False


def test_hpaio_no_files():
    assert scanning.hpaio_enabled(FakeRunner()) is False


def test_enable_hpaio():
    r = FakeRunner()
    scanning.enable_hpaio(r)
    assert r.files[scanning.DLL_D + "/libreprint"] == "hpaio\n"
    assert scanning.hpaio_enabled(r) is True


def test_disable_escl_backend():
    r = FakeRunner(files={scanning.DLL_CONF: "net\nescl\nfujitsu\n"})
    assert scanning.disable_escl_backend(r) is True
    assert r.files[scanning.DLL_CONF].splitlines()[1].startswith("#escl")
    assert scanning.disable_escl_backend(r) is False


def test_list_scanners():
    r = FakeRunner().on("scanimage", "-L", out=SCANIMAGE)
    assert scanning.list_scanners(r) == [
        "airscan:e0:HP OfficeJet Pro 9010",
        "hpaio:/net/officejet_pro_8600?ip=10.0.0.5",
    ]


def test_list_scanners_without_scanimage():
    assert scanning.list_scanners(FakeRunner(binaries=set())) == []


def test_scanner_for():
    scanners = scanning.list_scanners(FakeRunner().on("scanimage", "-L", out=SCANIMAGE))
    assert scanning.scanner_for(scanners, "OfficeJet Pro 9010 series") == scanners[0]
    assert scanning.scanner_for(scanners, "Officejet Pro 8600") == scanners[1]
    assert scanning.scanner_for(scanners, "LaserJet 1020") is None
