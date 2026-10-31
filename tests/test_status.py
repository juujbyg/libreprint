# SPDX-License-Identifier: GPL-2.0-or-later
from dataclasses import replace

import pytest
from conftest import fixture

from libreprint import status
from libreprint.runner import FakeRunner, Result


def test_parse_status_supplies():
    st = status.parse_status(fixture("ipptool_status.txt"))
    assert st is not None
    assert st.model == "HP ENVY 6000 series"
    assert st.state == "idle"
    assert st.reasons == ()
    assert st.firmware == "VASBYTPP2N001.2628C.00"
    tri, black = st.supplies
    assert tri.colors == ("#00FFFF", "#FF00FF", "#FFFF00")
    assert (tri.level, tri.low) == (20, False)
    assert black.colors == ("#000000",)
    assert (black.level, black.low) == (5, True)


def test_parse_status_unreachable():
    assert status.parse_status("") is None


def test_printer_queues_skips_implicitclass():
    out = (
        "device for HP_ENVY: ipps://HP1.local:631/ipp/print\n"
        "device for HP_ENVY_27647F: implicitclass://HP_ENVY_27647F/\n"
    )
    assert [q.name for q in status.printer_queues(out)] == ["HP_ENVY"]


def test_parse_jobs():
    out = "HP_ENVY_6000_series-55  juan  1024   Thu 29 Oct 2026 11:19:56 AM EDT\n"
    (job,) = status.parse_jobs(out)
    assert job.id == "HP_ENVY_6000_series-55"
    assert job.user == "juan"
    assert job.size == 1024


def test_web_url():
    assert status.web_url("ipps://HP1.local:631/ipp/print") == "https://hp1.local/"
    assert status.web_url("ipp://localhost:60000/ipp/print") is None
    assert status.web_url("hp:/net/envy?ip=1.2.3.4") is None


def test_print_argv():
    argv = status.print_argv(
        "Q", "/tmp/a.pdf", copies=2, sides="two-sided-long-edge", color=False, pages="1-3, 5"
    )
    assert argv == [
        "lp", "-d", "Q", "-n", "2",
        "-o", "sides=two-sided-long-edge",
        "-o", "print-color-mode=monochrome",
        "-o", "print-quality=4",
        "-o", "page-ranges=1-3,5",
        "-o", "outputorder=reverse",
        "--", "/tmp/a.pdf",
    ]  # fmt: skip


def test_print_argv_order():
    assert "outputorder=reverse" in status.print_argv("Q", "a.pdf")
    assert "outputorder=reverse" not in status.print_argv("Q", "a.pdf", reverse=False)


def ipp_out(*lines):
    return "\n".join(("    printer-make-and-model (text) = Acme 1", *lines)) + "\n"


def test_face_up_and_unknown_trays_print_last_page_first():
    face_up = ipp_out(
        "    output-bin-default (keyword) = face-up",
        "    printer-output-tray (octetString) = stackingorder=unknown;pagedelivery=faceUp;name=T1",
    )
    assert status.parse_status(face_up).face_down is False
    assert status.parse_status(ipp_out()).face_down is False


def test_face_down_trays_are_detected():
    by_bin = ipp_out("    output-bin-default (keyword) = face-down")
    by_tray = ipp_out(
        "    output-bin-default (keyword) = top",
        "    printer-output-tray (octetString) = pagedelivery=faceDown;name=T1",
    )
    assert status.parse_status(by_bin).face_down is True
    assert status.parse_status(by_tray).face_down is True


def test_stack_order_puts_the_first_document_on_top():
    assert status.stack_order(["a", "b", "c"], face_down=True) == ["a", "b", "c"]
    assert status.stack_order(["a", "b", "c"], face_down=False) == ["c", "b", "a"]


def test_print_argv_rejects_bad_input():
    with pytest.raises(ValueError):
        status.print_argv("Q", "a.pdf", pages="1;rm")
    with pytest.raises(ValueError):
        status.print_argv("Q", "a.pdf", sides="both")


def test_scan_argv():
    argv = status.scan_argv("airscan:e0:HP", "/tmp/p.png", resolution=600, mode="Gray")
    assert argv[:3] == ["scanimage", "-d", "airscan:e0:HP"]
    assert "600" in argv and "Gray" in argv and argv[-1] == "/tmp/p.png"


def test_job_label():
    job = status.Job("HP-56", "juan", 1024, "now")
    assert status.job_label(job) == "job 56"
    assert status.job_label(replace(job, name="Report.pdf")) == "Report.pdf"


def test_job_title():
    job = status.Job("HP-56", "juan", 1024, "now")
    assert status.job_title(job, active=True) == "Job 56 · Printing now"
    assert status.job_title(job, active=False) == "Job 56 · Waiting"
    named = replace(job, name="Report.pdf")
    assert status.job_title(named, active=True) == "Printing Report.pdf"
    assert status.job_title(named, active=False) == "Report.pdf · Waiting"
    test_page = replace(job, name=status.TEST_PAGE_JOB)
    assert status.job_title(test_page, active=True) == "Printing test page"
    assert status.job_title(test_page, active=False) == "Test page · Waiting"


def test_print_argv_title():
    argv = status.print_argv("HP", "/tmp/a.pdf", title="test page")
    assert argv[-4:] == ["-t", "test page", "--", "/tmp/a.pdf"]


def test_parse_job_names():
    out = 'job-id,job-name\n74,"Bills, A&B <2026>.txt"\n75,\n'
    assert status.parse_job_names(out) == {"74": "Bills, A&B <2026>.txt"}


def test_fetch_jobs_adds_names():
    runner = FakeRunner()
    runner.on("lpstat", "-o", "HP", out="HP-55 juan 1024 Mon\nHP-56 juan 2048 Tue\n")
    uri = "ipp://localhost/printers/HP"
    runner.on("ipptool", "-T", "10", "-c", uri, "/dev/stdin", out="job-id,job-name\n56,a.pdf\n")
    assert [j.name for j in status.fetch_jobs(runner, "HP")] == ["", "a.pdf"]


def test_fetch_jobs_without_ipptool_keeps_jobs():
    runner = FakeRunner()
    runner.on("lpstat", "-o", "HP", out="HP-55 juan 1024 Mon\n")
    runner.on("ipptool", "-T", "10", "-c", "ipp://localhost/printers/HP", "/dev/stdin", code=1)
    assert [j.id for j in status.fetch_jobs(runner, "HP")] == ["HP-55"]


def test_scanner_label():
    assert status.scanner_label("airscan:e0:HP ENVY 6000 series [27647F]") == (
        "HP ENVY 6000 series (eSCL)"
    )
    assert status.scanner_label("hpaio:/net/envy_6000_series?ip=10.0.0.2") == (
        "HP Envy 6000 Series (HPLIP)"
    )


def test_run_scan_retries_failed_open():
    runner = FakeRunner().on_seq(
        "scanimage",
        results=[Result(1, "", "scanimage: open of device x failed: Invalid argument"), Result(0)],
    )
    assert status.run_scan(runner, ["scanimage", "-d", "x"]).ok
    assert len(runner.calls) == 2


def test_run_scan_does_not_retry_other_errors():
    runner = FakeRunner().on("scanimage", code=1, err="scanimage: out of paper")
    assert not status.run_scan(runner, ["scanimage"]).ok
    assert len(runner.calls) == 1
