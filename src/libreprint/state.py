# SPDX-License-Identifier: GPL-2.0-or-later
"""Persistent state, configuration and the process-wide lock."""

from __future__ import annotations

import configparser
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field

from libreprint.runner import Runner

STATE_PATH = "/var/lib/libreprint/state.json"
LEGACY_STATE_PATH = "/var/lib/hpeasy/state.json"  # before the rename to LibrePrint
CONFIG_PATH = "/etc/libreprint/libreprint.conf"
LOCK_PATH = "/run/libreprint.lock"


@dataclass
class State:
    queues: dict[str, str] = field(default_factory=dict)  # queue name -> device model
    pending_plugin: list[str] = field(default_factory=list)  # models waiting for the plugin


def load_state(runner: Runner) -> State:
    text = runner.read_file(STATE_PATH)
    if text is None:
        text = runner.read_file(LEGACY_STATE_PATH)
    if text is None:
        return State()
    try:
        data = json.loads(text)
    except ValueError:
        return State()
    if not isinstance(data, dict):
        return State()
    queues = data.get("queues")
    pending = data.get("pending_plugin")
    return State(
        queues=({str(k): str(v) for k, v in queues.items()} if isinstance(queues, dict) else {}),
        pending_plugin=[str(m) for m in pending] if isinstance(pending, list) else [],
    )


def save_state(runner: Runner, state: State) -> None:
    runner.write_file(STATE_PATH, json.dumps(asdict(state), indent=2, sort_keys=True) + "\n")


@dataclass(frozen=True)
class Config:
    usb: bool = True
    network: str = "add"
    accept_hp_plugin_license: bool = False
    install_packages: bool = True


def load_config(runner: Runner) -> Config:
    default = Config()
    text = runner.read_file(CONFIG_PATH)
    if text is None:
        return default
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        parser.read_string(text)
    except configparser.Error:
        return default

    def flag(key: str, fallback: bool) -> bool:
        try:
            return parser.getboolean("libreprint", key, fallback=fallback)
        except ValueError:
            return fallback

    network = parser.get("libreprint", "network", fallback=default.network).strip().lower()
    if network not in ("add", "off"):
        network = default.network
    return Config(
        usb=flag("usb", default.usb),
        network=network,
        accept_hp_plugin_license=flag("accept_hp_plugin_license", default.accept_hp_plugin_license),
        install_packages=flag("install_packages", default.install_packages),
    )


@contextmanager
def lock(path: str = LOCK_PATH) -> Iterator[None]:
    import fcntl  # Linux only; imported here so the module loads on other platforms

    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "a+", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
