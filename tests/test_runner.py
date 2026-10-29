# SPDX-License-Identifier: GPL-2.0-or-later
import sys

from libreprint.runner import FakeRunner, Result, Runner


def test_runner_forces_c_locale():
    out = Runner().run([sys.executable, "-c", "import os;print(os.environ['LC_ALL'])"]).out
    assert out.strip() == "C"


def test_runner_missing_binary():
    assert Runner().run(["definitely-not-a-binary-xyz"]).code == 127


def test_runner_input_and_exit_code():
    res = Runner().run(
        [sys.executable, "-c", "import sys;d=sys.stdin.read();print(d.upper());sys.exit(3)"],
        input="ab",
    )
    assert res.out.strip() == "AB"
    assert res.code == 3
    assert res.ok is False


def test_runner_file_roundtrip(tmp_path):
    r = Runner()
    target = str(tmp_path / "a" / "b.txt")
    r.write_file(target, "x")
    assert r.read_file(target) == "x"
    assert r.read_file(str(tmp_path / "missing")) is None
    assert r.listdir(str(tmp_path / "missing")) == []


def test_fake_runner_prefix_matching():
    r = FakeRunner().on("lpstat", out="A").on("lpstat", "-v", out="B")
    assert r.run(["lpstat", "-v"]).out == "B"
    assert r.run(["lpstat", "-p"]).out == "A"
    assert r.run(["other"]).code == 0
    assert len(r.calls) == 3


def test_fake_runner_binaries():
    r = FakeRunner(binaries={"lpstat"})
    assert r.run(["avahi-browse"]).code == 127
    assert r.which("avahi-browse") is None
    assert r.which("lpstat") == "/usr/bin/lpstat"


def test_fake_runner_on_seq_last_repeats():
    r = FakeRunner().on_seq("x", results=[Result(1), Result(0, "ok")])
    assert [r.run(["x"]).code for _ in range(3)] == [1, 0, 0]


def test_fake_runner_listdir_and_write_file():
    r = FakeRunner(files={"/etc/d/a": "1", "/etc/d/b": "2", "/etc/d/sub/c": "3", "/etc/x": "4"})
    r.write_file("/etc/d/z", "5")
    assert r.listdir("/etc/d") == ["a", "b", "z"]
    assert r.listdir("/nope") == []
    assert r.exists("/etc/d/a")
    assert r.exists("/etc/d/sub")
