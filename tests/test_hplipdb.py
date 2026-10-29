# SPDX-License-Identifier: GPL-2.0-or-later
from conftest import fixture

from libreprint import hplipdb
from libreprint.runner import FakeRunner


def db():
    return hplipdb.load(fixture("models.dat"))


def test_normalize_model():
    assert hplipdb.normalize_model("HP LaserJet Pro M404dn") == "laserjet_pro_m404dn"
    assert (
        hplipdb.normalize_model("Hewlett-Packard OfficeJet Pro 9010 series")
        == "officejet_pro_9010_series"
    )
    assert hplipdb.normalize_model("hp deskjet 1000 j110 series") == "deskjet_1000_j110_series"


def test_lookup_plain():
    info = hplipdb.lookup(db(), "LaserJet Pro M404")
    assert info is not None
    assert info.supported is True
    assert info.plugin is False
    assert info.scan is False


def test_lookup_plugin_required():
    info = hplipdb.lookup(db(), "LaserJet Professional P1102")
    assert info is not None
    assert info.plugin is True


def test_lookup_scan():
    info = hplipdb.lookup(db(), "OfficeJet Pro 8600")
    assert info is not None
    assert info.scan is True


def test_lookup_series_variants():
    assert hplipdb.lookup(db(), "OfficeJet Pro 8600 series") is not None
    info = hplipdb.lookup(db(), "DeskJet 1000 J110")
    assert info is not None
    assert info.supported is False


def test_lookup_unknown():
    assert hplipdb.lookup(db(), "DeskJet 9999") is None


def test_load_tolerates_duplicate_sections():
    parsed = hplipdb.load("[a]\nplugin=0\n\n[a]\nplugin=1\n")
    assert "a" in parsed


def test_load_from_missing():
    assert hplipdb.load_from(FakeRunner(files={})) is None


def test_load_from_present():
    runner = FakeRunner(files={hplipdb.MODELS_DAT: fixture("models.dat")})
    loaded = hplipdb.load_from(runner)
    assert loaded is not None
    assert "laserjet_pro_m404" in loaded
