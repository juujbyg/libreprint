# SPDX-License-Identifier: GPL-2.0-or-later
"""HP proprietary plugin status and installation (never redistributed by libreprint)."""

from __future__ import annotations

import configparser
import re

from libreprint.runner import Runner

HPLIP_STATE = "/var/lib/hp/hplip.state"

_VERSION = re.compile(r"^\d+(?:\.\d+)*")


def hplip_version(runner: Runner) -> str | None:
    res = runner.run(["dpkg-query", "-W", "-f=${Version}", "hplip"])
    if not res.ok:
        return None
    version = res.out.strip()
    if ":" in version:
        version = version.split(":", 1)[1]
    m = _VERSION.match(version)
    return m.group(0) if m else None


def plugin_version(runner: Runner) -> str | None:
    text = runner.read_file(HPLIP_STATE)
    if text is None:
        return None
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        parser.read_string(text)
    except configparser.Error:
        return None
    if parser.get("plugin", "installed", fallback="0").strip() != "1":
        return None
    return parser.get("plugin", "version", fallback="").strip() or None


def plugin_ok(runner: Runner) -> bool:
    have = plugin_version(runner)
    want = hplip_version(runner)
    return have is not None and want is not None and have == want


def install_plugin(runner: Runner, *, interactive: bool) -> bool:
    argv = ["hp-plugin", "-i"]
    if interactive:
        runner.run_interactive(argv)
    else:
        runner.run(argv, input="d\ny\n", timeout=600)
    return plugin_ok(runner)
