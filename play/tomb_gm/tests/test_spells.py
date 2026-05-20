"""Spell service and casting (rules 1.1.0)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tomb_gm.services.simulation.spell_service import (
    SpellError,
    default_known_spells,
    ensure_spell_fields,
    spell_save_dc,
    spellcasting_bonus,
    casting_mod,
    proficiency_bonus,
    validate_cast,
)

REPO = Path(__file__).resolve().parents[3]
BUILD = REPO / "build"

def test_spell_save_dc_apprentice():
    sheet = {
        "classTier": 1,
        "attributes": {"INT": 16, "SPI": 10},
        "skills": [{"skillId": "spellcasting", "level": 5}],
        "spellFocusSchool": None,
    }
    spell = {"school": "pyromancy", "tradition": "arcane"}

    class FakeContent:
        def load_school(self, _sid):
            return None

    dc = spell_save_dc(sheet, spell, FakeContent())  # type: ignore[arg-type]
    assert dc == 15  # 8 + INT 16 (+3) + PB 2 + spellcasting 5 (+2)


def test_default_known_spells():
    assert "mend-light" in default_known_spells("novice")
    assert "ember-touch" in default_known_spells("apprentice")


def test_ensure_spell_fields_backfills():
    sheet = {"classId": "novice"}
    changed = ensure_spell_fields(sheet)
    assert changed is True
    assert "mend-light" in sheet["knownSpells"]


def test_validate_cast_unknown_spell():
    sheet = {
        "classId": "novice",
        "classTier": 1,
        "knownSpells": ["mend-light"],
        "mp": {"current": 5, "max": 10},
        "skills": [{"skillId": "spellcasting", "level": 1}],
    }
    spell = {"id": "firebolt", "tier": 2, "mpCost": 2}
    with pytest.raises(SpellError, match="not known"):
        validate_cast(sheet, spell, "firebolt")


def test_validate_cast_insufficient_mp():
    sheet = {
        "classId": "novice",
        "classTier": 1,
        "knownSpells": ["mend-light"],
        "mp": {"current": 0, "max": 10},
        "skills": [{"skillId": "spellcasting", "level": 1}],
    }
    spell = {"id": "mend-light", "tier": 1, "mpCost": 1}
    with pytest.raises(SpellError, match="insufficient_mp"):
        validate_cast(sheet, spell, "mend-light")


@pytest.fixture()
def status_ctx(tmp_path):
    from tomb_gm.config import load_config
    from tomb_gm.db.connection import connect, run_migrations
    from tomb_gm.cli.cmd_core import handle_status
    from tomb_gm.domain.character import create_character, set_roster_slot
    import argparse

    ws = tmp_path / "ws"
    (ws / ".local").mkdir(parents=True)
    (ws / "campaigns").mkdir()
    import os
    rel_build = Path(os.path.relpath(BUILD, ws))
    (ws / "config.yaml").write_text(f"content_root: {rel_build.as_posix()}\n", encoding="utf-8")
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    run_migrations(conn)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO campaigns (slug, display_name, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("test", "Test", now, now),
    )
    session_id = "current"
    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, phase) VALUES (?, ?, ?, ?)",
        (session_id, "test", now, "delve"),
    )
    conn.execute(
        "INSERT INTO party_state (session_id, address, mode, phase, site_id, dungeon_room_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, "32-C-UG-1", "dungeon", "delve", "32-C-UG-1", "chapel-stairs"),
    )
    conn.commit()
    create_character(
        conn,
        campaign_slug="test",
        display_name="Caster",
        base_class="novice",
        character_id="caster",
        skill_ids=["medicine", "spellcasting", "lore"],
        known_spell_ids=[],
    )
    set_roster_slot(conn, campaign_slug="test", slot=1, character_id="caster")
    cfg.active_path.write_text(
        json.dumps({"session_id": session_id, "campaign_slug": "test"}),
        encoding="utf-8",
    )
    args = argparse.Namespace(workspace=str(ws))
    yield args
    conn.close()


def test_status_migrates_known_spells(status_ctx):
    from tomb_gm.cli.cmd_core import handle_status

    payload = handle_status(status_ctx, None)
    roster = payload["roster"]
    assert roster
    assert roster[0]["known_spells"]
    assert roster[0]["spell_lines"]
    assert payload["party"]["display_address"] == "32-C-UG-1 / chapel-stairs"