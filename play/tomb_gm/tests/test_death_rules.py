"""Tests for death rules: massive trauma, consciousness roll, corpses."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture
def death_db(tmp_path):
    from tomb_gm.db.connection import connect, run_migrations
    from tomb_gm.domain.character import create_character

    db_path = tmp_path / "test.db"
    from tomb_gm.domain.creation import starting_kit_inventory

    conn = connect(db_path)
    run_migrations(conn)
    conn.execute(
        "INSERT INTO campaigns (slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES ('death-test', 'Death Test', '{}', '{}', '2026-01-01', '2026-01-01')"
    )
    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, phase) VALUES ('current', 'death-test', '2026-01-01', 'delve')"
    )
    conn.commit()
    create_character(
        conn,
        campaign_slug="death-test",
        display_name="Test Delver",
        base_class="novice",
        character_id="test-delver",
        attributes={"STR": 12, "AGI": 10, "STA": 14, "INT": 10, "SPI": 12, "LUC": 10},
        inventory=starting_kit_inventory(REPO / "build", "novice"),
        gold_gp=100,
    )
    conn.execute("UPDATE characters SET slot = 1 WHERE id = 'test-delver'")
    row = conn.execute(
        "SELECT id, sheet_json FROM characters WHERE campaign_slug = 'death-test' LIMIT 1"
    ).fetchone()
    sheet = json.loads(row["sheet_json"])
    sheet["hp"] = {"current": 3, "max": 20}
    conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ?",
        (json.dumps(sheet), row["id"]),
    )
    conn.execute(
        "INSERT INTO party_state (session_id, address, mode, site_id, dungeon_room_id) "
        "VALUES ('current', '32-C', 'dungeon', '32-C-UG-1', 'ossuary-hall')"
    )
    conn.commit()
    return conn, row["id"]


def test_massive_trauma_instant_death(death_db):
    conn, char_id = death_db
    from tomb_gm.domain.combat_player import resolve_pc_damage

    result = resolve_pc_damage(
        conn,
        campaign_slug="death-test",
        character_id=char_id,
        damage=9,
        seed=1,
    )
    assert result["died"] is True
    assert result["reason"] == "massive_trauma"
    row = conn.execute("SELECT alive FROM characters WHERE id = ?", (char_id,)).fetchone()
    assert row["alive"] == 0


def test_zero_hp_consciousness_roll_success(death_db, monkeypatch):
    conn, char_id = death_db
    from tomb_gm.domain.combat_player import DOWNED, resolve_pc_damage

    sheet = json.loads(
        conn.execute("SELECT sheet_json FROM characters WHERE id = ?", (char_id,)).fetchone()["sheet_json"]
    )
    sheet["hp"]["current"] = 10
    conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ?",
        (json.dumps(sheet), char_id),
    )
    conn.commit()

    monkeypatch.setattr("tomb_gm.rules.bridge.roll_d20", lambda _rng: 15)

    result = resolve_pc_damage(
        conn,
        campaign_slug="death-test",
        character_id=char_id,
        damage=10,
        seed=42,
    )
    assert result["died"] is False
    assert result["hp"] == 0
    assert DOWNED in result["conditions"]
    assert result["consciousness_roll"]["success"] is True


def test_damage_at_zero_kills(death_db):
    conn, char_id = death_db
    from tomb_gm.domain.combat_player import resolve_pc_damage

    resolve_pc_damage(conn, campaign_slug="death-test", character_id=char_id, damage=3, seed=42)
    result = resolve_pc_damage(conn, campaign_slug="death-test", character_id=char_id, damage=1, seed=43)
    assert result["died"] is True
    assert result["reason"] == "damage_at_zero_hp"


def test_corpse_persists_after_wipe(death_db):
    conn, char_id = death_db
    from tomb_gm.services.death import get_corpses_for_room, process_delver_death

    result = process_delver_death(
        conn,
        campaign_slug="death-test",
        character_id=char_id,
        session_id="current",
        cause="test death",
    )
    assert result["ok"]
    corpse_id = result["corpse"]["corpse_id"]
    corpses = get_corpses_for_room("32-C-UG-1", "ossuary-hall", conn)
    assert any(c["id"] == corpse_id for c in corpses)

    conn.execute("DELETE FROM characters")
    conn.commit()
    corpses_after = get_corpses_for_room("32-C-UG-1", "ossuary-hall", conn)
    assert len(corpses_after) == 1


def test_reconcile_legacy_zero_hp_after_fight(death_db):
    conn, char_id = death_db
    from tomb_gm.services.death import get_corpses_for_room, reconcile_save_vitals

    sheet = json.loads(
        conn.execute("SELECT sheet_json FROM characters WHERE id = ?", (char_id,)).fetchone()["sheet_json"]
    )
    sheet["hp"]["current"] = 0
    sheet["conditions"] = []
    conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ?",
        (json.dumps(sheet), char_id),
    )
    conn.commit()

    result = reconcile_save_vitals(
        conn,
        campaign_slug="death-test",
        session_id="current",
    )
    assert result["run_ended"] is True
    assert char_id in result["deaths"]
    row = conn.execute("SELECT alive FROM characters WHERE id = ?", (char_id,)).fetchone()
    assert row["alive"] == 0
    corpses = get_corpses_for_room("32-C-UG-1", "ossuary-hall", conn)
    assert len(corpses) == 1


def test_corpse_loot_transfers_pack(death_db):
    conn, victim_id = death_db
    from tomb_gm.domain.character import create_character, set_roster_slot
    from tomb_gm.domain.creation import starting_kit_inventory
    from tomb_gm.services.death import loot_corpse, process_delver_death

    create_character(
        conn,
        campaign_slug="death-test",
        display_name="Looter",
        base_class="urchin",
        character_id="looter",
        attributes={"STR": 8, "AGI": 12, "STA": 10, "INT": 10, "SPI": 10, "LUC": 10},
        inventory={"inventoryVersion": 2, "pack": []},
    )
    set_roster_slot(conn, campaign_slug="death-test", slot=1, character_id="looter")
    conn.execute("UPDATE characters SET slot = NULL WHERE id = ?", (victim_id,))
    conn.execute("UPDATE characters SET slot = 2 WHERE id = 'looter'")
    conn.commit()

    death = process_delver_death(
        conn,
        campaign_slug="death-test",
        character_id=victim_id,
        session_id="current",
    )
    corpse_id = death["corpse"]["corpse_id"]
    loot = json.loads(
        conn.execute("SELECT loot_json FROM world_corpses WHERE id = ?", (corpse_id,)).fetchone()[0]
    )
    assert loot["goldGp"] == 100
    assert len(loot.get("pack") or []) >= 5

    result = loot_corpse(
        conn,
        corpse_id=corpse_id,
        campaign_slug="death-test",
        character_id="looter",
        content_root=REPO / "build",
    )
    assert result["ok"]
    assert result["new_gold_gp"] == 100
    looter_sheet = json.loads(
        conn.execute("SELECT sheet_json FROM characters WHERE id = 'looter'", ()).fetchone()["sheet_json"]
    )
    assert len(looter_sheet["inventory"]["pack"]) >= 5


def test_grave_ghoul_feast_behavior():
    from tomb_gm.services.simulation.combat import _pick_monster_target

    attacker = {"downedBehavior": "feast"}
    combatants = [
        {"id": "pc1", "kind": "pc", "hp": 5, "conditions": []},
        {"id": "pc2", "kind": "pc", "hp": 0, "conditions": ["Dying"]},
    ]
    assert _pick_monster_target(attacker, combatants) == "pc2"
