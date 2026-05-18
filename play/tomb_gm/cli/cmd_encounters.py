from __future__ import annotations

import argparse
import json
import random

from tomb_gm.cli.cmd_core import log_event
from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect
from tomb_gm.services.content import ContentService
from tomb_gm.services.encounters import wilderness_travel_roll


def register(sub: argparse._SubParsersAction) -> None:
    enc = sub.add_parser("encounters", help="Encounter tables")
    actions = enc.add_subparsers(dest="encounters_action", required=True)
    roll = actions.add_parser("roll", help="Roll wilderness travel encounter")
    roll.add_argument("--biome", default=None, help="Biome code (default from party cell)")
    roll.add_argument("--danger", default=None, help="Danger tier override")
    roll.set_defaults(handler=handle_roll)


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    cfg = load_config(ws)
    return CommandContext(config=cfg, conn=connect(cfg.db_path))


def _session_party(ctx: CommandContext) -> tuple[str, dict] | tuple[None, dict]:
    if not ctx.config.active_path.exists():
        return None, {"ok": False, "error": "NO_ACTIVE_SESSION"}
    active = json.loads(ctx.config.active_path.read_text(encoding="utf-8"))
    session_id = active.get("session_id")
    if not session_id:
        return None, {"ok": False, "error": "NO_ACTIVE_SESSION"}
    row = ctx.conn.execute(
        "SELECT address, stamp_json FROM party_state WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if not row:
        return None, {"ok": False, "error": "NO_PARTY_STATE"}
    return session_id, {"address": row["address"]}


def handle_roll(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    session_id, party = _session_party(ctx)
    if session_id is None:
        return party
    content = ContentService(ctx.config.content_root)
    cell = content.cell_payload(party["address"]) or {}
    biomes = [args.biome] if args.biome else (cell.get("biomes") or ["HL"])
    danger = args.danger or cell.get("dangerRating") or "skirmisher"
    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    result = wilderness_travel_roll(
        ctx.config.content_root,
        biomes=biomes,
        danger=danger,
        rng=rng,
    )
    if result.get("ok"):
        log_event(ctx.conn, session_id, "encounter.wilderness", result)
    return result


add_command_module(register)
