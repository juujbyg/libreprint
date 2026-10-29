# SPDX-License-Identifier: GPL-2.0-or-later
"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict

from libreprint import __version__, doctor, hplipdb, plugin
from libreprint import setup as setup_mod
from libreprint.decide import decide
from libreprint.discovery import discover
from libreprint.models import Device
from libreprint.queues import find_existing, parse_lpstat_v
from libreprint.runner import Runner
from libreprint.setup import Options, Outcome
from libreprint.state import load_config
from libreprint.ui import ConsoleUI

EXIT_OK, EXIT_ERROR, EXIT_USAGE, EXIT_ROOT, EXIT_NO_DEVICE, EXIT_USER_ACTION = 0, 1, 2, 3, 4, 5

_UNICODE = {"ok": "✔", "fail": "✖", "dot": "•", "arrow": "→"}
_ASCII = {"ok": "[ok]", "fail": "[x]", "dot": "-", "arrow": "->"}


def _symbols() -> dict[str, str]:
    encoding = getattr(sys.stdout, "encoding", None) or "ascii"
    try:
        "".join(_UNICODE.values()).encode(encoding)
    except (UnicodeEncodeError, LookupError):
        return _ASCII
    return _UNICODE


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="libreprint", description="Set up any HP printer or MFP with one command."
    )
    parser.add_argument("--version", action="version", version=f"libreprint {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    p = sub.add_parser("setup", help="detect HP devices and create their print queues")
    p.add_argument("--uri", help="configure this device URI instead of discovering")
    p.add_argument("--yes", action="store_true", help="do not ask questions")
    p.add_argument("--no-test-page", action="store_true", help="do not print a test page")
    p.add_argument("--force", action="store_true", help="reconfigure an existing queue")

    p = sub.add_parser("list", help="list detected HP devices")
    p.add_argument("--json", action="store_true", help="machine-readable output")

    p = sub.add_parser("doctor", help="diagnose common problems")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--fix", action="store_true", help="apply the available fixes (needs root)")

    p = sub.add_parser("plugin", help="install the HP plugin (accepting HP's license)")
    p.add_argument("--yes", action="store_true", help="do not ask questions")

    p = sub.add_parser("auto", help="non-interactive setup (used by udev and packaging)")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--usb", metavar="DEVNAME", help="a USB device was just plugged in")
    group.add_argument("--all", action="store_true", help="USB and network devices")

    sub.add_parser("watch", help="watch the network for new HP printers (systemd service)")
    sub.add_parser("gui", help="open the graphical app: ink, printing, scanning, diagnostics")
    return parser


def _needs_root(args: argparse.Namespace) -> bool:
    if args.command in ("setup", "plugin", "auto", "watch"):
        return True
    return args.command == "doctor" and args.fix


def _default_euid() -> int:
    geteuid = getattr(os, "geteuid", None)
    return geteuid() if geteuid is not None else 0


def _elevate(argv: list[str]) -> int:
    if sys.stdin.isatty():
        try:
            os.execvp("sudo", ["sudo", sys.executable, "-m", "libreprint", *argv])
        except OSError as exc:
            print(f"libreprint: could not run sudo: {exc}", file=sys.stderr)
            return EXIT_ROOT
    print("libreprint: this command needs root (try: sudo libreprint ...)", file=sys.stderr)
    return EXIT_ROOT


def _print_outcome(outcome: Outcome, sym: dict[str, str]) -> None:
    name = outcome.device.display_name
    status = outcome.status
    if status == "created":
        method = outcome.plan.method.value if outcome.plan else "?"
        print(f"{sym['ok']} {name} {sym['arrow']} queue {outcome.queue} ({method})")
    elif status == "exists":
        print(f"{sym['dot']} {name}: already configured as {outcome.queue}")
    elif status == "needs-plugin":
        print(f"! {name} needs the HP plugin: run sudo libreprint plugin")
    elif status == "skipped":
        print(
            f"{sym['dot']} {name}: skipped" + (f" ({outcome.message})" if outcome.message else "")
        )
    else:
        print(f"{sym['fail']} {name}: {outcome.message or status}")
    if outcome.scanner:
        print(f"  scanner: {outcome.scanner}")
    if outcome.message and status in ("created", "exists"):
        print(f"  note: {outcome.message}")


def _report(outcomes: list[Outcome]) -> int:
    sym = _symbols()
    for outcome in outcomes:
        _print_outcome(outcome, sym)
    statuses = {o.status for o in outcomes}
    if "needs-plugin" in statuses:
        return EXIT_USER_ACTION
    if statuses & {"failed", "unsupported"}:
        return EXIT_ERROR
    return EXIT_OK


def _cmd_setup(args: argparse.Namespace, runner: Runner) -> int:
    opts = Options(
        assume_yes=args.yes, test_page=not args.no_test_page, force=args.force, uri=args.uri
    )
    ui = ConsoleUI(assume_yes=args.yes)
    outcomes = setup_mod.run_setup(runner, opts, load_config(runner), ui)
    if not outcomes:
        print("libreprint: no HP device found", file=sys.stderr)
        return EXIT_NO_DEVICE
    return _report(outcomes)


def _cmd_list(args: argparse.Namespace, runner: Runner) -> int:
    devices = discover(runner)
    db = hplipdb.load_from(runner)
    queues = parse_lpstat_v(runner.run(["lpstat", "-v"]).out)
    rows: list[tuple[Device, str, str]] = []
    for device in devices:
        info = hplipdb.lookup(db, device.model) if db else None
        method = decide(device, info, {q.name for q in queues}).method.value
        existing = find_existing(device, queues)
        rows.append((device, method, existing.name if existing else "-"))
    if args.json:
        print(json.dumps([{**asdict(d), "method": m, "queue": q} for d, m, q in rows], indent=2))
        return EXIT_OK
    header = ("MODEL", "CONNECTION", "METHOD", "QUEUE")
    table = [header, *[(d.display_name, d.connection, m, q) for d, m, q in rows]]
    widths = [max(len(row[i]) for row in table) for i in range(len(header))]
    for row in table:
        print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)).rstrip())
    if not rows:
        print("No HP device found.", file=sys.stderr)
    return EXIT_OK


