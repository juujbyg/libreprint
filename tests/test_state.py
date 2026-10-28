# SPDX-License-Identifier: GPL-2.0-or-later
import pytest

from hpeasy import state
from hpeasy.runner import FakeRunner
from hpeasy.state import Config, State
from hpeasy.ui import AutoUI, ConsoleUI


class FakeStdin:
    def __init__(self, tty, text=""):
        self._tty = tty
        self._lines = text.splitlines(keepends=True)

    def isatty(self):
        return self._tty

    def readline(self):
        return self._lines.pop(0) if self._lines else ""


def test_state_roundtrip():
    r = FakeRunner()
    st = State(queues={"HP_A": "LaserJet A"}, pending_plugin=["LaserJet P1102"])
    state.save_state(r, st)
    assert state.load_state(r) == st
    assert r.files[state.STATE_PATH].index('"pending_plugin"') < r.files[state.STATE_PATH].index(
        '"queues"'
    )


def test_state_missing_is_empty():
    assert state.load_state(FakeRunner()) == State()


def test_state_corrupt_json():
    assert state.load_state(FakeRunner(files={state.STATE_PATH: "{not json"})) == State()
    assert state.load_state(FakeRunner(files={state.STATE_PATH: "[1, 2]"})) == State()


def test_state_instances_do_not_share_defaults():
    a, b = State(), State()
    a.queues["x"] = "y"
    assert b.queues == {}


def test_config_defaults_and_invalid():
    assert state.load_config(FakeRunner()) == Config()
    text = "[hpeasy]\nnetwork = maybe\naccept_hp_plugin_license = yes\nusb = bogus\n"
    cfg = state.load_config(FakeRunner(files={state.CONFIG_PATH: text}))
    assert cfg.network == "add"
    assert cfg.accept_hp_plugin_license is True
    assert cfg.usb is True
    assert cfg.install_packages is True


def test_config_values():
    text = "[hpeasy]\nnetwork = off\nusb = false\ninstall_packages = no\n"
    cfg = state.load_config(FakeRunner(files={state.CONFIG_PATH: text}))
    assert cfg == Config(usb=False, network="off", install_packages=False)


def test_config_garbage_file():
    assert state.load_config(FakeRunner(files={state.CONFIG_PATH: "no sections"})) == Config()


def test_lock_is_exclusive(tmp_path):
    fcntl = pytest.importorskip("fcntl")
    path = str(tmp_path / "hpeasy.lock")
    with state.lock(path), open(path, "a+") as other, pytest.raises(BlockingIOError):
        fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
    with open(path, "a+") as again:
        fcntl.flock(again, fcntl.LOCK_EX | fcntl.LOCK_NB)  # released after the with block


def test_console_ui_assume_yes():
    ui = ConsoleUI(assume_yes=True, stdin=FakeStdin(True))
    assert ui.interactive is False
    assert ui.confirm("Go?", default=False) is True


def test_console_ui_non_tty_uses_default():
    ui = ConsoleUI(stdin=FakeStdin(False))
    assert ui.interactive is False
    assert ui.confirm("Go?", default=True) is True
    assert ui.confirm("Go?", default=False) is False
    assert ui.choose("Pick", ["a", "b"]) == [0, 1]


def test_console_ui_interactive_answers(capsys):
    ui = ConsoleUI(stdin=FakeStdin(True, "n\n\ny\n"))
    assert ui.interactive is True
    assert ui.confirm("One?", default=True) is False
    assert ui.confirm("Two?", default=True) is True
    assert ui.confirm("Three?", default=False) is True


def test_console_ui_choose():
    ui = ConsoleUI(stdin=FakeStdin(True, "2\n"))
    assert ui.choose("Pick", ["a", "b", "c"]) == [1]
    ui = ConsoleUI(stdin=FakeStdin(True, "a\n"))
    assert ui.choose("Pick", ["a", "b", "c"]) == [0, 1, 2]
    ui = ConsoleUI(stdin=FakeStdin(True, "\n"))
    assert ui.choose("Pick", ["a", "b"]) == [0, 1]
    ui = ConsoleUI(stdin=FakeStdin(True, "1, 3\n"))
    assert ui.choose("Pick", ["a", "b", "c"]) == [0, 2]


def test_auto_ui(capsys):
    ui = AutoUI()
    assert ui.interactive is False
    assert ui.confirm("Go?") is False
    assert ui.choose("Pick", ["a", "b"]) == [0, 1]
    ui.info("hello")
    assert capsys.readouterr().out.startswith("hpeasy: hello")
