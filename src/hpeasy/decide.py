# SPDX-License-Identifier: GPL-2.0-or-later
"""Pure decision engine: map a Device (and HPLIP knowledge) to a Plan."""

from __future__ import annotations

from hpeasy.models import Device, HplipInfo, Method, Plan, ScanMethod
from hpeasy.queues import queue_name

HPLIP_PACKAGES = ["hplip", "printer-driver-hpcups"]
ESCL_PACKAGES = ["sane-airscan", "sane-utils"]
HPAIO_PACKAGES = ["libsane-hpaio", "sane-utils"]


def best_ipp_uri(uris: list[str]) -> str | None:
    for scheme in ("ipps://", "ipp://"):
        for uri in uris:
            if uri.startswith(scheme):
                return uri
    return None


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def decide(device: Device, hplip: HplipInfo | None, taken_names: set[str]) -> Plan:
    if device.escl:
        scan, scan_packages = ScanMethod.ESCL, ESCL_PACKAGES
    elif hplip is not None and hplip.scan:
        scan, scan_packages = ScanMethod.HPAIO, HPAIO_PACKAGES
    else:
        scan, scan_packages = ScanMethod.NONE, []

    ipp_uri = best_ipp_uri(device.uris) if device.ipp_everywhere else None
    if ipp_uri is not None:
        return Plan(
            device=device,
            method=Method.DRIVERLESS,
            scan=scan,
            uri=ipp_uri,
            ppd="everywhere",
            queue=queue_name(device.model, taken_names),
            packages=_dedupe(list(scan_packages)),
        )

    if hplip is not None and hplip.supported:
        return Plan(
            device=device,
            method=Method.HPLIP_PLUGIN if hplip.plugin else Method.HPLIP,
            scan=scan,
            uri=next((u for u in device.uris if u.startswith("hp:")), None),
            ppd=None,
            queue=queue_name(device.model, taken_names),
            packages=_dedupe(HPLIP_PACKAGES + scan_packages),
            needs_plugin=hplip.plugin,
        )

    reason = (
        "HPLIP lists this model as unsupported"
        if hplip is not None
        else "model not found in the installed HPLIP database"
    )
    return Plan(device=device, method=Method.UNSUPPORTED, scan=scan, reason=reason)
