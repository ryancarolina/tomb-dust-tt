from __future__ import annotations

import argparse
import json

from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect
from tomb_gm.services.memory import build_recap, compact_session, recall_facts, remember_fact


def register(sub: argparse._SubParsersAction) -> None:
    mem = sub.add_parser("memory", help="Episodic and semantic memory")
    sub_mem = mem.add_subparsers(dest="memory_cmd", required=True)

    p_remember = sub_mem.add_parser("remember", help="Pin a semantic fact")
    p_remember.add_argument("--fact", required=True, help="Fact text to store")
    p_remember.add_argument(
        "--entities",
        nargs="*",
        default=[],
        help="Related entity names or ids (space-separated or comma-separated)",
    )
    p_remember.add_argument("--address", default=None, help="AV-GRID address tie-in")
    p_remember.add_argument("--importance", type=int, default=3, help="Importance 1-5")
    p_remember.set_defaults(handler=handle_remember)

    p_recall = sub_mem.add_parser("recall", help="Ranked semantic recall for a query")
    p_recall.add_argument("--query", required=True, help="Recall query")
    p_recall.add_argument("--top", type=int, default=5, help="Max results")
    p_recall.set_defaults(handler=handle_recall)

    sub_mem.add_parser("recap", help="Session and campaign recap for the agent").set_defaults(
        handler=handle_recap
    )
    sub_mem.add_parser("compact", help="Template scene summary from recent events").set_defaults(
        handler=handle_compact
    )


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    return CommandContext(config=cfg, conn=conn)


def _read_active(cfg) -> dict | None:
    if not cfg.active_path.exists():
        return None
    return json.loads(cfg.active_path.read_text(encoding="utf-8"))


def _resolve_play(
    ctx: CommandContext, _args: argparse.Namespace
) -> tuple[str | None, str | None, dict | None]:
    active = _read_active(ctx.config)
    session_id = active.get("session_id") if active else None
    campaign_slug = active.get("campaign_slug") if active else None
    if session_id and not campaign_slug:
        row = ctx.conn.execute(
            "SELECT campaign_slug FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if row:
            campaign_slug = row["campaign_slug"]
    if campaign_slug and not session_id:
        row = ctx.conn.execute(
            "SELECT id FROM sessions WHERE campaign_slug = ? AND ended_at IS NULL "
            "ORDER BY started_at DESC LIMIT 1",
            (campaign_slug,),
        ).fetchone()
        if row:
            session_id = row["id"]
    party = None
    if session_id:
        row = ctx.conn.execute(
            "SELECT address, phase, mode FROM party_state WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if row:
            party = {"address": row["address"], "phase": row["phase"], "mode": row["mode"]}
    return session_id, campaign_slug, party


def _parse_entities(raw: list[str]) -> list[str]:
    out: list[str] = []
    for item in raw:
        for part in item.split(","):
            part = part.strip()
            if part:
                out.append(part)
    return out


def handle_remember(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    session_id, campaign_slug, _party = _resolve_play(ctx, args)
    if not campaign_slug:
        return {"ok": False, "error": "No active campaign; start or resume a session first"}
    entities = _parse_entities(args.entities or [])
    memory_id = remember_fact(
        ctx.conn,
        campaign_slug,
        args.fact,
        entities=entities,
        address=args.address,
        importance=args.importance,
        session_id=session_id,
    )
    return {
        "ok": True,
        "memory_id": memory_id,
        "campaign_slug": campaign_slug,
        "session_id": session_id,
        "fact": args.fact,
        "entities": entities,
    }


def handle_recall(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    _session_id, campaign_slug, _party = _resolve_play(ctx, args)
    if not campaign_slug:
        return {"ok": False, "error": "No active campaign; start or resume a session first"}
    results = recall_facts(ctx.conn, campaign_slug, args.query, top=args.top)
    return {
        "ok": True,
        "campaign_slug": campaign_slug,
        "query": args.query,
        "results": results,
    }


def handle_recap(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    session_id, campaign_slug, party = _resolve_play(ctx, args)
    if not campaign_slug:
        return {"ok": False, "error": "No active campaign; start or resume a session first"}
    recap = build_recap(
        ctx.conn,
        campaign_slug=campaign_slug,
        session_id=session_id,
        party=party,
    )
    return {"ok": True, **recap}


def handle_compact(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    session_id, campaign_slug, _party = _resolve_play(ctx, args)
    if not session_id or not campaign_slug:
        return {"ok": False, "error": "Active session required for memory compact"}
    result = compact_session(ctx.conn, session_id, campaign_slug)
    return {"ok": True, "session_id": session_id, "campaign_slug": campaign_slug, **result}


add_command_module(register)
