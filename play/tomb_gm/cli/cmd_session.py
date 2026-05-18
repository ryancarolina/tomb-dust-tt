from __future__ import annotations

import argparse

from tomb_gm.cli.cmd_core import _ctx, log_event
from tomb_gm.cli.context import CommandContext
from tomb_gm.domain import session as session_domain


def register(sub: argparse._SubParsersAction) -> None:
    session = sub.add_parser("session", help="Session lifecycle")
    sess_sub = session.add_subparsers(dest="session_command", required=True)

    p_start = sess_sub.add_parser("start", help="Start a new play session")
    p_start.add_argument("--campaign", required=True, dest="campaign")
    p_start.set_defaults(handler=handle_session_start)

    p_resume = sess_sub.add_parser("resume", help="Resume an open session")
    p_resume.add_argument("--campaign", default=None, dest="campaign")
    p_resume.set_defaults(handler=handle_session_resume)

    sess_sub.add_parser("end", help="End the active session").set_defaults(handler=handle_session_end)


def handle_session_start(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    result = session_domain.start_session(ctx.conn, ctx.config, args.campaign)
    if result.get("ok"):
        log_event(
            ctx.conn,
            result["session_id"],
            "session.started",
            {
                "campaign_slug": result["campaign_slug"],
                "phase": result["phase"],
                "address": result["address"],
            },
        )
    return result


def handle_session_resume(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    result = session_domain.resume_session(ctx.conn, ctx.config, args.campaign)
    if result.get("ok"):
        log_event(
            ctx.conn,
            result["session_id"],
            "session.resumed",
            {"campaign_slug": result["campaign_slug"]},
        )
    return result


def handle_session_end(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    session_id = None
    campaign_slug = None
    active = session_domain.read_active(ctx.config)
    if active:
        session_id = active.get("session_id")
        if session_id:
            row = ctx.conn.execute(
                "SELECT campaign_slug FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
            if row:
                campaign_slug = row["campaign_slug"]
    result = session_domain.end_session(ctx.conn, ctx.config)
    if result.get("ok"):
        log_event(
            ctx.conn,
            result["session_id"],
            "session.ended",
            {"campaign_slug": result["campaign_slug"], "ended_at": result["ended_at"]},
        )
        if session_id and campaign_slug:
            from tomb_gm.services.memory import compact_session

            compact = compact_session(ctx.conn, session_id, campaign_slug)
            result["memory_compact"] = compact
    return result


from tomb_gm.cli.registry import add_command_module

add_command_module(register)
