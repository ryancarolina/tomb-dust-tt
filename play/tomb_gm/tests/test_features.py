from __future__ import annotations

import argparse
import random

import pytest

from helpers import REPO, seed_campaign
from tomb_gm.cli.cmd_character import handle_create
from tomb_gm.domain.creation import load_race, run_creation_pipeline
from tomb_gm.services.encounters import wilderness_travel_roll

CAMPAIGN = "features-test"


@pytest.fixture()
def ctx(command_ctx):
    seed_campaign(command_ctx.conn, CAMPAIGN, "Features")
    command_ctx.conn.execute("DELETE FROM characters WHERE campaign_slug = ?", (CAMPAIGN,))
    command_ctx.conn.commit()
    return command_ctx


def test_load_race_human():
    race = load_race(REPO / "build", "human")
    assert race["flexibleBonus"] == 2


def test_full_creation_pipeline_seeded():
    out = run_creation_pipeline(
        content_root=REPO / "build",
        base_class="militia",
        race_id="dwarf",
        human_bonus=None,
        life_event_flexible=None,
        rng=random.Random(42),
    )
    assert out["attributes"]["STA"] >= 1
    assert out["raceId"] == "dwarf"
    assert "audit" in out


def test_character_create_full(ctx):
    out = handle_create(
        argparse.Namespace(
            workspace=str(ctx.config.workspace),
            campaign=CAMPAIGN,
            name="Full Test",
            base_class="militia",
            character_id=None,
            str=None,
            agi=None,
            sta=None,
            int=None,
            spi=None,
            luc=None,
            skills=None,
            roll_attributes=False,
            race="human",
            human_bonus="STR,INT",
            life_flex=None,
            full=True,
            no_kit=False,
            seed=99,
        ),
        ctx,
    )
    assert out["ok"] is True, out
    assert out.get("race_id") == "human"
    assert out.get("creation_audit")


def test_wilderness_roll_seeded():
    result = wilderness_travel_roll(
        REPO / "build",
        biomes=["HL"],
        danger="skirmisher",
        rng=random.Random(1),
    )
    assert result["ok"] is True
    assert "travel_die" in result
