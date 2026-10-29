# SPDX-License-Identifier: GPL-2.0-or-later
from pathlib import Path

import pytest

from libreprint import __version__
from libreprint.runner import FakeRunner
from libreprint.state import CONFIG_PATH, Config, load_config

ROOT = Path(__file__).resolve().parent.parent
DEBIAN = ROOT / "packaging" / "DEBIAN"
SCRIPTS = ["postinst", "prerm", "postrm"]


def read(*parts):
    return ROOT.joinpath(*parts).read_text(encoding="utf-8")


def test_udev_rule_matches_hp_usb_and_starts_the_unit():
    rule = read("data", "60-libreprint.rules")
    assert '"03f0"' in rule
    assert "libreprint-usb@%k.service" in rule
    assert 'SUBSYSTEM=="usb"' in rule


def test_usb_unit_runs_auto_for_the_instance():
    unit = read("data", "libreprint-usb@.service")
    assert "ExecStart=/usr/bin/libreprint auto --usb %I" in unit
    assert "Type=oneshot" in unit
    assert "After=cups.service ipp-usb.service" in unit


def test_netwatch_unit():
    unit = read("data", "libreprint-netwatch.service")
    assert "ExecStart=/usr/bin/libreprint watch" in unit
    assert "Restart=always" in unit
    assert "WantedBy=multi-user.target" in unit


def test_default_conf_parses_to_default_config():
    runner = FakeRunner(files={CONFIG_PATH: read("data", "libreprint.conf")})
    assert load_config(runner) == Config()


def test_control_file():
    control = read("packaging", "DEBIAN", "control")
    assert "Package: libreprint\n" in control
    assert "Version: @VERSION@\n" in control
    assert "Architecture: all\n" in control
    assert "Depends: python3 (>= 3.10), cups, cups-client\n" in control
    assert (
        "Recommends: ipp-usb, avahi-daemon, avahi-utils, libnss-mdns, printer-driver-hpcups, "
        "hplip, sane-utils, sane-airscan, libsane-hpaio, cups-ipp-utils, "
        "python3-gi, gir1.2-adw-1, python3-cairo\n"
    ) in control
    assert "not affiliated with HP Inc." in control


def test_conffiles_lists_the_config():
    assert read("packaging", "DEBIAN", "conffiles").split() == ["/etc/libreprint/libreprint.conf"]


@pytest.mark.parametrize("name", SCRIPTS)
def test_maintainer_scripts_are_posix_sh_with_set_e(name):
    text = read("packaging", "DEBIAN", name)
    assert text.startswith("#!/bin/sh\n")
    assert "set -e" in text
    assert "\r" not in text


def test_postinst_runs_initial_auto_in_background_and_no_template_unit():
    text = read("packaging", "DEBIAN", "postinst")
    assert "/usr/bin/libreprint auto --all" in text
    assert "libreprint-usb@all" not in text
    assert "/run/systemd/system" in text


def test_postrm_purge_removes_state_only():
    text = read("packaging", "DEBIAN", "postrm")
    assert "purge)" in text
    assert "rm -rf /var/lib/libreprint" in text


@pytest.mark.parametrize(
    "path",
    [
        "packaging/build-deb.sh",
        "packaging/build-apt-repo.sh",
        "tests/integration/run.sh",
        "install.sh",
        *[f"packaging/DEBIAN/{name}" for name in SCRIPTS],
    ],
)
def test_shell_scripts_use_lf_line_endings(path):
    assert b"\r" not in (ROOT / path).read_bytes()


def test_version_is_a_plain_literal_for_build_deb():
    text = read("src", "libreprint", "__init__.py")
    assert f'__version__ = "{__version__}"' in text
