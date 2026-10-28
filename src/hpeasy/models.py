# SPDX-License-Identifier: GPL-2.0-or-later
"""Plain data models shared across hpeasy."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Method(str, Enum):
    DRIVERLESS = "driverless"
    HPLIP = "hplip"
    HPLIP_PLUGIN = "hplip-plugin"
    UNSUPPORTED = "unsupported"


class ScanMethod(str, Enum):
    ESCL = "escl"
    HPAIO = "hpaio"
    NONE = "none"


@dataclass
class Device:
    model: str  # without "HP "/"Hewlett-Packard " prefix
    connection: str  # "usb" | "network"
    uris: list[str] = field(default_factory=list)
    serial: str | None = None
    uuid: str | None = None  # lowercase
    ip: str | None = None
    ipp_everywhere: bool = False
    escl: bool = False

    @property
    def display_name(self) -> str:
        return "HP " + self.model


@dataclass(frozen=True)
class HplipInfo:
    name: str
    supported: bool
    plugin: bool
    scan: bool


@dataclass
class Plan:
    device: Device
    method: Method
    scan: ScanMethod
    uri: str | None = None
    ppd: str | None = None
    queue: str | None = None
    packages: list[str] = field(default_factory=list)
    needs_plugin: bool = False
    reason: str = ""


@dataclass(frozen=True)
class Check:
    id: str
    status: str  # "ok" | "fail" | "warn" | "skip"
    message: str
    fix: str | None = None
    fix_argv: tuple[str, ...] | None = None
