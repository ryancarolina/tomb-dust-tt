from __future__ import annotations

import argparse
import json

from tomb_gm.cli.cmd_core import log_event
from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect
from tomb_gm.services.content import ContentService
from tomb_gm.services.encounters import wilderness_travel_roll
from tomb_gm.services.rag.search import search_rules
from tomb_gm.services.world import WorldService


def register(sub: argparse._SubParsersAction) -> None:
    world = sub.add_parser("world", help="AV-GRID travel and exploration")
    actions = world.add_subparsers(dest="world_action", required=True)

    actions.add_parser("where", help="Current party cell").set_defaults(handler=handle_where)
    actions.add_parser("exits", help="Legal travel targets").set_defaults(handler=handle_exits)

    travel = actions.add_parser("travel", help="Move party to an address")
    travel.add_argument("--to", dest="to_address", required=True, metavar="ADDRESS")
    travel.add_argument(
        "--roll-wilderness",
        action="store_true",
        help="If wilderness travel, run encounters roll immediately",
    )
    travel.set_defaults(handler=handle_travel)

    describe = actions.add_parser("describe", help="Cell + location doc excerpt")
    describe.set_defaults(handler=handle_describe)

    search = actions.add_parser("search", help="List cells in a region")
    search.add_argument("--region", required=True)
    search.set_defaults(handler=handle_search)


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    return CommandContext(config=cfg, conn=conn)


def _read_active(cfg) -> dict | None:
    if not cfg.active_path.exists():
        return None
    return json.loads(cfg.active_path.read_text(encoding="utf-8"))


def _party_row(ctx: CommandContext, session_id: str):
    return ctx.conn.execute(
        "SELECT address, mode, stamp_json FROM party_state WHERE session_id = ?",
        (session_id,),
    ).fetchone()


def _require_session(ctx: CommandContext) -> tuple[str, dict] | tuple[None, dict]:
    active = _read_active(ctx.config)
    if not active or not active.get("session_id"):
        return None, {
            "ok": False,
            "error": "NO_ACTIVE_SESSION",
            "message": "Start or resume a session before world commands",
        }
    session_id = active["session_id"]
    row = ctx.conn.execute(
        "SELECT id, ended_at FROM sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    if not row or row["ended_at"] is not None:
        return None, {
            "ok": False,
            "error": "NO_ACTIVE_SESSION",
            "message": "Active session is missing or ended",
        }
    party = _party_row(ctx, session_id)
    if not party:
        return None, {
            "ok": False,
            "error": "NO_PARTY_STATE",
            "message": "Party state missing for session",
        }
    return session_id, {}


def handle_where(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    session_id, err = _require_session(ctx)
    if session_id is None:
        return err
    party = _party_row(ctx, session_id)
    content = ContentService(ctx.config.content_root)
    world = WorldService(content)
    payload = world.where_payload(
        party["address"],
        mode=party["mode"],
        stamp_json=party["stamp_json"],
    )
    if payload is None:
        return world.unknown_address_error(party["address"])
    return {"ok": True, **payload}


def handle_exits(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    session_id, err = _require_session(ctx)
    if session_id is None:
        return err
    party = _party_row(ctx, session_id)
    content = ContentService(ctx.config.content_root)
    world = WorldService(content)
    address = party["address"]
    exits = world.legal_exits(address)
    if exits is None:
        return world.unknown_address_error(address)
    return {
        "ok": True,
        "address": address,
        "exits": [{"address": e, "cell": content.cell_payload(e)} for e in exits],
    }


def handle_travel(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    session_id, err = _require_session(ctx)
    if session_id is None:
        return err
    party = _party_row(ctx, session_id)
    from_address = party["address"]
    to_address = args.to_address.strip()

    content = ContentService(ctx.config.content_root)
    world = WorldService(content)

    if not content.get_cell(to_address):
        return world.unknown_address_error(to_address)

    ok, code = world.can_travel(from_address, to_address)
    if not ok:
        return {
            "ok": False,
            "error": code,
            "from": from_address,
            "to": to_address,
            "exits": world.legal_exits(from_address) or [],
        }

    wilderness = world.wilderness_travel_needed(to_address, party["stamp_json"])
    ctx.conn.execute(
        "UPDATE party_state SET address = ? WHERE session_id = ?",
        (to_address, session_id),
    )
    ctx.conn.commit()

    log_event(
        ctx.conn,
        session_id,
        "world_travel",
        {
            "from": from_address,
            "to": to_address,
            "wilderness_roll_pending": wilderness,
        },
    )

    cell = content.cell_payload(to_address)
    out = {
        "ok": True,
        "from": from_address,
        "to": to_address,
        "address": to_address,
        "cell": cell,
        "wilderness_roll_pending": wilderness,
        "stamp": world.stamp_validity(to_address, party["stamp_json"]),
    }
    if wilderness and getattr(args, "roll_wilderness", False):
        import random

        rng = random.Random(getattr(args, "seed", None))
        enc = wilderness_travel_roll(
            ctx.config.content_root,
            biomes=cell.get("biomes") or ["HL"],
            danger=cell.get("dangerRating") or "skirmisher",
            rng=rng,
        )
        out["wilderness_encounter"] = enc
        log_event(ctx.conn, session_id, "encounter.wilderness", enc)
    return out


def handle_describe(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    session_id, err = _require_session(ctx)
    if session_id is None:
        return err
    party = _party_row(ctx, session_id)
    content = ContentService(ctx.config.content_root)
    world = WorldService(content)
    payload = world.where_payload(
        party["address"], mode=party["mode"], stamp_json=party["stamp_json"]
    )
    if payload is None:
        return world.unknown_address_error(party["address"])
    cell = payload.get("cell") or {}
    name = cell.get("displayName") or party["address"]
    excerpts = search_rules(ctx.conn, ctx.config.content_root, name, max_results=3)
    return {"ok": True, **payload, "location_excerpts": excerpts}


def handle_search(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    content = ContentService(ctx.config.content_root)
    cells = content.search_cells_by_region(args.region)
    return {"ok": True, "region": args.region, "cells": cells}


add_command_module(register)
