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
from tomb_gm.services.content import ContentService
from tomb_gm.services.simulation.combat import combat_status
from tomb_gm.services.simulation.spell_service import ensure_spell_fields
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


def _migrate_roster_sheets(conn, campaign_slug: str, content_root: Path) -> None:
    """Backfill knownSpells and persist sheet updates for legacy saves."""
    content = ContentService(content_root)
    rows = conn.execute(
        "SELECT id, sheet_json FROM characters WHERE campaign_slug = ?",
        (campaign_slug,),
    ).fetchall()
    for row in rows:
        sheet = json.loads(row["sheet_json"])
        if ensure_spell_fields(sheet):
            conn.execute(
                "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
                (json.dumps(sheet), row["id"], campaign_slug),
            )
    conn.commit()


def _spell_display_lines(content: ContentService, spell_ids: list[str]) -> list[str]:
    lines: list[str] = []
    for sid in spell_ids:
        spell = content.load_spell(sid)
        if spell:
            lines.append(
                f"{spell.get('displayName', sid)} ({sid}, tier {spell.get('tier', '?')}, {spell.get('mpCost', '?')} MP)"
            )
        else:
            lines.append(sid)
    return lines


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
        "SELECT s.*, p.address, p.mode, p.site_id, p.site_node_id, p.phase, p.clocks_json, p.gold_in_transit, "
        "p.scene_index, p.scene_max, p.heading, p.dungeon_room_id "
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
        "scene_index": row["scene_index"] if "scene_index" in row.keys() else 1,
        "scene_max": row["scene_max"] if "scene_max" in row.keys() else 3,
        "heading": row["heading"] if "heading" in row.keys() else "N",
        "dungeon_room_id": row["dungeon_room_id"] if "dungeon_room_id" in row.keys() else None,
    }
    if row["mode"] == "dungeon" and row["site_id"]:
        display = row["site_id"]
        if row["dungeon_room_id"]:
            display = f"{display} / {row['dungeon_room_id']}"
        payload["party"]["display_address"] = display
        payload["party"]["grid_address"] = row["address"]
    campaign_slug = row["campaign_slug"]
    _migrate_roster_sheets(ctx.conn, campaign_slug, cfg.content_root)
    content = ContentService(cfg.content_root)
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
        fortune = sheet.get("fortune", {})
        known = sheet.get("knownSpells") or []
        spell_lines = _spell_display_lines(content, known)
        payload["roster"].append(
            {
                "slot": c["slot"],
                "character_id": c["id"],
                "display_name": sheet.get("displayName", c["id"]),
                "hp": f"{hp.get('current', '?')}/{hp.get('max', '?')}",
                "fortune": f"{fortune.get('current', 0)}/{fortune.get('max', 1)}",
                "gold": sheet.get("goldGp", 0),
                "base_class": sheet.get("baseClass", sheet.get("classId", "")),
                "deed_tier": sheet.get("deedTier", 0),
                "mp": f"{sheet.get('mp', {}).get('current', 0)}/{sheet.get('mp', {}).get('max', 0)}",
                "conditions": sheet.get("conditions", []),
                "known_spells": known,
                "spell_lines": spell_lines,
                "spell_schools": sheet.get("spellSchools", []),
                "concentration": sheet.get("concentration"),
            }
        )
    if row["ended_at"] is None:
        if not payload["roster"] and not all_chars:
            payload["awaiting"] = "CHARACTER_CREATION"
        elif not payload["roster"] and all_chars:
            payload["awaiting"] = "ROSTER_SETUP"
        else:
            payload["awaiting"] = "PLAYER_ACTIONS"
        for entry in payload["roster"]:
            conds = entry.get("conditions") or []
            hp_parts = str(entry.get("hp", "0/0")).split("/")
            try:
                hp_current = int(hp_parts[0])
            except ValueError:
                hp_current = 0
            if hp_current <= 0:
                if "Dying" in conds:
                    payload["awaiting"] = "DYING"
                    break
                if "Downed" in conds:
                    payload["awaiting"] = "DOWNED"
                    break
                if "Stable" in conds:
                    payload["awaiting"] = "DYING"
                    break
    else:
        payload["awaiting"] = "SESSION_ENDED"
    combat = ctx.conn.execute(
        "SELECT * FROM combat_state WHERE session_id = ? AND active = 1",
        (session_id,),
    ).fetchone()
    if combat:
        combat_detail = combat_status(ctx.conn, session_id)
        if combat_detail.get("ok"):
            payload["combat"] = {
                "round": combat_detail["round"],
                "turn_index": combat_detail["turn_index"],
                "turn_id": combat_detail.get("turn_id"),
                "turn_kind": combat_detail.get("turn_kind"),
                "initiative": combat_detail["initiative"],
                "combatants": combat_detail["combatants"],
            }
            payload["awaiting"] = "COMBAT_TURN"
        else:
            payload["combat"] = {
                "round": combat["round"],
                "turn_index": combat["turn_index"],
                "initiative": json.loads(combat["initiative_json"]),
            }
            payload["awaiting"] = "COMBAT_TURN"
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

    active = _read_active(cfg)
    if active and active.get("session_id"):
        status = handle_status(args, None)
        awaiting = status.get("awaiting")
        if awaiting == "DYING":
            blockers.append(
                {
                    "code": "DYING",
                    "message": "Delver is unconscious at 0 HP — cannot take normal actions.",
                }
            )
        elif awaiting == "DOWNED":
            warnings.append("Delver is Downed at 0 HP — heal, stabilize, or flee only.")

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
