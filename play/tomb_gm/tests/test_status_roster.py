"""Status roster payload fields for sidebar stat block (APP-102)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
BUILD = REPO / "build"


@pytest.fixture()
def status_ctx(tmp_path):
    from tomb_gm.config import load_config
    from tomb_gm.db.connection import connect, run_migrations
    from tomb_gm.domain.character import create_character, set_roster_slot
    from tomb_gm.domain.inventory import ensure_normalized, get_pack, new_instance
    from tomb_gm.services.content import ContentService
    import argparse
    import os

    ws = tmp_path / "ws"
    (ws / ".local").mkdir(parents=True)
    (ws / "campaigns").mkdir()
    rel_build = Path(os.path.relpath(BUILD, ws))
    (ws / "config.yaml").write_text(f"content_root: {rel_build.as_posix()}\n", encoding="utf-8")
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    run_migrations(conn)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO campaigns (slug, display_name, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("stat-block", "Stat Block", now, now),
    )
    session_id = "current"
    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, phase) VALUES (?, ?, ?, ?)",
        (session_id, "stat-block", now, "preparation"),
    )
    conn.execute(
        "INSERT INTO party_state (session_id, address, mode, phase) VALUES (?, ?, ?, ?)",
        (session_id, "32-C", "surface", "preparation"),
    )
    conn.commit()

    create_character(
        conn,
        campaign_slug="stat-block",
        display_name="Kira",
        base_class="militia",
        character_id="kira",
        attributes={"STR": 12, "AGI": 14, "STA": 15, "INT": 8, "SPI": 10, "LUC": 14},
        skill_ids=["swordsmanship", "perception", "lore"],
        race_id="human",
    )
    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        ("kira", "stat-block"),
    ).fetchone()
    sheet = json.loads(row["sheet_json"])
    content = ContentService(BUILD)
    lookup = content.items_lookup()
    pack = get_pack(sheet)
    pack.append(
        new_instance("leather", kind="armor", equipped=True, slot="chest", catalog=lookup["leather"])
    )
    sheet["inventory"] = {"inventoryVersion": 3, "pack": pack}
    ensure_normalized(sheet)
    conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
        (json.dumps(sheet), "kira", "stat-block"),
    )
    conn.commit()
    set_roster_slot(conn, campaign_slug="stat-block", slot=1, character_id="kira")
    cfg.active_path.write_text(
        json.dumps({"session_id": session_id, "campaign_slug": "stat-block"}),
        encoding="utf-8",
    )
    args = argparse.Namespace(workspace=str(ws))
    yield args, sheet, cfg
    conn.close()


def test_status_roster_includes_stat_block_fields(status_ctx):
    from tomb_gm.cli.cmd_core import handle_status

    args, _sheet, _cfg = status_ctx
    payload = handle_status(args, None)
    roster = payload["roster"]
    assert roster
    pc = roster[0]

    assert pc["attributes"]["STR"] == 12
    assert pc["attribute_modifiers"]["STR"] == 1
    assert pc["attribute_modifiers"]["INT"] == -1
    assert pc["class_tier"] == 1
    assert pc["proficiency_bonus"] == 2
    assert pc["class_display"] == "Militia"
    assert pc["race_id"] == "human"
    assert pc["race_display"] == "Human"
    assert len(pc["skills"]) == 3
    assert pc["skills"][0]["skill_id"] == "swordsmanship"
    assert pc["skills"][0]["display_name"] == "Swordsmanship"


def test_status_roster_ac_matches_sheet_ac(status_ctx):
    from tomb_gm.cli.cmd_core import handle_status
    from tomb_gm.domain.combat_sheet import sheet_ac

    args, sheet, cfg = status_ctx
    payload = handle_status(args, None)
    expected = sheet_ac(sheet, content_root=cfg.content_root)
    assert payload["roster"][0]["ac"] == expected
    assert expected == 14
