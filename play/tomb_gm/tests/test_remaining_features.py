from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tomb_gm.cli.context import CommandContext
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect, run_migrations
from tomb_gm.domain.character import create_character
from tomb_gm.domain.combat_player import spend_fortune, spawn_roster_combatants
from tomb_gm.domain.creation import roll_genetics, roll_life_event
from tomb_gm.domain.spell_cast import cast_spell
from tomb_gm.services.loot import roll_loot_table
from tomb_gm.services.rag.lore import search_lore
from tomb_gm.services.simulation.combat import apply_damage_to_combatant, start_combat
from tomb_gm.services.site import enter_site, search_site

REPO = Path(__file__).resolve().parents[3]
WORKSPACE = REPO / "play" / "workspace"
CAMPAIGN = "remaining-test"
SESSION = "sess-remaining-test"


@pytest.fixture()
def play_ctx():
    ws = resolve_workspace(str(WORKSPACE))
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    run_migrations(conn)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO campaigns "
        "(slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (CAMPAIGN, "Remaining", "{}", "{}", now, now),
    )
    conn.execute("DELETE FROM characters WHERE campaign_slug = ?", (CAMPAIGN,))
    conn.execute("DELETE FROM combat_state WHERE session_id = ?", (SESSION,))
    conn.execute("DELETE FROM party_state WHERE session_id = ?", (SESSION,))
    conn.execute("DELETE FROM events WHERE session_id = ?", (SESSION,))
    conn.execute("DELETE FROM sessions WHERE id = ?", (SESSION,))
    conn.execute(
        "INSERT INTO sessions (id, campaign_slug, started_at, ended_at) VALUES (?, ?, ?, NULL)",
        (SESSION, CAMPAIGN, now),
    )
    conn.execute(
        "INSERT OR REPLACE INTO party_state "
        "(session_id, address, mode, site_id, site_node_id, phase, stamp_json) "
        "VALUES (?, '32-C', 'surface', NULL, NULL, 'preparation', NULL)",
        (SESSION,),
    )
    conn.commit()
    create_character(
        conn,
        campaign_slug=CAMPAIGN,
        display_name="Caster",
        base_class="apprentice",
        attributes={"STR": 10, "AGI": 12, "STA": 10, "INT": 14, "SPI": 10, "LUC": 10},
        character_id="caster",
    )
    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        ("caster", CAMPAIGN),
    ).fetchone()
    sheet = json.loads(row["sheet_json"])
    sheet["mp"] = {"current": 5, "max": 12}
    sheet["fortune"] = {"current": 2, "max": 2}
    conn.execute(
        "UPDATE characters SET sheet_json = ?, slot = 1 WHERE id = ? AND campaign_slug = ?",
        (json.dumps(sheet), "caster", CAMPAIGN),
    )
    conn.commit()
    ctx = CommandContext(config=cfg, conn=conn)
    active_path = cfg.active_path
    active_path.parent.mkdir(parents=True, exist_ok=True)
    active_path.write_text(
        json.dumps({"session_id": SESSION, "campaign_slug": CAMPAIGN}),
        encoding="utf-8",
    )
    yield ctx
    conn.execute("DELETE FROM combat_state WHERE session_id = ?", (SESSION,))
    conn.commit()
    conn.close()


def test_roll_genetics_seeded():
    mods, detail = roll_genetics(random.Random(7))
    assert len(detail) == 6
    assert "STR" in mods


def test_roll_life_event():
    event, dice = roll_life_event(random.Random(3), REPO / "build")
    assert len(dice) == 2
    assert "min" in event or "attributes" in event


def test_loot_table():
    out = roll_loot_table(REPO / "build", "skirmisher", rng=random.Random(1))
    assert out["ok"] is True


def test_fortune_spend(play_ctx):
    out = spend_fortune(
        play_ctx.conn,
        campaign_slug=CAMPAIGN,
        character_id="caster",
        amount=1,
    )
    assert out["spent"] == 1
    assert out["fortune"]["current"] == 1


def test_spawn_roster_combatants(play_ctx):
    pcs, init = spawn_roster_combatants(play_ctx.conn, CAMPAIGN, rng=random.Random(1))
    assert len(pcs) == 1
    assert pcs[0]["kind"] == "pc"
    assert init[0]["id"] == "caster"


def test_start_combat_with_party(play_ctx):
    out = start_combat(
        play_ctx.conn,
        session_id=SESSION,
        content_root=play_ctx.config.content_root,
        monster_specs=["grave-ghoul:1"],
        include_party=True,
        campaign_slug=CAMPAIGN,
        seed=42,
    )
    ids = {c["id"] for c in out["combatants"]}
    assert "grave-ghoul-1" in ids
    assert "caster" in ids


def test_pc_damage_syncs_sheet(play_ctx):
    start_combat(
        play_ctx.conn,
        session_id=SESSION,
        content_root=play_ctx.config.content_root,
        monster_specs=["grave-ghoul:1"],
        include_party=True,
        campaign_slug=CAMPAIGN,
        seed=1,
    )
    apply_damage_to_combatant(
        play_ctx.conn,
        SESSION,
        "caster",
        5,
        campaign_slug=CAMPAIGN,
    )
    row = play_ctx.conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ?",
        ("caster",),
    ).fetchone()
    sheet = json.loads(row["sheet_json"])
    assert sheet["hp"]["current"] == sheet["hp"]["max"] - 5


def test_cast_spell_save(play_ctx):
    def _log(conn, sid, kind, payload):
        pass

    out = cast_spell(
        play_ctx.conn,
        _log,
        content_root=play_ctx.config.content_root,
        campaign_slug=CAMPAIGN,
        character_id="caster",
        spell_id="ash-veil",
        session_id=SESSION,
        target_id=None,
        seed=10,
    )
    assert out["ok"] is True
    assert "save" in out
    assert out["mp_remaining"] == 3


def test_site_search_in_site(play_ctx):
    enter_site(play_ctx, "breley-undercrypt")
    play_ctx.conn.execute(
        "UPDATE party_state SET site_node_id = 'marshal-tomb' WHERE session_id = ?",
        (SESSION,),
    )
    play_ctx.conn.commit()
    out = search_site(play_ctx, dc=5, skill_mod=5, seed=99)
    assert out["success"] is True
    assert "loot" in out


def test_lore_search(play_ctx):
    results = search_lore(
        play_ctx.conn,
        play_ctx.config.content_root,
        "Breley",
        max_results=3,
    )
    assert isinstance(results, list)
