from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tomb_gm.cli.cmd_character import handle_create, handle_list, handle_show
from tomb_gm.cli.cmd_roster import handle_clear, handle_set, handle_show as handle_roster_show
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect, run_migrations
from tomb_gm.domain.character import (
    CharacterError,
    build_sheet,
    compute_fortune_max,
    compute_hp,
    compute_mp,
    create_character,
    eligible_tier1_classes,
)

REPO = Path(__file__).resolve().parents[3]
WORKSPACE = REPO / "play" / "workspace"
CAMPAIGN = "ws4-test"


@pytest.fixture()
def ctx():
    ws = resolve_workspace(str(WORKSPACE))
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    run_migrations(conn)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO campaigns "
        "(slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (CAMPAIGN, "WS-4 Test", "{}", "{}", now, now),
    )
    conn.execute("DELETE FROM characters WHERE campaign_slug = ?", (CAMPAIGN,))
    conn.commit()
    from tomb_gm.cli.context import CommandContext

    yield CommandContext(config=cfg, conn=conn)
    conn.close()


def _args(**kwargs):
    defaults = {"workspace": str(WORKSPACE)}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_derived_stats_formulas():
    assert compute_hp(12) == {"current": 70, "max": 70, "base": 10}
    assert compute_mp(8, "militia") == {"current": 29, "max": 29, "base": 5}
    assert compute_fortune_max(14) == 3
    assert compute_fortune_max(10) == 1


def test_class_eligibility():
    attrs = {"STR": 10, "AGI": 10, "STA": 10, "INT": 6, "SPI": 10, "LUC": 10}
    eligible = eligible_tier1_classes(attrs)
    assert "peasant" in eligible
    assert "militia" in eligible
    assert "apprentice" not in eligible


def test_build_sheet_schema_shape():
    sheet = build_sheet(
        character_id="kira",
        display_name="Kira",
        base_class="militia",
        attributes={"STR": 10, "AGI": 10, "STA": 12, "INT": 8, "SPI": 10, "LUC": 14},
        skill_ids=["swordsmanship", "perception", "lore"],
    )
    assert sheet["rulesVersion"] == "1.0.0"
    assert sheet["classTier"] == 1
    assert sheet["baseMpClass"] == "militia"
    assert sheet["hp"]["max"] == 70
    assert sheet["mp"]["max"] == 29
    assert sheet["fortune"]["max"] == 3


def test_create_militia_via_handler(ctx):
    out = handle_create(
        _args(
            campaign=CAMPAIGN,
            name="Kira",
            base_class="militia",
            character_id=None,
            str=None,
            agi=None,
            sta=12,
            int=8,
            spi=None,
            luc=14,
            skills=None,
            roll_attributes=False,
        ),
        ctx,
    )
    assert out["ok"] is True
    assert out["character_id"] == "kira"
    assert out["hp"]["max"] == 70
    assert out["mp"]["max"] == 29
    assert out["fortune"]["max"] == 3


def test_character_show_and_list(ctx):
    create_character(
        ctx.conn,
        campaign_slug=CAMPAIGN,
        display_name="Kira",
        base_class="militia",
        attributes={"STA": 12, "INT": 8, "LUC": 14},
    )
    show = handle_show(_args(campaign=CAMPAIGN, character_id="kira"), ctx)
    assert show["ok"] is True
    assert show["sheet"]["displayName"] == "Kira"

    listed = handle_list(_args(campaign=CAMPAIGN), ctx)
    assert listed["ok"] is True
    assert any(c["id"] == "kira" for c in listed["characters"])


def test_roster_set_show_clear(ctx):
    create_character(ctx.conn, campaign_slug=CAMPAIGN, display_name="Kira", base_class="militia")
    create_character(ctx.conn, campaign_slug=CAMPAIGN, display_name="Bran", base_class="urchin")

    bound = handle_set(_args(campaign=CAMPAIGN, slot=1, character_id="kira"), ctx)
    assert bound["ok"] is True
    handle_set(_args(campaign=CAMPAIGN, slot=2, character_id="bran"), ctx)

    party = handle_roster_show(_args(campaign=CAMPAIGN), ctx)
    assert len(party["roster"]) == 2
    slots = {entry["slot"]: entry["character_id"] for entry in party["roster"]}
    assert slots == {1: "kira", 2: "bran"}

    row = ctx.conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        ("kira", CAMPAIGN),
    ).fetchone()
    assert json.loads(row["sheet_json"])["slot"] == 1

    cleared = handle_clear(_args(campaign=CAMPAIGN, slot=2), ctx)
    assert cleared["cleared"] is True
    after = handle_roster_show(_args(campaign=CAMPAIGN), ctx)
    assert len(after["roster"]) == 1


def test_create_rejects_ineligible_class(ctx):
    with pytest.raises(CharacterError):
        create_character(
            ctx.conn,
            campaign_slug=CAMPAIGN,
            display_name="Fail Mage",
            base_class="apprentice",
            attributes={"STR": 10, "AGI": 10, "STA": 10, "INT": 6, "SPI": 10, "LUC": 10},
        )

    out = handle_create(
        _args(
            campaign=CAMPAIGN,
            name="Fail Mage",
            base_class="apprentice",
            character_id="fail-mage",
            str=10,
            agi=10,
            sta=10,
            int=6,
            spi=10,
            luc=10,
            skills=None,
            roll_attributes=False,
        ),
        ctx,
    )
    assert out["ok"] is False
