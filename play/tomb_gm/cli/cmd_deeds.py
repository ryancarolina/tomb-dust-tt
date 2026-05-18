from __future__ import annotations

import argparse
import json

from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect
from tomb_gm.domain.deeds import deeds_check
from tomb_gm.services.economy import get_account_state


def register(sub: argparse._SubParsersAction) -> None:
    deeds = sub.add_parser("deeds", help="Deed promotions")
    actions = deeds.add_subparsers(dest="deeds_action", required=True)
    check = actions.add_parser("check", help="List eligible promotions")
    check.add_argument("--campaign", required=True)
    check.add_argument("--character", required=True, dest="character_id")
    check.set_defaults(handler=handle_check)


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    cfg = load_config(ws)
    return CommandContext(config=cfg, conn=connect(cfg.db_path))


def handle_check(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    row = ctx.conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (args.character_id, args.campaign),
    ).fetchone()
    if not row:
        return {"ok": False, "error": f"Character not found: {args.character_id}"}
    sheet = json.loads(row["sheet_json"])
    account = get_account_state(ctx.conn, args.campaign)
    return deeds_check(ctx.config.content_root, sheet=sheet, account_state=account)


add_command_module(register)
