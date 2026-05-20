from __future__ import annotations

import random

import pytest

from helpers import seed_campaign
from tomb_gm.cli.cmd_character import handle_create
from tomb_gm.cli.cmd_core import handle_status
from tomb_gm.cli.cmd_roll import handle_attributes
from tomb_gm.domain.character import roll_attribute_scores, standard_attribute_pool

CAMPAIGN = "roll-attr-test"


@pytest.fixture()
def ctx(command_ctx):
    seed_campaign(command_ctx.conn, CAMPAIGN, "Roll Attr Test")
    command_ctx.conn.execute("DELETE FROM characters WHERE campaign_slug = ?", (CAMPAIGN,))
    command_ctx.conn.commit()
    return command_ctx


def test_roll_attribute_scores_range():
    scores, detail = roll_attribute_scores(random.Random(42))
    assert set(scores) == {"STR", "AGI", "STA", "INT", "SPI", "LUC"}
    assert all(1 <= v <= 10 for v in scores.values())
    assert len(detail) == 6


def test_standard_array_pool():
    meta, pool = standard_attribute_pool()
    assert meta["method"] == "standard-array"
    assert sorted(pool, reverse=True) == [15, 14, 13, 12, 10, 8]


def test_handle_attributes_roll(ctx, args_ns):
    out = handle_attributes(
        args_ns(method="roll", seed=99),
        ctx,
    )
    assert out["ok"] is True
    assert "attributes" in out


def test_handle_attributes_standard_array(ctx, args_ns):
    out = handle_attributes(
        args_ns(method="standard-array", seed=None),
        ctx,
    )
    assert out["ok"] is True
    assert out["method"] == "standard-array"
    assert "pool" in out


def test_create_with_rolled_attributes(ctx, args_ns):
    handle_create(
        args_ns(
            campaign=CAMPAIGN,
            name="Roller",
            base_class="militia",
            character_id="roller",
            str=10,
            agi=10,
            sta=10,
            int=10,
            spi=10,
            luc=10,
            skills=None,
            roll_attributes=False,
        ),
        ctx,
    )
    status = handle_status(args_ns(), ctx)
    assert status["ok"] is True
