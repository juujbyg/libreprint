# SPDX-License-Identifier: GPL-2.0-or-later
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


def test_print_argv_in_order():
    assert "outputorder=reverse" not in status.print_argv("Q", "a.pdf", reverse=False)


def test_print_argv_rejects_bad_input():
    with pytest.raises(ValueError):
        status.print_argv("Q", "a.pdf", pages="1;rm")
    with pytest.raises(ValueError):
        status.print_argv("Q", "a.pdf", sides="both")


def test_scan_argv():
    argv = status.scan_argv("airscan:e0:HP", "/tmp/p.png", resolution=600, mode="Gray")
    assert argv[:3] == ["scanimage", "-d", "airscan:e0:HP"]
    assert "600" in argv and "Gray" in argv and argv[-1] == "/tmp/p.png"


def test_parse_job_id():
    assert status.parse_job_id("request id is HP-56 (1 file(s))\n") == "HP-56"


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
