# SPDX-License-Identifier: GPL-2.0-or-later
"""User interaction: console prompts and the silent auto-mode UI."""

from __future__ import annotations

import sys
from typing import Protocol


class UI(Protocol):
    interactive: bool

    def info(self, msg: str) -> None: ...

    def warn(self, msg: str) -> None: ...

    def confirm(self, question: str, default: bool = True) -> bool: ...

    def choose(self, title: str, items: list[str]) -> list[int]: ...


class ConsoleUI:
    def __init__(self, assume_yes: bool = False, stream=None, stdin=None):
        self.assume_yes = assume_yes
        self.stream = stream if stream is not None else sys.stderr
        self.stdin = stdin if stdin is not None else sys.stdin
        isatty = getattr(self.stdin, "isatty", None)
        self.interactive = bool(isatty and isatty()) and not assume_yes

    def _say(self, msg: str) -> None:
        print(msg, file=self.stream, flush=True)

    def _ask(self, prompt: str) -> str | None:
        """Prompt and read one line; None on end of input."""
        print(prompt, end="", file=self.stream, flush=True)
        line = self.stdin.readline()
        return line.strip() if line else None

    def info(self, msg: str) -> None:
        self._say(msg)

    def warn(self, msg: str) -> None:
        self._say(f"warning: {msg}")

    def confirm(self, question: str, default: bool = True) -> bool:
        if self.assume_yes:
            return True
        if not self.interactive:
            return default
        answer = self._ask(f"{question} [{'Y/n' if default else 'y/N'}] ")
        if answer is None or not answer:
            return default
        if answer.lower() in ("y", "yes"):
            return True
        if answer.lower() in ("n", "no"):
            return False
        return default

    def choose(self, title: str, items: list[str]) -> list[int]:
        everything = list(range(len(items)))
        if not self.interactive:
            return everything
        self._say(title)
        for number, item in enumerate(items, 1):
            self._say(f"  {number}) {item}")
        while True:
            answer = self._ask("Select (e.g. 1,3; 'a' or Enter for all): ")
            if answer is None or answer == "" or answer.lower() == "a":
                return everything
            picks = [tok for tok in answer.replace(",", " ").split() if tok]
            if all(tok.isdigit() and 1 <= int(tok) <= len(items) for tok in picks):
                return sorted({int(tok) - 1 for tok in picks})
            self._say("Invalid selection.")


class AutoUI:
    interactive = False

    def info(self, msg: str) -> None:
        print(f"hpeasy: {msg}", flush=True)

    def warn(self, msg: str) -> None:
        print(f"hpeasy: warning: {msg}", flush=True)

    def confirm(self, question: str, default: bool = True) -> bool:
        return False

    def choose(self, title: str, items: list[str]) -> list[int]:
        return list(range(len(items)))
