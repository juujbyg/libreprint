# SPDX-License-Identifier: GPL-2.0-or-later
"""Turn documents CUPS cannot print, such as Office files, into PDF with LibreOffice."""

from __future__ import annotations

import os
import shutil
import tempfile
import threading

from libreprint.runner import Runner

# CUPS prints these itself, as well as anything that reads as plain text
DIRECT = {".pdf", ".ps", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".gif", ".bmp"}
# fmt: off
CONVERTIBLE = {
    ".doc", ".docx", ".odt", ".rtf", ".wpd", ".pages",
    ".xls", ".xlsx", ".ods", ".csv", ".tsv", ".numbers",
    ".ppt", ".pptx", ".odp", ".key",
    ".odg", ".vsd", ".svg", ".webp",
    ".html", ".htm", ".epub",
}
# fmt: on
_SNAP_OFFICE = "/snap/bin/libreoffice"
_SNAP_DATA = "~/snap/libreoffice/common"  # the snap cannot read /tmp or hidden folders
_CONVERT_TIMEOUT = 180

_lock = threading.Lock()  # instances sharing a profile hand their work to the first one


class ConvertError(Exception):
    pass


def kind(path: str) -> str:
    """How a file gets printed: ``direct``, ``convert`` or ``unsupported``."""
    ext = os.path.splitext(path)[1].lower()
    if ext in DIRECT:
        return "direct"
    if ext in CONVERTIBLE:
        return "convert"
    try:
        with open(path, "rb") as file:
            return "unsupported" if b"\0" in file.read(8192) else "direct"
    except OSError:
        return "unsupported"


def _offices(runner: Runner) -> list[tuple[str, str]]:
    """LibreOffice commands to try, each with a folder it is able to work in."""
    found = []
    if runner.which("soffice"):
        found.append(("soffice", os.path.expanduser("~/.cache/libreprint")))
    if runner.which(_SNAP_OFFICE):
        found.append((_SNAP_OFFICE, os.path.join(os.path.expanduser(_SNAP_DATA), "libreprint")))
    return found


def _convert(runner: Runner, office: str, base: str, path: str, outdir: str) -> str | None:
    os.makedirs(base, exist_ok=True)
    work = tempfile.mkdtemp(prefix="convert-", dir=base)
    try:
        # A plain name keeps LibreOffice from reading # or % in the original as URL syntax
        source = os.path.join(work, "document" + os.path.splitext(path)[1].lower())
        shutil.copyfile(path, source)
        # Its own profile, so this also works while LibreOffice is open
        profile = "-env:UserInstallation=file://" + os.path.join(base, "profile")
        argv = [office, profile, "--headless", "--norestore", "--convert-to", "pdf"]
        runner.run([*argv, "--outdir", work, source], timeout=_CONVERT_TIMEOUT)
        made = os.path.join(work, "document.pdf")
        if not os.path.isfile(made):
            return None
        stem = os.path.splitext(os.path.basename(path))[0]
        target = os.path.join(tempfile.mkdtemp(prefix="print-", dir=outdir), stem + ".pdf")
        shutil.move(made, target)
        return target
    finally:
        shutil.rmtree(work, ignore_errors=True)


def to_pdf(runner: Runner, path: str, outdir: str) -> str:
    """Path of a PDF made from ``path`` inside ``outdir``."""
    offices = _offices(runner)
    if not offices:
        raise ConvertError("Install LibreOffice to print this type of file")
    with _lock:
        # Ubuntu's soffice can be libreoffice-core alone, which opens nothing: try the next one
        for office, base in offices:
            pdf = _convert(runner, office, base, path, outdir)
            if pdf:
                return pdf
    raise ConvertError("LibreOffice could not open this file")
