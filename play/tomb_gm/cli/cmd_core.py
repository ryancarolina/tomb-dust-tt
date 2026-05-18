from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.output import emit, fail
from tomb_gm.config import REPO_ROOT, load_config, resolve_workspace
from tomb_gm.db.connection import connect, run_migrations, schema_version
from tomb_gm.suggest import build_suggest


def register(sub: argparse._SubParsersAction) -> None:
    sub.add_parser("init", help="Initialize workspace DB and config").set_defaults(handler=handle_init)
    sub.add_parser("status", help="Session and workspace status").set_defaults(handler=handle_status)
    sub.add_parser("check", help="Validators and blockers").set_defaults(handler=handle_check)
    sub.add_parser("suggest", help="What the agent should do next").set_defaults(handler=handle_suggest)


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    return CommandContext(config=cfg, conn=conn)


def _read_active(cfg) -> dict | None:
    if not cfg.active_path.exists():
        return None
    return json.loads(cfg.active_path.read_text(encoding="utf-8"))


def handle_init(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ws = resolve_workspace(args.workspace)
    cfg = load_config(ws)
    ver = run_migrations(connect(cfg.db_path))
    cfg.campaigns_dir.mkdir(parents=True, exist_ok=True)
    return {
        "ok": True,
        "workspace": str(cfg.workspace),
        "content_root": str(cfg.content_root),
        "db_path": str(cfg.db_path),
        "schema_version": ver,
    }


def handle_status(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    cfg = ctx.config
    active = _read_active(cfg)
    payload: dict = {
        "ok": True,
        "workspace": {"healthy": cfg.content_root.is_dir(), "path": str(cfg.workspace)},
        "content_root": str(cfg.content_root),
        "schema_version": schema_version(ctx.conn),
        "active": None,
        "party": None,
        "roster": [],
        "combat": None,
        "awaiting": "SETUP",
    }
    if not active:
        return payload
    session_id = active.get("session_id")
    row = ctx.conn.execute(
        "SELECT s.*, p.address, p.mode, p.site_id, p.site_node_id, p.phase, p.clocks_json, p.gold_in_transit "
        "FROM sessions s "
        "LEFT JOIN party_state p ON p.session_id = s.id "
        "WHERE s.id = ?",
        (session_id,),
    ).fetchone()
    if not row:
        payload["active"] = active
        payload["awaiting"] = "SETUP"
        return payload
    payload["active"] = {
        **active,
        "campaign_slug": row["campaign_slug"],
        "phase": row["phase"],
    }
    payload["party"] = {
        "address": row["address"],
        "mode": row["mode"],
        "site_id": row["site_id"],
        "site_node_id": row["site_node_id"],
        "phase": row["phase"],
        "clocks": json.loads(row["clocks_json"] or "{}"),
        "gold_in_transit": row["gold_in_transit"],
    }
    campaign_slug = row["campaign_slug"]
    all_chars = ctx.conn.execute(
        "SELECT id, slot, sheet_json FROM characters WHERE campaign_slug = ?",
        (campaign_slug,),
    ).fetchall()
    payload["characters"] = [
        {
            "character_id": c["id"],
            "slot": c["slot"],
            "display_name": json.loads(c["sheet_json"]).get("displayName", c["id"]),
        }
        for c in all_chars
    ]
    chars = [c for c in all_chars if c["slot"] is not None]
    for c in chars:
        sheet = json.loads(c["sheet_json"])
        hp = sheet.get("hp", {})
        payload["roster"].append(
            {
                "slot": c["slot"],
                "character_id": c["id"],
                "display_name": sheet.get("displayName", c["id"]),
                "hp": f"{hp.get('current', '?')}/{hp.get('max', '?')}",
            }
        )
    if row["ended_at"] is None:
        if not payload["roster"] and not all_chars:
            payload["awaiting"] = "CHARACTER_CREATION"
        elif not payload["roster"] and all_chars:
            payload["awaiting"] = "ROSTER_SETUP"
        else:
            payload["awaiting"] = "PLAYER_ACTIONS"
    else:
        payload["awaiting"] = "SESSION_ENDED"
    combat = ctx.conn.execute(
        "SELECT * FROM combat_state WHERE session_id = ? AND active = 1",
        (session_id,),
    ).fetchone()
    if combat:
        payload["combat"] = {
            "round": combat["round"],
            "turn_index": combat["turn_index"],
            "initiative": json.loads(combat["initiative_json"]),
        }
    return payload


def handle_check(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    ctx = _ctx(args)
    cfg = ctx.config
    blockers: list[dict] = []
    warnings: list[str] = []

    if not cfg.content_root.is_dir():
        blockers.append({"code": "CONTENT_ROOT", "message": f"Missing content_root: {cfg.content_root}"})
    else:
        validate = cfg.content_root / "tools" / "validate_content.py"
        if validate.exists():
            proc = subprocess.run(
                [sys.executable, str(validate)],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
            )
            if proc.returncode != 0:
                blockers.append(
                    {
                        "code": "VALIDATE_CONTENT",
                        "message": proc.stderr or proc.stdout or "validate_content failed",
                    }
                )

    if schema_version(ctx.conn) < 1:
        blockers.append({"code": "SCHEMA", "message": "Run init first"})

    return {
        "ok": len(blockers) == 0,
        "blocked": len(blockers) > 0,
        "blockers": blockers,
        "warnings": warnings,
    }


def handle_suggest(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    from tomb_gm.domain import gates as gates_domain

    ctx = _ctx(args)
    status = handle_status(args, None)
    check = handle_check(args, None)
    pending = None
    active = _read_active(ctx.config)
    if active and active.get("session_id"):
        pending = gates_domain.pending_gate(ctx.conn, active["session_id"])
    return build_suggest(status, check, pending_gate=pending)


def log_event(conn, session_id: str | None, event_type: str, payload: dict) -> None:
    conn.execute(
        "INSERT INTO events (session_id, ts, type, payload_json) VALUES (?, ?, ?, ?)",
        (
            session_id,
            datetime.now(timezone.utc).isoformat(),
            event_type,
            json.dumps(payload),
        ),
    )
    conn.commit()
