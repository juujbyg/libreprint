# Contributing to LibrePrint

Thanks for helping. LibrePrint is pure Python (standard library only at runtime) and targets
Ubuntu 22.04 / 24.04 / 26.04 and Debian 12 / 13.

## Setup

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install pytest ruff
python -m pytest -q
ruff check src tests
```

## Ground rules

- Python >= 3.10, standard library only. No `tomllib`, `ExceptionGroup` or `typing.Self`.
- Every source file starts with `# SPDX-License-Identifier: GPL-2.0-or-later`.
- Every external command and every file access goes through the injectable `Runner`
  (`src/libreprint/runner.py`). Tests use `FakeRunner` with real recorded command output in
  `tests/fixtures/`; tests never run system commands or touch the real filesystem.
- Commands run with `LC_ALL=C`, so parsers can assume English output.
- Never redistribute HP's plugin. Never modify or delete a queue LibrePrint did not create (except
  with `--force`).
- User-facing messages are in English.
- Shell scripts and unit files use LF line endings (enforced by `.gitattributes`).

## Layout

`src/libreprint/decide.py` is a pure function (device in, plan out); `setup.py` executes plans;
`doctor.py` holds the diagnostics; `cli.py` is the argparse entry point. The app (`libreprint gui`)
is `gui.py` (GTK 4 + libadwaita, imported only by that command); its logic lives in `status.py`,
which is tested without GTK. System files are in `data/`, packaging in `packaging/`, README
screenshots in `docs/screenshots/` (made from demo data, never a real printer).

## Packaging and integration tests

`bash packaging/build-deb.sh` builds `dist/libreprint_<version>_all.deb` (needs `dpkg-deb`). The CI
workflow installs it in Ubuntu and Debian containers and runs `tests/integration/run.sh`, which
starts `cupsd` and a fake HP printer (`ippeveprinter`) and checks that `libreprint setup` creates a
working queue.

## Adding a fixture

Capture the real output (for example `LC_ALL=C lpinfo -l -v` or `avahi-browse -a -r -p -t`) and
remove serial numbers and IP addresses you do not want public. Add it to `tests/fixtures/` and
write a test that parses it.

## Reporting hardware results

Add a row to [docs/HARDWARE.md](docs/HARDWARE.md) in the same pull request or issue.
