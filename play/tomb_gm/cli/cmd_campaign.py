from __future__ import annotations

import argparse

from tomb_gm.cli.cmd_core import _ctx, log_event
from tomb_gm.cli.context import CommandContext
from tomb_gm.domain import campaign as campaign_domain


def register(sub: argparse._SubParsersAction) -> None:
    campaign = sub.add_parser("campaign", help="Campaign management")
    camp_sub = campaign.add_subparsers(dest="campaign_command", required=True)

    p_new = camp_sub.add_parser("new", help="Create a new campaign")
    p_new.add_argument("--slug", required=True)
    p_new.add_argument("--name", required=True)
    p_new.set_defaults(handler=handle_campaign_new)

    camp_sub.add_parser("list", help="List campaigns").set_defaults(handler=handle_campaign_list)

    p_show = camp_sub.add_parser("show", help="Show campaign metadata")
    p_show.add_argument("--slug", required=True)
    p_show.set_defaults(handler=handle_campaign_show)


def handle_campaign_new(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    result = campaign_domain.create_campaign(ctx.conn, ctx.config, args.slug, args.name)
    if result.get("ok"):
        log_event(
            ctx.conn,
            None,
            "campaign.created",
            {"slug": args.slug, "display_name": args.name},
        )
    return result


def handle_campaign_list(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    return campaign_domain.list_campaigns(ctx.conn)


def handle_campaign_show(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    return campaign_domain.show_campaign(ctx.conn, args.slug)


from tomb_gm.cli.registry import add_command_module

add_command_module(register)
