# SPDX-License-Identifier: GPL-2.0-or-later
from libreprint import plugin
from libreprint.runner import FakeRunner

VERSION_Q = ["dpkg-query", "-W", "-f=${Version}", "hplip"]


def test_hplip_version_strips_debian_suffix():
    r = FakeRunner().on(*VERSION_Q, out="3.23.12+dfsg0-0ubuntu5")
    assert plugin.hplip_version(r) == "3.23.12"
    r = FakeRunner().on(*VERSION_Q, out="1:3.22.10-1")
    assert plugin.hplip_version(r) == "3.22.10"


def test_hplip_version_missing():
    assert plugin.hplip_version(FakeRunner().on(*VERSION_Q, code=1)) is None
    assert plugin.hplip_version(FakeRunner().on(*VERSION_Q, out="")) is None


def _runner(state_version):
    files = {}
    if state_version is not None:
        files[plugin.HPLIP_STATE] = f"[plugin]\ninstalled=1\nversion={state_version}\n"
    return FakeRunner(files=files).on(*VERSION_Q, out="3.23.12+dfsg0-0ubuntu5")


def test_plugin_ok_matching():
    assert plugin.plugin_ok(_runner("3.23.12")) is True


def test_plugin_ok_mismatch():
    assert plugin.plugin_ok(_runner("3.22.10")) is False


def test_plugin_ok_missing_file():
    r = _runner(None)
    assert plugin.plugin_version(r) is None
    assert plugin.plugin_ok(r) is False


def test_plugin_version_requires_installed_flag():
    r = FakeRunner(files={plugin.HPLIP_STATE: "[plugin]\ninstalled=0\nversion=3.23.12\n"})
    assert plugin.plugin_version(r) is None


def test_install_plugin_noninteractive_input():
    r = _runner("3.23.12")
    assert plugin.install_plugin(r, interactive=False) is True
    assert ["hp-plugin", "-i"] in r.calls
    assert "d\ny\n" in r.inputs


def test_install_plugin_interactive():
    r = _runner("3.23.12")
    assert plugin.install_plugin(r, interactive=True) is True
    assert r.interactive_calls == [["hp-plugin", "-i"]]


def test_install_plugin_fails_when_state_missing():
    assert plugin.install_plugin(_runner(None), interactive=False) is False
