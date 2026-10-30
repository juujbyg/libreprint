# SPDX-License-Identifier: GPL-2.0-or-later
"""Graphical front end (GTK 4 + libadwaita): status and ink, printing, scanning, diagnostics."""

from __future__ import annotations

import os
import shutil
import tempfile
import threading
from collections.abc import Callable
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gsk", "4.0")
gi.require_version("Graphene", "1.0")
from gi.repository import Adw, Gdk, GdkPixbuf, Gio, GLib, Graphene, Gsk, Gtk

from libreprint import __version__, convert, doctor, scanning, status
from libreprint.models import Check
from libreprint.queues import Queue
from libreprint.runner import Runner
from libreprint.setup import TEST_PAGE

MIN_ADW = (1, 5)  # AboutDialog, ToolbarView, SpinRow, SwitchRow
APP_ID = "io.github.libreprint.LibrePrint"
REFRESH_SECONDS = 10
BUSY_REFRESH_SECONDS = 3  # while jobs are queued, so progress and cancels show up quickly
RESOLUTIONS = (75, 150, 300, 600, 1200)

_CSS = """
.status-pill { border-radius: 999px; padding: 4px 14px; font-weight: bold; }
.state-idle { background: alpha(@success_color, 0.15); color: @success_color; }
.state-processing { background: alpha(@accent_bg_color, 0.15); color: @accent_color; }
.state-stopped, .state-unknown { background: alpha(@error_color, 0.15); color: @error_color; }
.ink-card { padding: 18px 24px; }
.ink-low { color: @warning_color; font-weight: bold; }
.drop-hover { background: alpha(@accent_bg_color, 0.08); }
.queue-active { box-shadow: 0 0 0 2px alpha(@error_color, 0.6); }
.cancel-job { padding: 4px 14px; }
banner.queue-banner > revealer > widget { background-color: @error_bg_color; color: @error_fg_color; }
banner.queue-banner button { background-color: alpha(white, 0.2); color: @error_fg_color; }
"""

_STATE_LABELS = {
    "idle": "Ready",
    "processing": "Printing",
    "stopped": "Stopped",
    "unknown": "Unreachable",
}
_CHECK_TITLES = {
    "cups-service": "Printing service (CUPS)",
    "avahi-service": "Network discovery (Avahi)",
    "nss-mdns": "Printer name resolution (mDNS)",
    "ipp-usb": "USB driverless access (ipp-usb)",
    "firewall-mdns": "Firewall",
    "queues-enabled": "Print queues enabled",
    "queues-duplicate": "No duplicate queues",
    "hp-plugin": "HP plugin",
    "hplip-model": "Model support",
    "scanner": "Scanner",
    "user-groups": "Printer administration rights",
}
_CHECK_ICONS = {
    "ok": ("emblem-ok-symbolic", "success"),
    "warn": ("dialog-warning-symbolic", "warning"),
    "fail": ("dialog-error-symbolic", "error"),
    "skip": ("action-unavailable-symbolic", "dim-label"),
}


def _background(work: Callable[[], Any], done: Callable[[Any], None]) -> None:
    """Run ``work`` in a thread and hand its result (or exception) to ``done`` on the UI thread."""

    def target() -> None:
        try:
            result: Any = work()
        except Exception as exc:  # noqa: BLE001 - surfaced to the user by ``done``
            result = exc
        GLib.idle_add(lambda: done(result) and False)

    threading.Thread(target=target, daemon=True).start()


def _boxed_list(group: Adw.PreferencesGroup) -> Gtk.ListBox:
    """A boxed list inside ``group`` whose rows can be replaced with ``remove_all()``."""
    rows = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE, css_classes=["boxed-list"])
    group.add(rows)
    return rows


def _spinner(size: int = 16) -> Gtk.Widget:
    """Adw.Spinner needs libadwaita 1.6; fall back to Gtk.Spinner (Ubuntu 24.04 has 1.5)."""
    if hasattr(Adw, "Spinner"):
        return Adw.Spinner(width_request=size, height_request=size)
    return Gtk.Spinner(spinning=True, width_request=size, height_request=size)


def _pill_button(label: str, icon: str, suggested: bool = False) -> Gtk.Button:
    content = Adw.ButtonContent(label=label, icon_name=icon)
    button = Gtk.Button(child=content)
    button.add_css_class("pill")
    if suggested:
        button.add_css_class("suggested-action")
    return button


def _rgba(spec: str, alpha: float | None = None) -> Gdk.RGBA:
    rgba = Gdk.RGBA()
    rgba.parse(spec)
    if alpha is not None:
        rgba.alpha = alpha
    return rgba


