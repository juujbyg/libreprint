# SPDX-License-Identifier: GPL-2.0-or-later
"""Setup orchestration: turn discovered devices into working CUPS queues."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from urllib.parse import urlsplit

from libreprint import deps, hplipdb, plugin, scanning
from libreprint import state as state_mod
from libreprint.decide import best_ipp_uri, decide
from libreprint.discovery import discover, parse_avahi, probe_uri
from libreprint.hplipdb import normalize_model
from libreprint.models import Device, Method, Plan, ScanMethod
from libreprint.queues import (
    find_existing,
    find_hpcups_ppd,
    lpadmin_argv,
    parse_lpstat_v,
)
from libreprint.runner import Result, Runner
from libreprint.state import Config, State, save_state
from libreprint.status import TEST_PAGE_JOB
from libreprint.ui import UI, AutoUI

TEST_PAGE = "/usr/share/cups/data/testprint"

AUTO_RETRY_DELAYS = [2, 4, 8, 16, 30]
WATCH_SETTLE_SECONDS = 5

_PLUGIN_NOTICE = (
    "This printer needs HP's proprietary plugin. It is not part of libreprint or of your "
    "distribution: it is downloaded from HP and is covered by HP's own license."
)


@dataclass
class Options:
    assume_yes: bool = False
    test_page: bool = True
    force: bool = False
    uri: str | None = None


@dataclass
class Outcome:
    device: Device
    status: str  # "created" | "exists" | "needs-plugin" | "unsupported" | "failed" | "skipped"
    plan: Plan | None = None
    queue: str | None = None
    message: str = ""
    scanner: str | None = None


@contextmanager
def _locked() -> Iterator[None]:
    """Hold the process-wide lock; a no-op where fcntl does not exist (non-Linux)."""
    try:
        import fcntl  # noqa: F401
    except ImportError:
        yield
        return
    with state_mod.lock():
        yield


def _failed(device: Device, step: str, res: Result, plan: Plan | None = None) -> Outcome:
    detail = (res.err or res.out).strip()
    message = f"{step} failed (exit {res.code})" + (f": {detail}" if detail else "")
    return Outcome(device, "failed", plan=plan, message=message)


def _ensure_packages(
    runner: Runner, packages: list[str], config: Config, ui: UI, assume_yes: bool
) -> str | None:
    """Install missing packages after the consent rules; return an error message or None."""
    missing = deps.missing_packages(runner, packages)
    if not missing:
        return None
    if ui.interactive:
        allowed = ui.confirm(f"Install {', '.join(missing)}?")
    else:
        allowed = config.install_packages or assume_yes
    if not allowed:
        return f"required packages not installed: {', '.join(missing)}"
    res = deps.install(runner, missing)
    if not res.ok:
        detail = (res.err or res.out).strip()
        return f"apt-get install {' '.join(missing)} failed (exit {res.code})" + (
            f": {detail}" if detail else ""
        )
    return None


def _driverless_ready(device: Device) -> bool:
    return device.ipp_everywhere and best_ipp_uri(device.uris) is not None


def _awaiting_ipp_usb(runner: Runner, device: Device) -> bool:
    """An IPP-over-USB printer seen by lpinfo before ipp-usb has published its endpoint.

    Setting it up now would pick HPLIP, whose hp:/usb/ backend competes with ipp-usb
    for the same USB interface, so auto mode waits for the driverless endpoint.
    """
    return (
        device.connection == "usb"
        and device.ipp_everywhere
        and not _driverless_ready(device)
        and deps.is_installed(runner, "ipp-usb")
    )


def _hpmakeuri(runner: Runner, ip: str) -> str | None:
    res = runner.run(["hp-makeuri", "-c", ip], timeout=60)
    for token in res.out.split():
        if token.startswith("hp:/"):
            return token
    return None


def _hp_usb_uri(runner: Runner, model: str) -> str | None:
    wanted = normalize_model(model)
    for token in runner.run(["lpinfo", "-v"], timeout=60).out.split():
        if token.startswith("hp:/usb/") and wanted in normalize_model(urlsplit(token).path):
            return token
    return None


def _obtain_plugin(runner: Runner, config: Config, ui: UI) -> bool:
    if ui.interactive:
        ui.info(_PLUGIN_NOTICE)
        if not ui.confirm("Download and install the HP plugin now?"):
            return False
        return plugin.install_plugin(runner, interactive=True)
    if config.accept_hp_plugin_license:
        return plugin.install_plugin(runner, interactive=False)
    return False


def _configure_scanner(
    runner: Runner, device: Device, plan: Plan, outcome: Outcome, ui: UI
) -> None:
    if plan.scan is ScanMethod.HPAIO and not scanning.hpaio_enabled(runner):
        scanning.enable_hpaio(runner)
    if plan.scan is ScanMethod.ESCL:
        scanning.disable_escl_backend(runner)
    if plan.scan is ScanMethod.NONE:
        return
    found = scanning.scanner_for(scanning.list_scanners(runner), device.model)
    if found:
        outcome.scanner = found
        return
    note = "scanner not visible yet (check with: scanimage -L)"
    outcome.message = f"{outcome.message}; {note}" if outcome.message else note
    ui.warn(note)


def _setup_device(
    runner: Runner, device: Device, opts: Options, config: Config, state: State, ui: UI
) -> Outcome:
    # 1. Already configured?
    res = runner.run(["lpstat", "-v"])
    if res.code == 127:
        return _failed(device, "lpstat -v", res)
    queues = parse_lpstat_v(res.out)
    existing = find_existing(device, queues)
    taken = {q.name for q in queues}
    db = hplipdb.load_from(runner)

    if existing is not None and not opts.force:
        info = hplipdb.lookup(db, device.model) if db else None
        plan = decide(device, info, taken)
        outcome = Outcome(device, "exists", plan=plan, queue=existing.name)
        _configure_scanner(runner, device, plan, outcome, ui)
        return outcome
    if existing is not None:
        taken.discard(existing.name)  # --force: reconfigure the existing queue in place

    # 2. HP only: HPLIP database needed unless the device can be set up driverless right now.
    if device.is_hp and not _driverless_ready(device) and db is None:
        error = _ensure_packages(
            runner, ["hplip", "printer-driver-hpcups"], config, ui, opts.assume_yes
        )
        if error:
            return Outcome(device, "failed", message=error)
        db = hplipdb.load_from(runner)

    # 3-4. Decide.
    info = hplipdb.lookup(db, device.model) if db else None
    plan = decide(device, info, taken)
    if existing is not None:
        plan.queue = existing.name if plan.method is not Method.UNSUPPORTED else None
    if plan.method is Method.UNSUPPORTED:
        return Outcome(device, "unsupported", plan=plan, message=plan.reason)

    # 5. Packages.
    error = _ensure_packages(runner, plan.packages, config, ui, opts.assume_yes)
    if error:
        return Outcome(device, "failed", plan=plan, message=error)

    # 6. Plugin.
    if (
        plan.needs_plugin
        and not plugin.plugin_ok(runner)
        and not _obtain_plugin(runner, config, ui)
    ):
        if device.model not in state.pending_plugin:
            state.pending_plugin.append(device.model)
        save_state(runner, state)
        return Outcome(device, "needs-plugin", plan=plan, message="run: sudo libreprint plugin")

    # 7. Create the queue.
    assert plan.queue is not None
    if plan.method in (Method.HPLIP, Method.HPLIP_PLUGIN):
        if plan.uri is None:
            if device.connection == "network" and device.ip:
                plan.uri = _hpmakeuri(runner, device.ip)
            elif device.connection == "usb":
                plan.uri = _hp_usb_uri(runner, device.model)
        if plan.uri is None:
            return Outcome(
                device, "failed", plan=plan, message="could not determine the HPLIP device URI"
            )
        models = runner.run(["lpinfo", "-m"], timeout=120)
        plan.ppd = find_hpcups_ppd(models.out, device.model)
        if plan.ppd is None:
            return Outcome(
                device,
                "failed",
                plan=plan,
                message="no matching hpcups PPD found for " + device.model,
            )
    assert plan.uri is not None and plan.ppd is not None
    res = runner.run(lpadmin_argv(plan.queue, plan.uri, plan.ppd), timeout=120)
    if not res.ok:
        return _failed(device, "lpadmin", res, plan)
    if "no system default destination" in runner.run(["lpstat", "-d"]).out:
        res = runner.run(["lpadmin", "-d", plan.queue])
        if not res.ok:
            ui.warn(f"could not set {plan.queue} as default printer: {res.err.strip()}")
    state.queues[plan.queue] = device.model
    if device.model in state.pending_plugin:
        state.pending_plugin.remove(device.model)
    save_state(runner, state)
    outcome = Outcome(device, "created", plan=plan, queue=plan.queue)

    # 8. Scanner.
    _configure_scanner(runner, device, plan, outcome, ui)

    # 9. Test page.
    if opts.test_page and ui.interactive:
        res = runner.run(["lp", "-d", plan.queue, "-t", TEST_PAGE_JOB, TEST_PAGE])
        if not res.ok:
            ui.warn(f"test page failed: {res.err.strip()}")
    return outcome


def setup_device(
    runner: Runner, device: Device, opts: Options, config: Config, state: State, ui: UI
) -> Outcome:
    try:
        return _setup_device(runner, device, opts, config, state, ui)
    except Exception as exc:  # noqa: BLE001 - a bad device must not abort the whole run
        return Outcome(device, "failed", message=f"unexpected error: {exc}")


def _setup_all(
    runner: Runner, devices: list[Device], opts: Options, config: Config, ui: UI
) -> list[Outcome]:
    outcomes: list[Outcome] = []
    with _locked():
        state = state_mod.load_state(runner)
        for device in devices:
            outcomes.append(setup_device(runner, device, opts, config, state, ui))
    return outcomes


def run_setup(
    runner: Runner,
    opts: Options,
    config: Config,
    ui: UI,
    *,
    models: set[str] | None = None,
) -> list[Outcome]:
    """Set up discovered devices; ``models`` (additive) restricts them to those model names."""
    if opts.uri:
        probed = probe_uri(runner, opts.uri)
        devices = [probed] if probed is not None else []
    else:
        devices = discover(runner)
    if models is not None:
        devices = [d for d in devices if d.model in models]
    if ui.interactive and len(devices) > 1:
        picks = ui.choose(
            "Several printers found:", [f"{d.display_name} ({d.connection})" for d in devices]
        )
        devices = [devices[i] for i in picks]
    if not devices:
        return []
    return _setup_all(runner, devices, opts, config, ui)


def _summary(outcome: Outcome) -> str:
    name = outcome.device.display_name
    parts = [f"{name}: {outcome.status}"]
    if outcome.queue:
        parts.append(f"queue {outcome.queue}")
    if outcome.message:
        parts.append(outcome.message)
    return " - ".join(parts)


def run_auto(
    runner: Runner, config: Config, *, usb_only: bool, network_only: bool = False
) -> list[Outcome]:
    """Non-interactive setup for hotplug and network sightings.

    ``network_only`` is an additive option used by :func:`watch`.
    """
    want_usb = config.usb and not network_only
    want_network = config.network != "off" and not usb_only
    if not want_usb and not want_network:
        return []

    def wanted(devices: list[Device]) -> list[Device]:
        return [
            d
            for d in devices
            if (d.connection == "usb" and want_usb) or (d.connection == "network" and want_network)
        ]

    devices = wanted(discover(runner))
    for delay in AUTO_RETRY_DELAYS:
        if devices and not any(_awaiting_ipp_usb(runner, d) for d in devices):
            break
        runner.sleep(delay)
        devices = wanted(discover(runner))
    if not devices:
        return []
    ui = AutoUI()
    outcomes = _setup_all(runner, devices, Options(assume_yes=True, test_page=False), config, ui)
    for outcome in outcomes:
        ui.info(_summary(outcome))
    return outcomes


def watch(runner: Runner, config: Config) -> None:
    seen: set[str] = set()
    for line in runner.stream(["avahi-browse", "-a", "-r", "-p", "-k"]):
        if not line.startswith("="):
            continue
        fresh = False
        for device in parse_avahi(line):
            key = device.uuid or device.ip
            if device.connection != "network" or not key or key in seen:
                continue
            seen.add(key)
            fresh = True
        if fresh:
            runner.sleep(WATCH_SETTLE_SECONDS)
            run_auto(runner, config, usb_only=False, network_only=True)


def clear_pending_plugin(runner: Runner) -> list[str]:
    """Empty ``state.pending_plugin`` under the lock; return the models that were pending."""
    with _locked():
        state = state_mod.load_state(runner)
        pending = list(state.pending_plugin)
        if pending:
            state.pending_plugin = []
            save_state(runner, state)
    return pending
