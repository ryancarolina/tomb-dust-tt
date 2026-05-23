"""Tests for sheet-backed social skill checks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
CONTENT = REPO / "build"


@pytest.fixture
def skill_db(tmp_path):
    from tomb_gm.db.connection import connect, run_migrations
    from tomb_gm.domain.character import create_character
    from tomb_gm.tests.helpers import seed_campaign

    conn = connect(tmp_path / "skill.db")
    run_migrations(conn)
    seed_campaign(conn, "skill-test")
    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, phase) "
        "VALUES ('sess1', 'skill-test', '2026-01-01', 'preparation')"
    )
    conn.commit()
    create_character(
        conn,
        campaign_slug="skill-test",
        display_name="Talker",
        base_class="novice",
        character_id="talker",
        attributes={"STR": 10, "AGI": 10, "STA": 10, "INT": 14, "SPI": 16, "LUC": 10},
        skill_ids=["persuasion", "intimidation", "deception"],
        gold_gp=10,
    )
    conn.execute("UPDATE characters SET slot = 1 WHERE id = 'talker'")
    conn.commit()
    return conn


def test_assemble_persuasion_modifiers(skill_db):
    from tomb_gm.services.simulation.skill_checks import assemble_skill_modifiers

    sheet = json.loads(
        skill_db.execute("SELECT sheet_json FROM characters WHERE id = 'talker'").fetchone()[
            "sheet_json"
        ]
    )
    total, breakdown = assemble_skill_modifiers(sheet, "persuasion")
    assert total == 5
    labels = {m["label"]: m["value"] for m in breakdown}
    assert labels["SPI"] == 3
    assert labels["PB"] == 2
    assert labels["skill"] == 0


def test_intimidation_uses_higher_str_spi(skill_db):
    from tomb_gm.services.simulation.skill_checks import assemble_skill_modifiers

    sheet = json.loads(
        skill_db.execute("SELECT sheet_json FROM characters WHERE id = 'talker'").fetchone()[
            "sheet_json"
        ]
    )
    sheet["attributes"]["STR"] = 18
    sheet["attributes"]["SPI"] = 12
    total, breakdown = assemble_skill_modifiers(sheet, "intimidation")
    labels = {m["label"]: m["value"] for m in breakdown}
    assert labels["STR"] == 4
    assert total == 6


def test_skill_check_uses_sheet_not_llm_mod(skill_db):
    from tomb_gm.cli.cmd_core import log_event
    from tomb_gm.services.simulation.skill_checks import skill_check

    result = skill_check(
        skill_db,
        "skill-test",
        "talker",
        "persuasion",
        10,
        content_root=CONTENT,
        log_event=log_event,
        session_id="sess1",
        seed=7,
    )
    assert result["ok"] is True
    assert result["skill_id"] == "persuasion"
    assert result["mod"] == 5
    assert result["dc"] == 10
    assert result["total"] == result["natural"] + 5
    assert "margin" in result


def test_opposed_dc_placeholder(skill_db):
    from tomb_gm.services.simulation.skill_checks import opposed_dc

    assert opposed_dc(content_root=CONTENT, opposed_npc_id="marshal-garrick-holt") == 12
    assert opposed_dc(explicit_dc=15) == 15
    assert opposed_dc() == 15
