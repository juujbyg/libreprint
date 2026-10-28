# SPDX-License-Identifier: GPL-2.0-or-later
"""Entry point for ``python -m hpeasy``."""


def _run() -> int:
    from hpeasy.cli import main

    return main()


if __name__ == "__main__":
    raise SystemExit(_run())
