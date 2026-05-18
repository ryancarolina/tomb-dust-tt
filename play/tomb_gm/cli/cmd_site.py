from __future__ import annotations

import argparse

from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect
from tomb_gm.services import site as site_svc


def register(sub: argparse._SubParsersAction) -> None:
    site = sub.add_parser("site", help="Navigate site graphs")
    site_sub = site.add_subparsers(dest="site_cmd", required=True)

    enter_p = site_sub.add_parser("enter", help="Enter a site at its entry node")
    enter_p.add_argument("--id", dest="site_id", required=True, help="Site slug")
    enter_p.set_defaults(handler=handle_site_enter)

    site_sub.add_parser("where", help="Current site node").set_defaults(handler=handle_site_where)
    site_sub.add_parser("exits", help="Available edges from current node").set_defaults(
        handler=handle_site_exits
    )

    move_p = site_sub.add_parser("move", help="Traverse an edge to another node")
    move_p.add_argument("--to", dest="to_node", required=True, help="Target node id")
    move_p.set_defaults(handler=handle_site_move)

    search_p = site_sub.add_parser("search", help="Investigation roll at current node")
    search_p.add_argument("--dc", type=int, default=13)
    search_p.add_argument("--mod", type=int, default=0, help="Skill/ability modifier")
    search_p.set_defaults(handler=handle_site_search)


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    cfg = load_config(ws)
    return CommandContext(config=cfg, conn=connect(cfg.db_path))


def handle_site_enter(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    return site_svc.enter_site(_ctx(args), args.site_id)


def handle_site_where(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    return site_svc.where_site(_ctx(args))


def handle_site_exits(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    return site_svc.exits_site(_ctx(args))


def handle_site_move(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    return site_svc.move_site(_ctx(args), args.to_node)


def handle_site_search(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    try:
        return site_svc.search_site(
            _ctx(args),
            dc=args.dc,
            skill_mod=args.mod,
            seed=args.seed,
        )
    except site_svc.SiteError as exc:
        return {"ok": False, "error": str(exc)}


add_command_module(register)
