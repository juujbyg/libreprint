# SPDX-License-Identifier: GPL-2.0-or-later
import os

import pytest

from libreprint import convert
from libreprint.runner import FakeRunner, Result


class OfficeRunner(FakeRunner):
    """soffice stand-in: only the commands in ``working`` produce a PDF."""

    def __init__(self, binaries, working=()):
        super().__init__(binaries=set(binaries))
        self.working = set(working)

    def run(self, argv, *, input=None, timeout=60):
        self.calls.append(list(argv))
        if argv[0] in self.working:
            with open(os.path.join(argv[argv.index("--outdir") + 1], "document.pdf"), "w") as f:
                f.write("%PDF")
        return Result(0, "", "")


@pytest.fixture
def doc(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    path = tmp_path / "Q3 #1 100%.docx"
    path.write_text("office")
    return str(path)


@pytest.mark.parametrize(
    ("name", "content", "expected"),
    [
        ("a.pdf", b"%PDF", "direct"),
        ("a.JPG", b"\xff\xd8\0", "direct"),
        ("notes.md", b"# hello", "direct"),
        ("README", b"hello", "direct"),
        ("a.docx", b"PK\0", "convert"),
        ("a.XLSX", b"PK\0", "convert"),
        ("a.bin", b"\0\1\2", "unsupported"),
    ],
)
def test_kind(tmp_path, name, content, expected):
    path = tmp_path / name
    path.write_bytes(content)
    assert convert.kind(str(path)) == expected


def test_to_pdf_keeps_the_document_name(doc, tmp_path):
    runner = OfficeRunner({"soffice"}, working={"soffice"})
    pdf = convert.to_pdf(runner, doc, str(tmp_path))
    assert os.path.basename(pdf) == "Q3 #1 100%.pdf"
    assert os.path.isfile(pdf)


def test_to_pdf_gives_libreoffice_a_plain_name_in_its_own_profile(doc, tmp_path):
    runner = OfficeRunner({"soffice"}, working={"soffice"})
    convert.to_pdf(runner, doc, str(tmp_path))
    argv = runner.calls[0]
    assert os.path.basename(argv[-1]) == "document.docx"
    assert argv[1].startswith("-env:UserInstallation=file://")


def test_to_pdf_falls_back_to_the_snap(doc, tmp_path):
    snap = "/snap/bin/libreoffice"
    runner = OfficeRunner({"soffice", snap}, working={snap})
    convert.to_pdf(runner, doc, str(tmp_path))
    assert [call[0] for call in runner.calls] == ["soffice", snap]
    assert "/snap/libreoffice/common/" in runner.calls[1][-1]


def test_to_pdf_without_libreoffice(doc, tmp_path):
    with pytest.raises(convert.ConvertError, match="Install LibreOffice"):
        convert.to_pdf(OfficeRunner(set()), doc, str(tmp_path))


def test_to_pdf_when_nothing_opens_the_file(doc, tmp_path):
    with pytest.raises(convert.ConvertError, match="could not open"):
        convert.to_pdf(OfficeRunner({"soffice"}), doc, str(tmp_path))


def test_to_pdf_leaves_no_work_folders(doc, tmp_path):
    runner = OfficeRunner({"soffice"}, working={"soffice"})
    convert.to_pdf(runner, doc, str(tmp_path))
    assert os.listdir(tmp_path / "home/.cache/libreprint") == []
