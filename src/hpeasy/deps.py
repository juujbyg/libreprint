# SPDX-License-Identifier: GPL-2.0-or-later
"""System package checks and installation through dpkg/apt."""

from __future__ import annotations

from hpeasy.runner import Result, Runner

BINARY_PACKAGES: dict[str, str] = {
    "lpadmin": "cups-client",
    "lpstat": "cups-client",
    "lpinfo": "cups-client",
    "lp": "cups-client",
    "avahi-browse": "avahi-utils",
    "ipptool": "cups-ipp-utils",
    "hp-plugin": "hplip",
    "hp-makeuri": "hplip",
    "scanimage": "sane-utils",
    "ufw": "ufw",
}

_INSTALL_TIMEOUT = 900
_NOT_FOUND_MARKERS = ("Unable to locate package", "has no installation candidate")


def is_installed(runner: Runner, package: str) -> bool:
    res = runner.run(["dpkg-query", "-W", "-f=${db:Status-Status}", package])
    return res.ok and res.out.strip() == "installed"


def missing_packages(runner: Runner, packages: list[str]) -> list[str]:
    return [pkg for pkg in packages if not is_installed(runner, pkg)]


def install(runner: Runner, packages: list[str]) -> Result:
    if not packages:
        return Result(0)
    argv = ["apt-get", "install", "-y", *packages]
    res = runner.run(argv, timeout=_INSTALL_TIMEOUT)
    if not res.ok and any(marker in res.err for marker in _NOT_FOUND_MARKERS):
        runner.run(["apt-get", "update"], timeout=_INSTALL_TIMEOUT)
        res = runner.run(argv, timeout=_INSTALL_TIMEOUT)
    return res