def _cmd_doctor(args: argparse.Namespace, runner: Runner) -> int:
    devices = discover(runner)
    checks = doctor.run_checks(runner, devices)
    if args.fix:
        checks = doctor.apply_fixes(runner, checks)
    if args.json:
        print(doctor.to_json(checks, devices, hplip=plugin.hplip_version(runner)))
    else:
        labels = {"ok": "[ OK ]", "fail": "[FAIL]", "warn": "[WARN]", "skip": "[SKIP]"}
        for check in checks:
            print(f"{labels.get(check.status, '[????]')} {check.id}: {check.message}")
            if check.fix and check.status in ("fail", "warn"):
                print(f"  fix: {check.fix}")
    return EXIT_ERROR if any(c.status == "fail" for c in checks) else EXIT_OK


def _cmd_plugin(args: argparse.Namespace, runner: Runner) -> int:
    print(
        "hp-plugin will download HP's proprietary plugin from HP; it is covered by HP's own "
        "license.",
        file=sys.stderr,
    )
    if not plugin.install_plugin(runner, interactive=not args.yes):
        print(
            "libreprint: the HP plugin is not installed (see the messages above)",
            file=sys.stderr,
        )
        return EXIT_ERROR
    print("HP plugin installed.")
    pending = setup_mod.clear_pending_plugin(runner)
    if not pending:
        return EXIT_OK
    outcomes = setup_mod.run_setup(
        runner,
        Options(assume_yes=True, test_page=False),
        load_config(runner),
        ConsoleUI(assume_yes=True),
        models=set(pending),
    )
    return _report(outcomes)


def _cmd_auto(args: argparse.Namespace, runner: Runner) -> int:
    outcomes = setup_mod.run_auto(runner, load_config(runner), usb_only=not args.all)
    return EXIT_ERROR if any(o.status == "failed" for o in outcomes) else EXIT_OK


def _cmd_watch(args: argparse.Namespace, runner: Runner) -> int:
    setup_mod.watch(runner, load_config(runner))
    return EXIT_OK


def _cmd_gui(args: argparse.Namespace, runner: Runner) -> int:
    try:
        from libreprint import gui
    except (ImportError, ValueError) as exc:
        print(f"libreprint: the graphical app needs GTK 4 and libadwaita ({exc})", file=sys.stderr)
        print("  sudo apt install python3-gi gir1.2-adw-1", file=sys.stderr)
        return EXIT_ERROR
    return gui.main(runner)


_COMMANDS = {
    "setup": _cmd_setup,
    "list": _cmd_list,
    "doctor": _cmd_doctor,
    "plugin": _cmd_plugin,
    "auto": _cmd_auto,
    "watch": _cmd_watch,
    "gui": _cmd_gui,
}


def main(
    argv: list[str] | None = None,
    runner: Runner | None = None,
    *,
    euid: int | None = None,
) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()
    try:
        args = parser.parse_args(raw_argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else EXIT_USAGE
    if args.command is None:
        parser.print_usage(sys.stderr)
        return EXIT_USAGE
    if _needs_root(args) and (_default_euid() if euid is None else euid) != 0:
        return _elevate(raw_argv)
    try:
        return _COMMANDS[args.command](args, runner if runner is not None else Runner())
    except KeyboardInterrupt:
        return 130
