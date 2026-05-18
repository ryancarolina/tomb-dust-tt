from __future__ import annotations

import argparse
from collections.abc import Callable

from tomb_gm.config import resolve_workspace

Handler = Callable[[argparse.Namespace, object], dict]


def _autoload_command_modules() -> None:
    import importlib
    import pkgutil

    import tomb_gm.cli as cli_pkg

    for mod in pkgutil.iter_modules(cli_pkg.__path__, cli_pkg.__name__ + "."):
        if mod.name.rsplit(".", 1)[-1].startswith("cmd_") and not mod.name.endswith("cmd_core"):
            importlib.import_module(mod.name)


def build_parser() -> argparse.ArgumentParser:
    _autoload_command_modules()
    parser = argparse.ArgumentParser(prog="tomb_gm")
    parser.add_argument(
        "--workspace",
        default=None,
        help="Play workspace path (default: play/workspace)",
    )
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for tests")
    sub = parser.add_subparsers(dest="command", required=True)

    _register_builtin(sub)
    from tomb_gm.cli.registry import COMMAND_REGISTRARS

    for reg in COMMAND_REGISTRARS:
        reg(sub)
    return parser


def _register_builtin(sub: argparse._SubParsersAction) -> None:
    from tomb_gm.cli import cmd_core  # noqa: WPS433

    cmd_core.register(sub)