class InkGauge(Gtk.Widget):
    """A cartridge drawn as a rounded tank filled to its level with the ink colours."""

    def __init__(self, supply: status.Supply):
        super().__init__(width_request=56, height_request=110, halign=Gtk.Align.CENTER)
        self.supply = supply

    def do_snapshot(self, snapshot: Gtk.Snapshot) -> None:
        width, height = self.get_width(), self.get_height()
        bounds = Graphene.Rect().init(0, 0, width, height)
        outline = Gsk.RoundedRect()
        outline.init_from_rect(bounds, 12)
        fg = self.get_color().to_string()

        snapshot.push_rounded_clip(outline)
        snapshot.append_color(_rgba(fg, 0.08), bounds)
        level = max(self.supply.level, 0) / 100
        colors = self.supply.colors or ("#808080",)
        stripe = width / len(colors)
        for i, spec in enumerate(colors):
            top = height * (1 - level)
            area = Graphene.Rect().init(i * stripe, top, stripe + 0.5, height * level)
            snapshot.append_color(_rgba(spec, 0.9), area)
        snapshot.pop()
        border = _rgba(fg, 0.35)
        snapshot.append_border(outline, [2.0] * 4, [border] * 4)


class Window(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application, runner: Runner):
        super().__init__(application=app, title="LibrePrint", default_width=940, default_height=700)
        self.runner = runner
        self.queues: list[Queue] = []
        self.queue: Queue | None = None
        self.face_down = False  # last known output tray of the selected printer
        self.print_path: str | None = None  # the file chosen
        self.print_doc: str | None = None  # what gets printed: the file or its PDF
        self.scanners: list[str] = []
        self.pages: list[tuple[str, int]] = []  # (png path, dpi)
        self.tmpdir = tempfile.mkdtemp(prefix="libreprint-")
        self._refreshing = False

        self.toasts = Adw.ToastOverlay()
        self.stack = Adw.ViewStack()
        self.toasts.set_child(self.stack)

        header = Adw.HeaderBar()
        switcher = Adw.ViewSwitcher(stack=self.stack, policy=Adw.ViewSwitcherPolicy.WIDE)
        header.set_title_widget(switcher)
        self.queue_menu = Gtk.DropDown(visible=False, tooltip_text="Printer")
        self.queue_menu.connect("notify::selected", self._on_queue_selected)
        header.pack_start(self.queue_menu)
        refresh = Gtk.Button(icon_name="view-refresh-symbolic", tooltip_text="Refresh")
        refresh.connect("clicked", lambda *_: self.refresh())
        menu = Gio.Menu()
        menu.append("About LibrePrint", "app.about")
        header.pack_end(Gtk.MenuButton(icon_name="open-menu-symbolic", menu_model=menu))
        header.pack_end(refresh)

        view = Adw.ToolbarView(content=self.toasts)
        view.add_top_bar(header)
        self.banner = Adw.Banner(button_label="Cancel all", revealed=False)
        self.banner.add_css_class("queue-banner")
        self.banner.connect("button-clicked", self._cancel_all)
        view.add_top_bar(self.banner)
        self.set_content(view)

        self._build_status_page()
        self._build_print_page()
        self._build_scan_page()
        self._build_doctor_page()

        self.connect("close-request", self._on_close)
        self._load_queues()
        self._load_scanners()
        self._jobs: list[status.Job] = []
        self._since_refresh = 0
        GLib.timeout_add_seconds(1, self._tick)

    # --- helpers ----------------------------------------------------------------

    def toast(self, text: str) -> None:
        self.toasts.add_toast(Adw.Toast(title=GLib.markup_escape_text(text), timeout=4))

    def _on_close(self, *_: Any) -> bool:
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        return False

    def _tick(self) -> bool:
        self._since_refresh += 1
        busy_due = bool(self._jobs) and self._since_refresh >= BUSY_REFRESH_SECONDS
        on_status = self.stack.get_visible_child_name() == "status"
        if busy_due or (on_status and self._since_refresh >= REFRESH_SECONDS):
            self.refresh()
        return True

    # --- printer selection -------------------------------------------------------

    def _load_queues(self) -> None:
        def work() -> tuple[list[Queue], str]:
            queues = status.printer_queues(self.runner.run(["lpstat", "-v"]).out)
            default = self.runner.run(["lpstat", "-d"]).out.rpartition(":")[2].strip()
            return queues, default

        def done(result: Any) -> None:
            if isinstance(result, Exception):
                self.toast(f"Cannot read printers: {result}")
                return
            self.queues, default = result
            names = [q.name for q in self.queues]
            self.queue_menu.set_model(Gtk.StringList.new([n.replace("_", " ") for n in names]))
            self.queue_menu.set_visible(len(names) > 1)
            if names:
                self.queue_menu.set_selected(names.index(default) if default in names else 0)
                self._on_queue_selected()
            else:
                self.status_stack.set_visible_child_name("empty")

        _background(work, done)

    def _on_queue_selected(self, *_: Any) -> None:
        index = self.queue_menu.get_selected()
        if 0 <= index < len(self.queues):
            self.queue = self.queues[index]
            self.face_down = False
            self.refresh()

    # --- status page -------------------------------------------------------------

    def _build_status_page(self) -> None:
        self.status_stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.status_stack.add_named(
            Adw.StatusPage(
                icon_name="printer-symbolic",
                title="No printer configured",
                description="Run “sudo libreprint setup” to add your printer.",
            ),
            "empty",
        )
        spinner = _spinner(48)
        spinner.set_halign(Gtk.Align.CENTER)
        self.status_stack.add_named(spinner, "loading")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        box.set_margin_top(32)
        box.set_margin_bottom(32)
        box.set_margin_start(16)
        box.set_margin_end(16)

        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        icon = Gtk.Image(icon_name="printer-symbolic", pixel_size=96, css_classes=["dim-label"])
        hero.append(icon)
        self.model_label = Gtk.Label(
            css_classes=["title-1"], wrap=True, justify=Gtk.Justification.CENTER
        )
        hero.append(self.model_label)
        self.state_label = Gtk.Label(halign=Gtk.Align.CENTER, css_classes=["status-pill"])
        hero.append(self.state_label)
        self.reason_label = Gtk.Label(css_classes=["dim-label"], wrap=True, visible=False)
        hero.append(self.reason_label)
        box.append(hero)

        actions = Gtk.Box(spacing=12, halign=Gtk.Align.CENTER)
        test = _pill_button("Print test page", "document-print-symbolic", suggested=True)
        test.connect(
            "clicked", lambda *_: self._submit_print(TEST_PAGE, {"title": status.TEST_PAGE_JOB})
        )
        actions.append(test)
        self.web_button = _pill_button("Printer web page", "web-browser-symbolic")
        self.web_button.connect("clicked", self._open_web)
        actions.append(self.web_button)
        box.append(actions)

        self.jobs_group = Adw.PreferencesGroup(title="Print queue")
        self.cancel_all_button = Gtk.Button(
            child=Adw.ButtonContent(label="Cancel all", icon_name="process-stop-symbolic"),
            css_classes=["destructive-action", "pill", "cancel-job"],
            valign=Gtk.Align.CENTER,
            visible=False,
        )
        self.cancel_all_button.connect("clicked", self._cancel_all)
        self.jobs_group.set_header_suffix(self.cancel_all_button)
        self.jobs_list = _boxed_list(self.jobs_group)
        box.append(self.jobs_group)

        self.ink_group = Adw.PreferencesGroup(
            title="Ink", description="Levels reported by the printer"
        )
        self.ink_box = Gtk.FlowBox(
            selection_mode=Gtk.SelectionMode.NONE,
            homogeneous=True,
            max_children_per_line=4,
            column_spacing=12,
            row_spacing=12,
        )
        self.ink_group.add(self.ink_box)
        box.append(self.ink_group)

        self.details_group = Adw.PreferencesGroup(title="Details")
        self.uri_row = Adw.ActionRow(title="Connection")
        self.queue_row = Adw.ActionRow(title="CUPS queue")
        self.firmware_row = Adw.ActionRow(title="Firmware")
        for row in (self.uri_row, self.queue_row, self.firmware_row):
            row.add_css_class("property")
            self.details_group.add(row)
        box.append(self.details_group)

        clamp = Adw.Clamp(maximum_size=760, child=box)
        self.status_stack.add_named(Gtk.ScrolledWindow(child=clamp, vexpand=True), "status")
        self.status_stack.set_visible_child_name("loading")
        self.stack.add_titled_with_icon(self.status_stack, "status", "Printer", "printer-symbolic")

    def refresh(self) -> None:
        queue = self.queue
        if queue is None or self._refreshing:
            return
        self._refreshing = True
        self._since_refresh = 0

        def work() -> tuple[status.PrinterStatus | None, list[status.Job], str]:
            info = None
            if queue.uri.startswith(("ipp://", "ipps://")):
                info = status.fetch_status(self.runner, queue.uri)
            jobs = status.fetch_jobs(self.runner, queue.name)
            lpstat_p = self.runner.run(["lpstat", "-p", queue.name]).out
            return info, jobs, lpstat_p

        def done(result: Any) -> None:
            self._refreshing = False
            if isinstance(result, Exception):
                self.toast(f"Cannot read printer status: {result}")
                return
            self._show_status(queue, *result)

        _background(work, done)

    def _show_status(
        self, queue: Queue, info: status.PrinterStatus | None, jobs: list[status.Job], lpstat_p: str
    ) -> None:
        self.face_down = info.face_down if info else False
        state = info.state if info else "unknown"
        if info is None and " is idle" in lpstat_p:
            state = "idle"
        elif info is None and "now printing" in lpstat_p:
            state = "processing"
        self.model_label.set_label(info.model if info else queue.name.replace("_", " "))
        for name in _STATE_LABELS:
            self.state_label.remove_css_class(f"state-{name}")
        self.state_label.add_css_class(f"state-{state}")
        self.state_label.set_label(_STATE_LABELS.get(state, state.title()))
        reasons = [r.replace("-", " ") for r in (info.reasons if info else ())]
        detail = (info.message if info else "") or ", ".join(reasons)
        self.reason_label.set_label(detail)
        self.reason_label.set_visible(bool(detail))

        self.web_button.set_visible(status.web_url(queue.uri) is not None)
        self.uri_row.set_subtitle(queue.uri)
        self.queue_row.set_subtitle(queue.name)
        self.firmware_row.set_subtitle((info.firmware if info else "") or "—")

        self.ink_box.remove_all()
        supplies = info.supplies if info else ()
        self.ink_group.set_visible(bool(supplies))
        for supply in supplies:
            card = Gtk.Box(
                orientation=Gtk.Orientation.VERTICAL, spacing=8, css_classes=["card", "ink-card"]
            )
            card.append(InkGauge(supply))
            percent = f"{supply.level}%" if supply.level >= 0 else "?"
            card.append(Gtk.Label(label=percent, css_classes=["title-2"]))
            name = supply.name.capitalize()
            card.append(Gtk.Label(label=name, wrap=True, css_classes=["caption"]))
            if supply.low:
                low = Gtk.Label(label="Low — order soon", css_classes=["caption", "ink-low"])
                card.append(low)
            self.ink_box.append(card)

        self._show_jobs(jobs, printing=state == "processing")

        self.status_stack.set_visible_child_name("status")

    def _show_jobs(self, jobs: list[status.Job], printing: bool) -> None:
        self._jobs = jobs
        count = len(jobs)
        waiting = f"{count} job{'s' if count != 1 else ''}"
        self.jobs_group.set_description(f"{waiting} in the queue" if jobs else None)
        self.cancel_all_button.set_visible(count > 1)
        self.banner.set_title(f"{'Printing' if printing else 'Queued'} — {waiting} in the queue")
        self.banner.set_revealed(bool(jobs))
        if jobs:
            self.jobs_list.add_css_class("queue-active")
        else:
            self.jobs_list.remove_css_class("queue-active")

        self.jobs_list.remove_all()
        if not jobs:
            idle = Adw.ActionRow(title="Nothing printing", subtitle="Jobs you send appear here")
            idle.add_prefix(Gtk.Image(icon_name="emblem-ok-symbolic", css_classes=["dim-label"]))
            self.jobs_list.append(idle)
        for position, job in enumerate(jobs):
            active = printing and position == 0
            row = Adw.ActionRow(
                title=GLib.markup_escape_text(status.job_title(job, active)),
                subtitle=f"{job.user} · {job.submitted}",
            )
            if active:
                row.add_prefix(_spinner())
            else:
                row.add_prefix(Gtk.Image(icon_name="document-print-symbolic"))
            cancel = Gtk.Button(
                child=Adw.ButtonContent(label="Cancel", icon_name="process-stop-symbolic"),
                tooltip_text=f"Cancel {status.job_label(job)}",
                valign=Gtk.Align.CENTER,
                css_classes=["destructive-action", "pill", "cancel-job"],
            )
            cancel.connect("clicked", self._cancel_job, job)
            row.add_suffix(cancel)
            self.jobs_list.append(row)

    def _cancel_all(self, *_: Any) -> None:
        if self.queue is None:
            return
        queue = self.queue.name

        def done(result: Any) -> None:
            ok = not isinstance(result, Exception) and result.ok
            self.toast("Cancelled all jobs" if ok else "Could not cancel the jobs")
            self.refresh()

        _background(lambda: self.runner.run(["cancel", "-a", queue]), done)

    def _open_web(self, *_: Any) -> None:
        url = status.web_url(self.queue.uri) if self.queue else None
        if url:
            Gtk.UriLauncher(uri=url).launch(self, None, None, None)

    def _cancel_job(self, button: Gtk.Button, job: status.Job) -> None:
        button.set_sensitive(False)
        label = status.job_label(job)

        def done(result: Any) -> None:
            ok = not isinstance(result, Exception) and result.ok
            self.toast(f"Cancelled {label}" if ok else f"Could not cancel {label}")
            self.refresh()

        _background(lambda: self.runner.run(["cancel", job.id]), done)

    # --- print page --------------------------------------------------------------

    def _build_print_page(self) -> None:
        page = Adw.PreferencesPage()

        doc = Adw.PreferencesGroup(
            title="Document",
            description="Choose a file or drop it on this page (PDF, images, text, Office documents)",
        )
        self.file_row = Adw.ActionRow(title="No file selected", subtitle="—")
        self.file_row.add_prefix(Gtk.Image(icon_name="text-x-generic-symbolic"))
        self.file_spinner = _spinner()
        self.file_spinner.set_visible(False)
        self.file_row.add_suffix(self.file_spinner)
        self.preview_button = Gtk.Button(label="Preview", valign=Gtk.Align.CENTER, sensitive=False)
        self.preview_button.connect("clicked", self._preview)
        self.file_row.add_suffix(self.preview_button)
        choose = Gtk.Button(label="Choose…", valign=Gtk.Align.CENTER)
        choose.connect("clicked", self._choose_file)
        self.file_row.add_suffix(choose)
        doc.add(self.file_row)
        page.add(doc)

        opts = Adw.PreferencesGroup(title="Options")
        self.copies_row = Adw.SpinRow.new_with_range(1, 99, 1)
        self.copies_row.set_title("Copies")
        self.sides_row = Adw.ComboRow(
            title="Two-sided",
            model=Gtk.StringList.new(["Off", "Long edge (book)", "Short edge (flip)"]),
        )
        self.color_row = Adw.SwitchRow(
            title="Colour", subtitle="Off prints in greyscale", active=True
        )
        self.quality_row = Adw.ComboRow(
            title="Quality", model=Gtk.StringList.new(["Draft", "Normal", "Best"]), selected=1
        )
        self.pages_row = Adw.EntryRow(title="Pages (e.g. 1-3,5 — empty for all)")
        rows = (
            self.copies_row,
            self.sides_row,
            self.color_row,
            self.quality_row,
            self.pages_row,
        )
        for row in rows:
            opts.add(row)
        page.add(opts)

        go = Adw.PreferencesGroup()
        self.print_button = _pill_button("Print", "document-print-symbolic", suggested=True)
        self.print_button.set_halign(Gtk.Align.CENTER)
        self.print_button.set_sensitive(False)
        self.print_button.connect("clicked", self._print_clicked)
        go.add(self.print_button)
        page.add(go)

        drop = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        drop.connect("drop", lambda _t, value, _x, _y: self._set_print_file(value.get_path()))
        drop.connect("enter", lambda *_: page.add_css_class("drop-hover") or Gdk.DragAction.COPY)
        drop.connect("leave", lambda *_: page.remove_css_class("drop-hover"))
        page.add_controller(drop)

        self.stack.add_titled_with_icon(page, "print", "Print", "document-print-symbolic")

    def _choose_file(self, *_: Any) -> None:
        dialog = Gtk.FileDialog(title="Choose a document to print")

        def done(dlg: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
            try:
                file = dlg.open_finish(result)
            except GLib.Error:
                return  # cancelled
            self._set_print_file(file.get_path())

        dialog.open(self, None, done)

    def _set_print_file(self, path: str | None) -> bool:
        if not path or not os.path.isfile(path):
            self.toast("That is not a file that can be printed")
            return False
        how = convert.kind(path)
        if how == "unsupported":
            self.toast("This type of file cannot be printed")
            return False
        self.print_path = path
        self.file_row.set_title(GLib.markup_escape_text(os.path.basename(path)))
        if how == "direct":
            self._document_ready(path)
            return True
        self._document_busy(True)

        def done(result: Any) -> None:
            if path != self.print_path:
                return  # another file was chosen meanwhile
            self._document_busy(False)
            if isinstance(result, Exception):
                self.print_path = None
                self.file_row.set_subtitle(GLib.markup_escape_text(str(result)))
                self.toast(str(result))
                return
            self._document_ready(result)

        _background(lambda: convert.to_pdf(self.runner, path, self.tmpdir), done)
        return True

    def _document_busy(self, busy: bool) -> None:
        self.print_doc = None
        self.file_spinner.set_visible(busy)
        self.preview_button.set_sensitive(False)
        self.print_button.set_sensitive(False)
        if busy:
            self.file_row.set_subtitle("Preparing for printing, this can take a moment…")

    def _document_ready(self, doc: str) -> None:
        self._document_busy(False)
        self.print_doc = doc
        folder = os.path.dirname(self.print_path or "")
        self.file_row.set_subtitle(GLib.markup_escape_text(folder))
        self.preview_button.set_sensitive(True)
        self.print_button.set_sensitive(True)

    def _preview(self, *_: Any) -> None:
        if self.print_doc:
            Gtk.FileLauncher(file=Gio.File.new_for_path(self.print_doc)).launch(
                self, None, None, None
            )

    def _print_clicked(self, *_: Any) -> None:
        if not self.print_path or not self.print_doc:
            return
        options = {
            "copies": int(self.copies_row.get_value()),
            "sides": status.SIDES[self.sides_row.get_selected()],
            "color": self.color_row.get_active(),
            "quality": ("draft", "normal", "best")[self.quality_row.get_selected()],
            "pages": self.pages_row.get_text(),
            "title": os.path.basename(self.print_path),
        }
        self._submit_print(self.print_doc, options)

    def _submit_print(self, path: str, options: dict[str, Any]) -> None:
        if self.queue is None:
            self.toast("No printer configured")
            return
        try:
            argv = status.print_argv(self.queue.name, path, reverse=not self.face_down, **options)
        except ValueError as exc:
            self.toast(str(exc).capitalize())
            return

        def done(result: Any) -> None:
            if isinstance(result, Exception) or not result.ok:
                err = str(result) if isinstance(result, Exception) else result.err.strip()
                self.toast(f"Printing failed: {err or 'unknown error'}")
                return
            self.toast(f"Printing {options.get('title') or os.path.basename(path)}")
            self.refresh()

        _background(lambda: self.runner.run(argv, timeout=120), done)

    # --- scan page ---------------------------------------------------------------

    def _build_scan_page(self) -> None:
        root = Gtk.Box(spacing=0)

        side = Adw.PreferencesPage(width_request=340, hexpand=False)
        group = Adw.PreferencesGroup(title="Scanner")
        self.scanner_row = Adw.ComboRow(title="Device", model=Gtk.StringList.new(["Searching…"]))
        self.resolution_row = Adw.ComboRow(
            title="Resolution",
            model=Gtk.StringList.new([f"{r} dpi" for r in RESOLUTIONS]),
            selected=RESOLUTIONS.index(300),
        )
        modes = Gtk.StringList.new(["Colour", "Greyscale"])
        self.mode_row = Adw.ComboRow(title="Mode", model=modes)
        for row in (self.scanner_row, self.resolution_row, self.mode_row):
            group.add(row)
        side.add(group)

        buttons = Adw.PreferencesGroup()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.scan_button = _pill_button("Scan page", "scanner-symbolic", suggested=True)
        self.scan_button.set_sensitive(False)
        self.scan_button.connect("clicked", self._scan_clicked)
        box.append(self.scan_button)
        self.save_button = _pill_button("Save…", "document-save-symbolic")
        self.save_button.set_sensitive(False)
        self.save_button.connect("clicked", self._save_clicked)
        box.append(self.save_button)
        self.remove_button = _pill_button("Remove page", "user-trash-symbolic")
        self.remove_button.add_css_class("destructive-action")
        self.remove_button.set_sensitive(False)
        self.remove_button.connect("clicked", self._remove_page)
        box.append(self.remove_button)
        buttons.add(box)
        side.add(buttons)
        root.append(side)
        root.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        self.scan_stack = Gtk.Stack(hexpand=True, transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.scan_stack.add_named(
            Adw.StatusPage(
                icon_name="scanner-symbolic",
                title="Ready to scan",
                description="Place the document face down on the glass and press “Scan page”.\n"
                "Scan several pages to save them as one PDF.",
            ),
            "empty",
        )
        busy = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16, valign=Gtk.Align.CENTER)
        busy.append(_spinner(48))
        busy.append(Gtk.Label(label="Scanning…", css_classes=["title-3"]))
        self.scan_stack.add_named(busy, "busy")

        pages = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        pages.set_margin_top(16)
        pages.set_margin_bottom(12)
        self.carousel = Adw.Carousel(vexpand=True, hexpand=True, spacing=24)
        self.carousel.set_overflow(Gtk.Overflow.HIDDEN)
        pages.append(self.carousel)
        pages.append(Adw.CarouselIndicatorDots(carousel=self.carousel))
        self.page_label = Gtk.Label(css_classes=["dim-label", "caption"])
        pages.append(self.page_label)
        self.scan_stack.add_named(pages, "pages")
        root.append(self.scan_stack)

        self.stack.add_titled_with_icon(root, "scan", "Scan", "scanner-symbolic")

    def _load_scanners(self) -> None:
        def done(result: Any) -> None:
            if isinstance(result, Exception) or not result:
                self.scanner_row.set_model(Gtk.StringList.new(["No scanner found"]))
                return
            # sane-airscan first: it is the most reliable backend for network devices
            self.scanners = sorted(result, key=lambda s: (not s.startswith("airscan:"), s))
            labels = [status.scanner_label(s) for s in self.scanners]
            self.scanner_row.set_model(Gtk.StringList.new(labels))
            self.scan_button.set_sensitive(True)

        def work() -> list[str]:
            found = scanning.list_scanners(self.runner)
            return [s for s in found if not s.startswith("v4l:")]

        _background(work, done)

    def _scan_clicked(self, *_: Any) -> None:
        index = self.scanner_row.get_selected()
        if not 0 <= index < len(self.scanners):
            return
        dpi = RESOLUTIONS[self.resolution_row.get_selected()]
        mode = status.SCAN_MODES[self.mode_row.get_selected()]
        name = f"page-{len(self.pages) + 1:03d}-{GLib.get_real_time()}.png"
        out = os.path.join(self.tmpdir, name)
        argv = status.scan_argv(self.scanners[index], out, resolution=dpi, mode=mode)
        self.scan_button.set_sensitive(False)
        self.scan_stack.set_visible_child_name("busy")

        def done(result: Any) -> None:
            self.scan_button.set_sensitive(True)
            if isinstance(result, Exception) or not result.ok or not os.path.exists(out):
                err = str(result) if isinstance(result, Exception) else result.err.strip()
                self.toast(f"Scan failed: {err.splitlines()[-1] if err else 'unknown error'}")
                self._show_pages()
                return
            self.pages.append((out, dpi))
            self._show_pages(select_last=True)

        _background(lambda: status.run_scan(self.runner, argv), done)

    def _show_pages(self, select_last: bool = False) -> None:
        while self.carousel.get_n_pages():
            self.carousel.remove(self.carousel.get_nth_page(0))
        for path, _dpi in self.pages:
            picture = Gtk.Picture.new_for_filename(path)
            picture.set_content_fit(Gtk.ContentFit.CONTAIN)
            picture.set_hexpand(True)
            # a full-width page keeps the neighbouring scan out of view
            page = Gtk.Box(hexpand=True, vexpand=True)
            page.append(picture)
            self.carousel.append(page)
        has_pages = bool(self.pages)
        self.scan_stack.set_visible_child_name("pages" if has_pages else "empty")
        self.save_button.set_sensitive(has_pages)
        self.remove_button.set_sensitive(has_pages)
        n = len(self.pages)
        self.page_label.set_label(f"{n} page{'s' if n != 1 else ''} · saved as PDF keeps them all")
        if select_last and has_pages:
            last = self.carousel.get_nth_page(n - 1)
            GLib.idle_add(lambda: self.carousel.scroll_to(last, True) and False)

    def _current_page(self) -> int:
        return min(round(self.carousel.get_position()), len(self.pages) - 1)

    def _remove_page(self, *_: Any) -> None:
        if self.pages:
            path, _dpi = self.pages.pop(self._current_page())
            if os.path.exists(path):
                os.unlink(path)
            self._show_pages()

    def _save_clicked(self, *_: Any) -> None:
        filters = Gio.ListStore.new(Gtk.FileFilter)
        for name, pattern in (
            ("PDF document (all pages)", "*.pdf"),
            ("PNG image", "*.png"),
            ("JPEG image", "*.jpg"),
        ):
            flt = Gtk.FileFilter(name=name)
            flt.add_pattern(pattern)
            filters.append(flt)
        dialog = Gtk.FileDialog(
            title="Save scan",
            initial_name=f"scan-{GLib.DateTime.new_now_local().format('%Y%m%d-%H%M%S')}.pdf",
            filters=filters,
        )
        documents = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS)
        if documents:
            dialog.set_initial_folder(Gio.File.new_for_path(documents))

        def done(dlg: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
            try:
                target = dlg.save_finish(result).get_path()
            except GLib.Error:
                return  # cancelled
            if target.lower().endswith(".pdf"):
                pages = list(self.pages)
            else:
                pages = [self.pages[self._current_page()]]
            _background(lambda: save_scan(pages, target), lambda res: self._saved(res, target))

        dialog.save(self, None, done)

    def _saved(self, result: Any, target: str) -> None:
        if isinstance(result, Exception):
            self.toast(f"Could not save: {result}")
            return
        name = GLib.markup_escape_text(os.path.basename(target))
        toast = Adw.Toast(title=f"Saved {name}", button_label="Open")
        launcher = Gtk.FileLauncher(file=Gio.File.new_for_path(target))
        toast.connect("button-clicked", lambda *_: launcher.launch(self, None, None, None))
        self.toasts.add_toast(toast)

    # --- diagnostics page --------------------------------------------------------

    def _build_doctor_page(self) -> None:
        page = Adw.PreferencesPage()
        self.checks_group = Adw.PreferencesGroup(
            title="Diagnostics",
            description="Checks the printing system, network discovery and scanner",
        )
        self.doctor_button = Gtk.Button(
            icon_name="view-refresh-symbolic", tooltip_text="Run again", css_classes=["flat"]
        )
        self.doctor_button.connect("clicked", lambda *_: self.run_doctor())
        self.checks_group.set_header_suffix(self.doctor_button)
        self.checks_list = _boxed_list(self.checks_group)
        page.add(self.checks_group)
        self.stack.add_titled_with_icon(page, "doctor", "Diagnostics", "emblem-system-symbolic")
        self.stack.connect("notify::visible-child-name", self._on_page_changed)
        self._doctor_ran = False

    def _on_page_changed(self, *_: Any) -> None:
        if self.stack.get_visible_child_name() == "doctor" and not self._doctor_ran:
            self.run_doctor()

    def run_doctor(self) -> None:
        self._doctor_ran = True
        self.doctor_button.set_sensitive(False)
        self.checks_list.remove_all()
        row = Adw.ActionRow(title="Running checks…", subtitle="Looking for printers on the network")
        row.add_prefix(_spinner())
        self.checks_list.append(row)

        def done(result: Any) -> None:
            self.doctor_button.set_sensitive(True)
            self.checks_list.remove_all()
            if isinstance(result, Exception):
                failed = Adw.ActionRow(title="Diagnostics failed", subtitle=str(result))
                self.checks_list.append(failed)
                return
            for check in result:
                self.checks_list.append(self._check_row(check))

        _background(lambda: doctor.run_checks(self.runner), done)

    def _check_row(self, check: Check) -> Gtk.Widget:
        icon, css = _CHECK_ICONS.get(check.status, _CHECK_ICONS["skip"])
        title = _CHECK_TITLES.get(check.id, check.id.replace("-", " ").capitalize())
        subtitle = GLib.markup_escape_text(check.message)
        if not (check.fix and check.status in ("fail", "warn")):
            row = Adw.ActionRow(title=title, subtitle=subtitle)
            row.add_prefix(Gtk.Image(icon_name=icon, css_classes=[css]))
            return row
        row = Adw.ExpanderRow(title=title, subtitle=subtitle, expanded=True)
        row.add_prefix(Gtk.Image(icon_name=icon, css_classes=[css]))
        fix = Adw.ActionRow(title="Suggested fix", subtitle=GLib.markup_escape_text(check.fix))
        fix.add_css_class("property")
        copy = Gtk.Button(
            icon_name="edit-copy-symbolic",
            tooltip_text="Copy command",
            valign=Gtk.Align.CENTER,
            css_classes=["flat"],
        )
        copy.connect("clicked", self._copy_fix, check.fix)
        fix.add_suffix(copy)
        row.add_row(fix)
        return row

    def _copy_fix(self, _button: Gtk.Button, command: str) -> None:
        self.get_clipboard().set(command)
        self.toast("Command copied")


def save_scan(pages: list[tuple[str, int]], target: str) -> None:
    """Write scanned PNG pages to ``target``: one multi-page PDF, or the first page as PNG/JPEG."""
    lower = target.lower()
    if lower.endswith(".pdf"):
        import cairo

        pdf = None
        for path, dpi in pages:
            image = cairo.ImageSurface.create_from_png(path)
            width, height = image.get_width() * 72 / dpi, image.get_height() * 72 / dpi
            if pdf is None:
                pdf = cairo.PDFSurface(target, width, height)
            else:
                pdf.set_size(width, height)
            ctx = cairo.Context(pdf)
            ctx.scale(72 / dpi, 72 / dpi)
            ctx.set_source_surface(image, 0, 0)
            ctx.paint()
            pdf.show_page()
        if pdf is not None:
            pdf.finish()
    elif lower.endswith((".jpg", ".jpeg")):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(pages[0][0])
        pixbuf.savev(target, "jpeg", ["quality"], ["92"])
    else:
        shutil.copyfile(pages[0][0], target)


class App(Adw.Application):
    def __init__(self, runner: Runner):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.runner = runner
        self.connect("activate", self._on_activate)

    def _on_activate(self, app: Adw.Application) -> None:
        window = self.get_active_window()
        if window is None:
            css = Gtk.CssProvider()
            css.load_from_string(_CSS)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            window = Window(app, self.runner)
            about = Gio.SimpleAction(name="about")
            about.connect(
                "activate",
                lambda *_: Adw.AboutDialog(
                    application_name="LibrePrint",
                    version=__version__,
                    comments="Set up and use any printer on Linux.",
                    license_type=Gtk.License.GPL_2_0,
                ).present(window),
            )
            self.add_action(about)
        window.present()


def main(runner: Runner | None = None) -> int:
    return App(runner if runner is not None else Runner()).run([])
