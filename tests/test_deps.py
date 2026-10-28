# SPDX-License-Identifier: GPL-2.0-or-later
from hpeasy import deps
from hpeasy.runner import FakeRunner, Result

QUERY = ["dpkg-query", "-W", "-f=${db:Status-Status}"]


def test_missing_packages():
    runner = (
        FakeRunner()
        .on(*QUERY, "hplip", out="installed")
        .on(*QUERY, "sane-airscan", code=1, err="no packages found")
    )
    assert deps.missing_packages(runner, ["hplip", "sane-airscan"]) == ["sane-airscan"]
    assert deps.is_installed(runner, "hplip") is True
    assert deps.is_installed(runner, "sane-airscan") is False


def test_not_installed_status_is_missing():
    runner = FakeRunner().on(*QUERY, "pkg", out="config-files")
    assert deps.is_installed(runner, "pkg") is False


def test_install_retries_after_update():
    install = ["apt-get", "install", "-y", "sane-airscan"]
    runner = FakeRunner().on_seq(
        *install,
        results=[Result(100, "", "E: Unable to locate package sane-airscan"), Result(0)],
    )
    res = deps.install(runner, ["sane-airscan"])
    assert res.ok
    assert runner.calls == [install, ["apt-get", "update"], install]


def test_install_does_not_retry_other_errors():
    runner = FakeRunner().on("apt-get", "install", code=100, err="E: dpkg was interrupted")
    res = deps.install(runner, ["x"])
    assert res.code == 100
    assert runner.calls == [["apt-get", "install", "-y", "x"]]


def test_install_empty_noop():
    runner = FakeRunner()
    assert deps.install(runner, []).ok
    assert runner.calls == []


def test_binary_packages_mapping():
    assert deps.BINARY_PACKAGES["lpadmin"] == "cups-client"
    assert deps.BINARY_PACKAGES["ipptool"] == "cups-ipp-utils"
