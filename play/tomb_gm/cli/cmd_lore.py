from __future__ import annotations

import argparse

from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect
from tomb_gm.services.rag.lore import index_lore, search_lore


def register(sub: argparse._SubParsersAction) -> None:
    lore = sub.add_parser("lore", help="Search setting lore (locations, factions, NPCs)")
    lore_sub = lore.add_subparsers(dest="lore_cmd", required=True)

    p_search = lore_sub.add_parser("search", help="Search lore by keyword")
    p_search.add_argument("query", help="Search terms")
    p_search.add_argument("--max", type=int, default=5, help="Maximum results")
    p_search.set_defaults(handler=handle_search)

    p_index = lore_sub.add_parser("index", help="Rebuild lore search index slice")
    p_index.set_defaults(handler=handle_index)


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    return CommandContext(config=cfg, conn=conn)


def handle_search(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    results = search_lore(
        ctx.conn,
        ctx.config.content_root,
        args.query,
        max_results=args.max,
    )
    return {"ok": True, "query": args.query, "results": results}


def handle_index(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    stats = index_lore(ctx.conn, ctx.config.content_root)
    return {"ok": True, **stats}


add_command_module(register)
