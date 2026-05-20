from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from tomb_gm.config import GameplayConfig, DEFAULT_WORKSPACE

SAVE_SESSION_ID = "current"
DEFAULT_HUB_ADDRESS = "32-C"
DEFAULT_PHASE = "preparation"
DEFAULT_MODE = "surface"
DEFAULT_CLOCKS = {"ingress": 0, "delve": 0, "extract": 0, "max": 6}

_SESSION_SCOPED_TABLES = (
    "events",
    "combat_state",
    "party_state",
    "scene_summaries",
    "cell_features",
    "cell_visits",
    "site_rooms",
    "room_features",
)


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


def _assert_not_play_workspace(cfg: GameplayConfig) -> None:
    """Block tests from wiping the player's real save in play/workspace."""
    import os
    import sys

    if "pytest" not in sys.modules:
        return
    if os.environ.get("TOMB_GM_ALLOW_PLAY_WORKSPACE") == "1":
        return
    if cfg.workspace.resolve() == DEFAULT_WORKSPACE.resolve():
        raise RuntimeError(
            "Refusing to mutate play/workspace during tests. "
            "Use an isolated tmp workspace (play/tomb_gm/tests/conftest.py)."
        )


def _clear_save_slot(conn: sqlite3.Connection) -> None:
    """Remove the one playable session and all runtime state bound to it."""
    for table in _SESSION_SCOPED_TABLES:
        conn.execute(f"DELETE FROM {table}")
    conn.execute("DELETE FROM sessions")


def _normalize_save_session_id(conn: sqlite3.Connection) -> None:
    """Rename a legacy sole open session to SAVE_SESSION_ID."""
    row = conn.execute(
        "SELECT id FROM sessions WHERE ended_at IS NULL ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    if not row or row["id"] == SAVE_SESSION_ID:
        return
    conflict = conn.execute(
        "SELECT id FROM sessions WHERE id = ?", (SAVE_SESSION_ID,)
    ).fetchone()
    if conflict:
        return
    old_id = row["id"]
    for table in _SESSION_SCOPED_TABLES:
        conn.execute(
            f"UPDATE {table} SET session_id = ? WHERE session_id = ?",
            (SAVE_SESSION_ID, old_id),
        )
    conn.execute(
        "UPDATE sessions SET id = ? WHERE id = ?",
        (SAVE_SESSION_ID, old_id),
    )
    conn.commit()


def _campaign_has_roster(conn: sqlite3.Connection, campaign_slug: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM characters WHERE campaign_slug = ? AND slot IS NOT NULL AND alive = 1 LIMIT 1",
        (campaign_slug,),
    ).fetchone()
    return row is not None


def _is_test_campaign_slug(slug: str) -> bool:
    """Test suites write ephemeral campaigns into the shared workspace DB."""
    if slug in {"features-test", "remaining-test", "roll-attr-test", "test-campaign"}:
        return True
    prefixes = ("test-", "beat-", "mem-test-", "ws")
    return any(slug.startswith(p) for p in prefixes) and slug.endswith("-test")


def find_save_campaign(conn: sqlite3.Connection) -> str | None:
    """Return the campaign slug for a playable save, recovering orphaned characters."""
    session = _get_save_session(conn)
    if session and _campaign_has_roster(conn, session["campaign_slug"]):
        return session["campaign_slug"]

    row = conn.execute(
        """
        SELECT campaign_slug FROM characters
        WHERE slot IS NOT NULL AND alive = 1
        ORDER BY created_at DESC
        """
    ).fetchall()
    for r in row:
        slug = r["campaign_slug"]
        if not _is_test_campaign_slug(slug):
            return slug
    return None


def has_save_session(conn: sqlite3.Connection) -> bool:
    return find_save_campaign(conn) is not None


def _get_save_session(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """Return the sole open session, closing duplicates if legacy data exists."""
    rows = conn.execute(
        "SELECT * FROM sessions WHERE ended_at IS NULL ORDER BY started_at DESC"
    ).fetchall()
    if not rows:
        return None
    if len(rows) == 1:
        return rows[0]

    keep = rows[0]
    now = _utc_now()
    for row in rows[1:]:
        conn.execute(
            "UPDATE sessions SET ended_at = ?, phase = 'ended' WHERE id = ?",
            (now, row["id"]),
        )
    conn.commit()
    return keep


def start_session(
    conn: sqlite3.Connection,
    cfg: GameplayConfig,
    campaign_slug: str,
) -> dict:
    if not _campaign_exists(conn, campaign_slug):
        return {"ok": False, "error": f"campaign not found: {campaign_slug}"}

    _assert_not_play_workspace(cfg)

    _clear_save_slot(conn)
    clear_active(cfg)

    now = _utc_now()
    clocks_json = json.dumps(DEFAULT_CLOCKS)

    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, ended_at, phase, summary_id) "
        "VALUES (?, ?, ?, NULL, ?, NULL)",
        (SAVE_SESSION_ID, campaign_slug, now, DEFAULT_PHASE),
    )
    conn.execute(
        "INSERT INTO party_state (session_id, address, mode, site_id, site_node_id, phase, "
        "stamp_json, clocks_json, gold_in_transit, flags_json) "
        "VALUES (?, ?, ?, NULL, NULL, ?, NULL, ?, 0, '{}')",
        (SAVE_SESSION_ID, DEFAULT_HUB_ADDRESS, DEFAULT_MODE, DEFAULT_PHASE, clocks_json),
    )
    conn.commit()

    active_payload = {
        "campaign_slug": campaign_slug,
        "session_id": SAVE_SESSION_ID,
        "activated_at": now,
    }
    write_active(cfg, active_payload)

    return {
        "ok": True,
        "session_id": SAVE_SESSION_ID,
        "campaign_slug": campaign_slug,
        "phase": DEFAULT_PHASE,
        "address": DEFAULT_HUB_ADDRESS,
        "mode": DEFAULT_MODE,
        "started_at": now,
        "active": active_payload,
        "replaced_previous": True,
    }


