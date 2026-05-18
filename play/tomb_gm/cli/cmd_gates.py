from __future__ import annotations

import argparse
import json

from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect
from tomb_gm.domain import gates as gates_domain


def register(sub: argparse._SubParsersAction) -> None:
    gate = sub.add_parser("gate", help="Human approval gates")
    actions = gate.add_subparsers(dest="gate_action", required=True)
    open_p = actions.add_parser("open", help="Open a gate")
    open_p.add_argument("--type", required=True, dest="gate_type")
    open_p.add_argument("--payload", default="{}")
    open_p.set_defaults(handler=handle_open)
    resolve_p = actions.add_parser("resolve", help="Approve or reject gate")
    resolve_p.add_argument("--id", required=True, dest="gate_id")
    resolve_p.add_argument("--approve", action="store_true")
    resolve_p.add_argument("--reject", action="store_true")
    resolve_p.set_defaults(handler=handle_resolve)
    actions.add_parser("pending", help="Show pending gate").set_defaults(handler=handle_pending)


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    cfg = load_config(ws)
    return CommandContext(config=cfg, conn=connect(cfg.db_path))


def _session_id(ctx: CommandContext) -> str | None:
    if not ctx.config.active_path.exists():
        return None
    return json.loads(ctx.config.active_path.read_text(encoding="utf-8")).get("session_id")


def handle_open(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    session_id = _session_id(ctx)
    if not session_id:
        return {"ok": False, "error": "NO_ACTIVE_SESSION"}
    try:
        payload = json.loads(args.payload)
        result = gates_domain.open_gate(
            ctx.conn, session_id=session_id, gate_type=args.gate_type, payload=payload
        )
        return {"ok": True, **result}
    except (ValueError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc)}


def handle_resolve(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    if args.approve == args.reject:
        return {"ok": False, "error": "Specify exactly one of --approve or --reject"}
    try:
        return gates_domain.resolve_gate(ctx.conn, gate_id=args.gate_id, approve=args.approve)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}


def handle_pending(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    session_id = _session_id(ctx)
    if not session_id:
        return {"ok": False, "error": "NO_ACTIVE_SESSION"}
    pending = gates_domain.pending_gate(ctx.conn, session_id)
    return {"ok": True, "pending": pending}


add_command_module(register)
