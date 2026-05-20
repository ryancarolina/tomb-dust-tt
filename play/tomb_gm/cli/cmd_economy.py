from __future__ import annotations

import argparse
import json

from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect
from tomb_gm.services.content import ContentService
from tomb_gm.services import economy as econ


def register(sub: argparse._SubParsersAction) -> None:
    economy = sub.add_parser("economy", help="Buy, sell, stash")
    actions = economy.add_subparsers(dest="economy_action", required=True)

    buy = actions.add_parser("buy", help="Buy item for character")
    buy.add_argument("--campaign", required=True)
    buy.add_argument("--character", required=True, dest="character_id")
    buy.add_argument("--item", required=True)
    buy.add_argument("--qty", type=int, default=1)
    buy.add_argument("--vendor", default=None, dest="vendor_id")
    buy.add_argument("--session", default=None, dest="session_id")
    buy.set_defaults(handler=handle_buy)

    sell = actions.add_parser("sell", help="Sell item from pack by instanceId")
    sell.add_argument("--campaign", required=True)
    sell.add_argument("--character", required=True, dest="character_id")
    sell.add_argument("--instance", required=True, dest="instance_id")
    sell.add_argument("--quantity", type=int, default=None)
    sell.add_argument("--vendor", default=None, dest="vendor_id")
    sell.add_argument("--session", default=None, dest="session_id")
    sell.set_defaults(handler=handle_sell)

    stash = actions.add_parser("stash", help="Account stash")
    stash_sub = stash.add_subparsers(dest="stash_action", required=True)
    dep = stash_sub.add_parser("deposit")
    dep.add_argument("--campaign", required=True)
    dep.add_argument("--character", required=True, dest="character_id")
    dep.add_argument("--gold", type=int, default=0)
    dep.add_argument("--instance", default=None, dest="instance_id")
    dep.add_argument("--quantity", type=int, default=None)
    dep.add_argument("--session", default=None, dest="session_id")
    dep.set_defaults(handler=handle_stash_deposit)
    wit = stash_sub.add_parser("withdraw")
    wit.add_argument("--campaign", required=True)
    wit.add_argument("--character", required=True, dest="character_id")
    wit.add_argument("--gold", type=int, default=0)
    wit.add_argument("--instance", default=None, dest="instance_id")
    wit.add_argument("--quantity", type=int, default=None)
    wit.add_argument("--session", default=None, dest="session_id")
    wit.set_defaults(handler=handle_stash_withdraw)
    show_st = stash_sub.add_parser("show")
    show_st.add_argument("--campaign", required=True)
    show_st.set_defaults(handler=handle_stash_show)

    death = actions.add_parser("death", help="Mark character dead (corpse via process_delver_death)")
    death.add_argument("--campaign", required=True)
    death.add_argument("--character", required=True, dest="character_id")
    death.add_argument("--inherit", default=None, dest="inherit_id")
    death.set_defaults(handler=handle_death)


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    return CommandContext(config=load_config(ws), conn=connect(load_config(ws).db_path))


def _session_id(ctx: CommandContext, args: argparse.Namespace) -> str:
    if getattr(args, "session_id", None):
        return args.session_id
    if not ctx.config.active_path.exists():
        raise econ.EconomyError("no active session — pass --session")
    data = json.loads(ctx.config.active_path.read_text(encoding="utf-8"))
    sid = data.get("session_id")
    if not sid:
        raise econ.EconomyError("no active session — pass --session")
    return sid


def handle_buy(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    try:
        session_id = _session_id(ctx, args) if args.vendor_id else None
        return econ.buy_item(
            ctx.conn,
            ContentService(ctx.config.content_root),
            campaign_slug=args.campaign,
            character_id=args.character_id,
            item_id=args.item,
            quantity=args.qty,
            session_id=session_id,
            vendor_id=args.vendor_id,
        )
    except econ.EconomyError as exc:
        return {"ok": False, "error": str(exc)}


def handle_sell(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    try:
        return econ.sell_item(
            ctx.conn,
            ContentService(ctx.config.content_root),
            campaign_slug=args.campaign,
            session_id=_session_id(ctx, args),
            character_id=args.character_id,
            instance_id=args.instance_id,
            quantity=args.quantity,
            vendor_id=args.vendor_id,
        )
    except econ.EconomyError as exc:
        return {"ok": False, "error": str(exc)}


def handle_stash_deposit(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    try:
        if args.instance_id:
            return econ.stash_deposit_item(
                ctx.conn,
                ContentService(ctx.config.content_root),
                campaign_slug=args.campaign,
                session_id=_session_id(ctx, args),
                character_id=args.character_id,
                instance_id=args.instance_id,
                quantity=args.quantity,
            )
        return econ.stash_deposit(
            ctx.conn,
            campaign_slug=args.campaign,
            character_id=args.character_id,
            gold_gp=args.gold,
        )
    except econ.EconomyError as exc:
        return {"ok": False, "error": str(exc)}


def handle_stash_withdraw(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    try:
        if args.instance_id:
            return econ.stash_withdraw_item(
                ctx.conn,
                ContentService(ctx.config.content_root),
                campaign_slug=args.campaign,
                session_id=_session_id(ctx, args),
                character_id=args.character_id,
                instance_id=args.instance_id,
                quantity=args.quantity,
            )
        if args.gold <= 0:
            raise econ.EconomyError("--gold required for gold withdraw")
        return econ.stash_withdraw(
            ctx.conn,
            campaign_slug=args.campaign,
            character_id=args.character_id,
            gold_gp=args.gold,
        )
    except econ.EconomyError as exc:
        return {"ok": False, "error": str(exc)}


def handle_stash_show(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    try:
        return econ.list_stash(ctx.conn, args.campaign)
    except econ.EconomyError as exc:
        return {"ok": False, "error": str(exc)}


def handle_death(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    try:
        return econ.mark_character_dead(
            ctx.conn,
            campaign_slug=args.campaign,
            character_id=args.character_id,
            inherit_character_id=args.inherit_id,
        )
    except econ.EconomyError as exc:
        return {"ok": False, "error": str(exc)}


add_command_module(register)
