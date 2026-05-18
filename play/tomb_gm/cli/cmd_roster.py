from __future__ import annotations

import argparse

from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect
from tomb_gm.domain.character import (
    CharacterError,
    clear_roster_slot,
    roster_summary,
    set_roster_slot,
)


def register(sub: argparse._SubParsersAction) -> None:
    roster = sub.add_parser("roster", help="Party slot bindings (1-4)")
    roster_sub = roster.add_subparsers(dest="roster_command", required=True)

    set_p = roster_sub.add_parser("set", help="Bind a character to a slot")
    set_p.add_argument("--campaign", required=True)
    set_p.add_argument("--slot", type=int, required=True, help="Party slot 1-4")
    set_p.add_argument("--character", required=True, dest="character_id")
    set_p.set_defaults(handler=handle_set)

    show_p = roster_sub.add_parser("show", help="Show bound party roster")
    show_p.add_argument("--campaign", required=True)
    show_p.set_defaults(handler=handle_show)

    clear_p = roster_sub.add_parser("clear", help="Unbind a slot")
    clear_p.add_argument("--campaign", required=True)
    clear_p.add_argument("--slot", type=int, required=True)
    clear_p.set_defaults(handler=handle_clear)


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    return CommandContext(config=cfg, conn=conn)


def handle_set(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    try:
        result = set_roster_slot(
            ctx.conn,
            campaign_slug=args.campaign,
            slot=args.slot,
            character_id=args.character_id,
            max_players=ctx.config.max_players,
        )
    except CharacterError as exc:
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "campaign": args.campaign, **result}


def handle_show(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    party = roster_summary(ctx.conn, campaign_slug=args.campaign)
    return {"ok": True, "campaign": args.campaign, "roster": party}


def handle_clear(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    try:
        result = clear_roster_slot(
            ctx.conn,
            campaign_slug=args.campaign,
            slot=args.slot,
            max_players=ctx.config.max_players,
        )
    except CharacterError as exc:
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "campaign": args.campaign, **result}


add_command_module(register)