def resume_session(
    conn: sqlite3.Connection,
    cfg: GameplayConfig,
    campaign_slug: str | None = None,
    session_id: str | None = None,
) -> dict:
    del campaign_slug, session_id  # single save slot — no selection needed

    _normalize_save_session_id(conn)
    session_row = _get_save_session(conn)
    save_campaign = find_save_campaign(conn)
    if not save_campaign:
        return {"ok": False, "error": "no save session found"}

    if not _campaign_exists(conn, save_campaign):
        return {"ok": False, "error": f"campaign not found: {save_campaign}"}

    recovered = False
    if not session_row:
        now = _utc_now()
        clocks_json = json.dumps(DEFAULT_CLOCKS)
        conn.execute(
            "INSERT INTO sessions (id, campaign_slug, started_at, ended_at, phase, summary_id) "
            "VALUES (?, ?, ?, NULL, ?, NULL)",
            (SAVE_SESSION_ID, save_campaign, now, DEFAULT_PHASE),
        )
        conn.execute(
            "INSERT INTO party_state (session_id, address, mode, site_id, site_node_id, phase, "
            "stamp_json, clocks_json, gold_in_transit, flags_json) "
            "VALUES (?, ?, ?, NULL, NULL, ?, NULL, ?, 0, '{}')",
            (SAVE_SESSION_ID, DEFAULT_HUB_ADDRESS, DEFAULT_MODE, DEFAULT_PHASE, clocks_json),
        )
        conn.commit()
        session_row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (SAVE_SESSION_ID,)
        ).fetchone()
    elif session_row["campaign_slug"] != save_campaign:
        recovered = True
        conn.execute(
            "UPDATE sessions SET campaign_slug = ? WHERE id = ?",
            (save_campaign, session_row["id"]),
        )
        conn.commit()
        session_row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_row["id"],)
        ).fetchone()

    slug = session_row["campaign_slug"]

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

    from tomb_gm.domain.inventory import normalize_campaign_sheets
    from tomb_gm.services.content import ContentService
    from tomb_gm.services.death import reconcile_save_vitals

    content = ContentService(cfg.content_root)
    inventory_normalize = normalize_campaign_sheets(
        conn,
        campaign_slug=slug,
        item_lookup=content.items_lookup(),
    )

    reconcile = reconcile_save_vitals(
        conn,
        campaign_slug=slug,
        session_id=session_row["id"],
    )

    result: dict = {
        "ok": True,
        "session_id": session_row["id"],
        "campaign_slug": slug,
        "phase": session_row["phase"],
        "address": party["address"] if party else DEFAULT_HUB_ADDRESS,
        "mode": party["mode"] if party else DEFAULT_MODE,
        "started_at": session_row["started_at"],
        "resumed": True,
        "recovered_campaign": recovered,
        "active": active_payload,
        "inventory_normalize": inventory_normalize,
        "reconcile": reconcile,
    }
    if reconcile.get("run_ended"):
        result["run_ended"] = True
        result["new_game_required"] = True
        corpses = [d.get("corpse") for d in reconcile.get("death_results") or [] if d.get("ok")]
        result["corpses"] = corpses
    return result


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
