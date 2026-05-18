from __future__ import annotations

import argparse

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
    buy.set_defaults(handler=handle_buy)

    sell = actions.add_parser("sell", help="Sell item from pack")
    sell.add_argument("--campaign", required=True)
    sell.add_argument("--character", required=True, dest="character_id")
    sell.add_argument("--item", required=True)
    sell.add_argument("--price", type=int, default=None)
    sell.set_defaults(handler=handle_sell)

    stash = actions.add_parser("stash", help="Account stash")
    stash_sub = stash.add_subparsers(dest="stash_action", required=True)
    dep = stash_sub.add_parser("deposit")
    dep.add_argument("--campaign", required=True)
    dep.add_argument("--character", required=True, dest="character_id")
    dep.add_argument("--gold", type=int, required=True)
    dep.set_defaults(handler=handle_stash_deposit)
    wit = stash_sub.add_parser("withdraw")
    wit.add_argument("--campaign", required=True)
    wit.add_argument("--character", required=True, dest="character_id")
    wit.add_argument("--gold", type=int, required=True)
    wit.set_defaults(handler=handle_stash_withdraw)
    show_st = stash_sub.add_parser("show")
    show_st.add_argument("--campaign", required=True)
    show_st.set_defaults(handler=handle_stash_show)

    death = actions.add_parser("death", help="Mark character dead; optional inherit stash")
    death.add_argument("--campaign", required=True)
    death.add_argument("--character", required=True, dest="character_id")
    death.add_argument("--inherit", default=None, dest="inherit_id")
    death.set_defaults(handler=handle_death)


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    return CommandContext(config=load_config(ws), conn=connect(load_config(ws).db_path))


def handle_buy(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    try:
        return econ.buy_item(
            ctx.conn,
            ContentService(ctx.config.content_root),
            campaign_slug=args.campaign,
            character_id=args.character_id,
            item_id=args.item,
            quantity=args.qty,
        )
    except econ.EconomyError as exc:
        return {"ok": False, "error": str(exc)}


def handle_sell(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    try:
        return econ.sell_item(
            ctx.conn,
            campaign_slug=args.campaign,
            character_id=args.character_id,
            item_id=args.item,
            price_gp=args.price,
        )
    except econ.EconomyError as exc:
        return {"ok": False, "error": str(exc)}


def handle_stash_deposit(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    try:
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
        state = econ.get_account_state(ctx.conn, args.campaign)
        return {"ok": True, "campaign": args.campaign, "stash": state}
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
