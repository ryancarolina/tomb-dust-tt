from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from tomb_gm.config import GameplayConfig

DEFAULT_HUB_ADDRESS = "32-C"
DEFAULT_PHASE = "preparation"
DEFAULT_MODE = "surface"
DEFAULT_CLOCKS = {"ingress": 0, "delve": 0, "extract": 0, "max": 6}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_active(cfg: GameplayConfig) -> dict | None:
    if not cfg.active_path.exists():
        return None
    return json.loads(cfg.active_path.read_text(encoding="utf-8"))


def write_active(cfg: GameplayConfig, payload: dict) -> None:
    cfg.active_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.active_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def clear_active(cfg: GameplayConfig) -> None:
    if cfg.active_path.exists():
        cfg.active_path.unlink()


def _campaign_exists(conn: sqlite3.Connection, campaign_slug: str) -> bool:
    row = conn.execute("SELECT slug FROM campaigns WHERE slug = ?", (campaign_slug,)).fetchone()
    return row is not None


def _find_open_session(conn: sqlite3.Connection, campaign_slug: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM sessions WHERE campaign_slug = ? AND ended_at IS NULL "
        "ORDER BY started_at DESC LIMIT 1",
        (campaign_slug,),
    ).fetchone()


def start_session(
    conn: sqlite3.Connection,
    cfg: GameplayConfig,
    campaign_slug: str,
) -> dict:
    if not _campaign_exists(conn, campaign_slug):
        return {"ok": False, "error": f"campaign not found: {campaign_slug}"}

    active = read_active(cfg)
    if active:
        session_id = active.get("session_id")
        if session_id:
            open_row = conn.execute(
                "SELECT id, ended_at FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if open_row and open_row["ended_at"] is None:
                return {
                    "ok": False,
                    "error": "active session already exists",
                    "session_id": session_id,
                    "campaign_slug": active.get("campaign_slug"),
                }

    open_for_campaign = _find_open_session(conn, campaign_slug)
    if open_for_campaign:
        return {
            "ok": False,
            "error": "campaign already has an open session",
            "session_id": open_for_campaign["id"],
        }

    session_id = str(uuid.uuid4())
    now = _utc_now()
    clocks_json = json.dumps(DEFAULT_CLOCKS)

    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, ended_at, phase, summary_id) "
        "VALUES (?, ?, ?, NULL, ?, NULL)",
        (session_id, campaign_slug, now, DEFAULT_PHASE),
    )
    conn.execute(
        "INSERT INTO party_state (session_id, address, mode, site_id, site_node_id, phase, "
        "stamp_json, clocks_json, gold_in_transit, flags_json) "
        "VALUES (?, ?, ?, NULL, NULL, ?, NULL, ?, 0, '{}')",
        (session_id, DEFAULT_HUB_ADDRESS, DEFAULT_MODE, DEFAULT_PHASE, clocks_json),
    )
    conn.commit()

    active_payload = {
        "campaign_slug": campaign_slug,
        "session_id": session_id,
        "activated_at": now,
    }
    write_active(cfg, active_payload)

    return {
        "ok": True,
        "session_id": session_id,
        "campaign_slug": campaign_slug,
        "phase": DEFAULT_PHASE,
        "address": DEFAULT_HUB_ADDRESS,
        "mode": DEFAULT_MODE,
        "started_at": now,
        "active": active_payload,
    }


def resume_session(
    conn: sqlite3.Connection,
    cfg: GameplayConfig,
    campaign_slug: str | None = None,
) -> dict:
    slug = campaign_slug
    if not slug:
        active = read_active(cfg)
        if active and active.get("campaign_slug"):
            slug = active["campaign_slug"]
        else:
            row = conn.execute(
                "SELECT campaign_slug FROM sessions WHERE ended_at IS NULL "
                "ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
            if row:
                slug = row["campaign_slug"]

    if not slug:
        return {"ok": False, "error": "no campaign specified and no open session found"}

    if not _campaign_exists(conn, slug):
        return {"ok": False, "error": f"campaign not found: {slug}"}

    session_row = _find_open_session(conn, slug)
    if not session_row:
        return {"ok": False, "error": f"no open session for campaign: {slug}"}

    party = conn.execute(
        "SELECT address, mode, phase FROM party_state WHERE session_id = ?",
        (session_row["id"],),
    ).fetchone()

    now = _utc_now()
    active_payload = {
        "campaign_slug": slug,
        "session_id": session_row["id"],
        "activated_at": now,
    }
    write_active(cfg, active_payload)

    return {
        "ok": True,
        "session_id": session_row["id"],
        "campaign_slug": slug,
        "phase": session_row["phase"],
        "address": party["address"] if party else DEFAULT_HUB_ADDRESS,
        "mode": party["mode"] if party else DEFAULT_MODE,
        "started_at": session_row["started_at"],
        "resumed": True,
        "active": active_payload,
    }


def end_session(conn: sqlite3.Connection, cfg: GameplayConfig) -> dict:
    active = read_active(cfg)
    if not active or not active.get("session_id"):
        return {"ok": False, "error": "no active session"}

    session_id = active["session_id"]
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not row:
        clear_active(cfg)
        return {"ok": False, "error": f"session not found: {session_id}"}

    if row["ended_at"] is not None:
        clear_active(cfg)
        return {"ok": False, "error": "session already ended", "session_id": session_id}

    now = _utc_now()
    ended_phase = "ended"
    conn.execute(
        "UPDATE sessions SET ended_at = ?, phase = ? WHERE id = ?",
        (now, ended_phase, session_id),
    )
    conn.execute(
        "UPDATE party_state SET phase = ? WHERE session_id = ?",
        (ended_phase, session_id),
    )
    conn.commit()
    clear_active(cfg)

    return {
        "ok": True,
        "session_id": session_id,
        "campaign_slug": row["campaign_slug"],
        "ended_at": now,
        "phase": ended_phase,
    }
