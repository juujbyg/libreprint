# SPDX-License-Identifier: GPL-2.0-or-later
"""Subprocess and filesystem access behind an injectable Runner."""

from __future__ import annotations

import os
import posixpath
import shutil
import subprocess
import time
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class Result:
    code: int
    out: str = ""
    err: str = ""

    @property
    def ok(self) -> bool:
        return self.code == 0


def _env() -> dict[str, str]:
    return {**os.environ, "LC_ALL": "C", "DEBIAN_FRONTEND": "noninteractive"}


class Runner:
    """Real implementation: runs commands and touches the filesystem."""

    def run(self, argv: list[str], *, input: str | None = None, timeout: float = 60) -> Result:
        try:
            proc = subprocess.run(
                argv,
                input=input,
                check=False,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=timeout,
                env=_env(),
            )
        except FileNotFoundError:
            return Result(127, "", f"{argv[0]}: command not found")
        except subprocess.TimeoutExpired:
            return Result(124, "", "timeout")
        return Result(proc.returncode, proc.stdout or "", proc.stderr or "")

    def run_interactive(self, argv: list[str]) -> int:
        try:
            return subprocess.run(argv, check=False, env=_env()).returncode
        except FileNotFoundError:
            return 127

    def stream(self, argv: list[str]) -> Iterator[str]:
        try:
            proc = subprocess.Popen(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                errors="replace",
                env=_env(),
            )
        except FileNotFoundError:
            return
        assert proc.stdout is not None
        try:
            for line in proc.stdout:
                yield line.rstrip("\n")
        finally:
            proc.stdout.close()
            if proc.poll() is None:
                proc.terminate()
            proc.wait()

    def which(self, name: str) -> str | None:
        return shutil.which(name)

    def read_file(self, path: str) -> str | None:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                return fh.read()
        except OSError:
            return None

    def write_file(self, path: str, content: str) -> None:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)

    def exists(self, path: str) -> bool:
        return os.path.exists(path)

    def listdir(self, path: str) -> list[str]:
        try:
            return sorted(os.listdir(path))
        except OSError:
            return []

    def fetch(self, url: str, timeout: float = 5) -> str | None:
        """Body of an HTTP GET, or ``None`` when the request fails."""
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                return response.read().decode("utf-8", "replace")
        except (OSError, ValueError):
            return None

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


class FakeRunner(Runner):
    """Test double: canned command results and an in-memory filesystem."""

    def __init__(self, files: dict[str, str] | None = None, binaries: set[str] | None = None):
        self.files: dict[str, str] = dict(files or {})
        self.binaries = binaries
        self.calls: list[list[str]] = []
        self.interactive_calls: list[list[str]] = []
        self.inputs: list[str | None] = []
        self.stream_lines: dict[tuple[str, ...], list[str]] = {}
        self.slept: list[float] = []
        self.urls: dict[str, str] = {}
        self._results: dict[tuple[str, ...], Result] = {}
        self._seqs: dict[tuple[str, ...], list[Result]] = {}
        self._seq_pos: dict[tuple[str, ...], int] = {}

    def on(self, *argv: str, out: str = "", err: str = "", code: int = 0) -> FakeRunner:
        self._results[tuple(argv)] = Result(code, out, err)
        return self

    def on_seq(self, *argv: str, results: list[Result]) -> FakeRunner:
        """Return ``results`` in order for successive matching calls; the last one repeats."""
        key = tuple(argv)
        self._seqs[key] = list(results)
        self._seq_pos[key] = 0
        return self

    def _has_binary(self, name: str) -> bool:
        return self.binaries is None or name in self.binaries

    def _lookup(self, argv: list[str]) -> Result:
        key = tuple(argv)
        best: tuple[str, ...] | None = None
        best_is_seq = False
        for table, is_seq in ((self._results, False), (self._seqs, True)):
            for reg in table:
                if key[: len(reg)] != reg:
                    continue
                if best is None or len(reg) > len(best) or (len(reg) == len(best) and is_seq):
                    best, best_is_seq = reg, is_seq
        if best is None:
            return Result(0)
        if not best_is_seq:
            return self._results[best]
        seq = self._seqs[best]
        pos = self._seq_pos[best]
        self._seq_pos[best] = min(pos + 1, len(seq) - 1)
        return seq[pos]

    def run(self, argv: list[str], *, input: str | None = None, timeout: float = 60) -> Result:
        self.calls.append(list(argv))
        self.inputs.append(input)
        if not self._has_binary(argv[0]):
            return Result(127, "", f"{argv[0]}: command not found")
        return self._lookup(argv)

    def run_interactive(self, argv: list[str]) -> int:
        self.interactive_calls.append(list(argv))
        self.calls.append(list(argv))
        if not self._has_binary(argv[0]):
            return 127
        return self._lookup(argv).code

    def stream(self, argv: list[str]) -> Iterator[str]:
        yield from self.stream_lines.get(tuple(argv), [])

    def which(self, name: str) -> str | None:
        return f"/usr/bin/{name}" if self._has_binary(name) else None

    def read_file(self, path: str) -> str | None:
        return self.files.get(path)

    def write_file(self, path: str, content: str) -> None:
        self.files[path] = content

    def exists(self, path: str) -> bool:
        return path in self.files or any(k.startswith(path.rstrip("/") + "/") for k in self.files)

    def listdir(self, path: str) -> list[str]:
        base = path.rstrip("/")
        return sorted(posixpath.basename(k) for k in self.files if posixpath.dirname(k) == base)

    def fetch(self, url: str, timeout: float = 5) -> str | None:
        return self.urls.get(url)

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
