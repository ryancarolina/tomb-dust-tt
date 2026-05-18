from __future__ import annotations

import argparse
import json

from tomb_gm.cli.cmd_core import _ctx
from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module
from tomb_gm.services.beat import process_beat


def register(sub: argparse._SubParsersAction) -> None:
    beat = sub.add_parser("beat", help="Process one table beat from player actions")
    beat.add_argument(
        "--actions",
        required=True,
        help='JSON: {"lines":[{"slot":1,"raw":"..."}]}',
    )
    beat.set_defaults(handler=handle_beat)


def handle_beat(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    try:
        actions = json.loads(args.actions)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"invalid JSON for --actions: {exc}"}
    if not isinstance(actions, dict):
        return {"ok": False, "error": "--actions must be a JSON object"}
    try:
        return process_beat(ctx, actions)
    except ValueError as exc:
        code = str(exc)
        return {
            "ok": False,
            "error": code,
            "message": "Start or resume a session before beat",
        }


add_command_module(register)
