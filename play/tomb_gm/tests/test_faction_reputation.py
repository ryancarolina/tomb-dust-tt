"""Unit tests for faction reputation service (APP-100)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
CONTENT = REPO / "build"


@pytest.fixture
def faction_db(tmp_path):
    from tomb_gm.db.connection import connect, run_migrations

    conn = connect(tmp_path / "factions.db")
    run_migrations(conn)
    conn.execute(
        "INSERT INTO campaigns (slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES ('rep-test', 'Rep Test', '{}', '{}', '2026-01-01', '2026-01-01')"
    )
    conn.commit()
    return conn


def test_ensure_reputation_defaults_all_zero(faction_db):
    from tomb_gm.services.economy import get_account_state, save_account_state
    from tomb_gm.services.factions import ensure_reputation_defaults, faction_ids

    state = get_account_state(faction_db, "rep-test")
    rep = ensure_reputation_defaults(state, CONTENT)
    save_account_state(faction_db, "rep-test", state)

    assert set(rep.keys()) == set(faction_ids(CONTENT))
    assert all(v == 0 for v in rep.values())


def test_adjust_rep_clamps(faction_db):
    from tomb_gm.services.factions import adjust_rep, get_rep

    adjust_rep(
        faction_db,
        "rep-test",
        "knights-of-breley",
        5,
        "test_bump",
        content_root=CONTENT,
    )
    assert get_rep(faction_db, "rep-test", "knights-of-breley", content_root=CONTENT) == 3

    adjust_rep(
        faction_db,
        "rep-test",
        "knights-of-breley",
        -10,
        "test_drop",
        content_root=CONTENT,
    )
    assert get_rep(faction_db, "rep-test", "knights-of-breley", content_root=CONTENT) == -3


def test_holt_advance_dc_modifier_at_knights_minus_two(faction_db):
    from tomb_gm.services.factions import adjust_rep, effects_at, resolve_mechanical_key

    adjust_rep(
        faction_db,
        "rep-test",
        "knights-of-breley",
        -2,
        "test",
        content_root=CONTENT,
    )
    rep_state = {"knights-of-breley": -2}
    assert resolve_mechanical_key("holt_advance_dc_modifier", rep_state) == 2
    active = effects_at(CONTENT, rep_state, address="32-C")
    assert active.get("holt_advance_dc_modifier") == 2


def test_holt_advance_cap_bonus_at_knights_plus_two(faction_db):
    from tomb_gm.services.factions import adjust_rep, effects_at, resolve_mechanical_key

    adjust_rep(
        faction_db,
        "rep-test",
        "knights-of-breley",
        2,
        "test",
        content_root=CONTENT,
    )
    rep_state = {"knights-of-breley": 2}
    assert resolve_mechanical_key("holt_advance_cap_bonus", rep_state) == 25
    active = effects_at(CONTENT, rep_state, address="32-C")
    assert active.get("holt_advance_cap_bonus") == 25


def test_tier_for_knights_standard_patrol(faction_db):
    from tomb_gm.services.factions import tier_for

    tier = tier_for(CONTENT, "knights-of-breley", 0)
    assert tier["label"] == "standard_patrol"


def test_rep_persists_in_account_state(faction_db):
    from tomb_gm.services.economy import get_account_state
    from tomb_gm.services.factions import adjust_rep

    adjust_rep(
        faction_db,
        "rep-test",
        "knights-of-breley",
        1,
        "quest_reward",
        content_root=CONTENT,
        source="test",
    )
    state = get_account_state(faction_db, "rep-test")
    rep = json.loads(json.dumps(state)).get("reputation", {})
    assert rep["knights-of-breley"] == 1


def test_verdant_travel_tier_bump(faction_db):
    from tomb_gm.services.factions import adjust_rep, resolve_mechanical_key

    adjust_rep(
        faction_db,
        "rep-test",
        "verdant-vale",
        -2,
        "desecration",
        content_root=CONTENT,
    )
    rep_state = {"verdant-vale": -2}
    assert resolve_mechanical_key("verdant_travel_tier_bump", rep_state) == 1
