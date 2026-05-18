from __future__ import annotations

from collections.abc import Callable

# Each cmd_*.py appends its register(subparsers) function at import time.
COMMAND_REGISTRARS: list[Callable] = []


def add_command_module(register_fn: Callable) -> None:
    COMMAND_REGISTRARS.append(register_fn)
