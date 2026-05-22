"""APP-027 V9: engine validate_monster_specs unit tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLAY = Path(__file__).resolve().parents[1]
REPO = PLAY.parents[1]
BUILD = REPO / "build"

if str(PLAY) not in sys.path:
    sys.path.insert(0, str(PLAY))

from tomb_gm.services.simulation.combat import validate_monster_specs


@pytest.fixture
def content_root() -> Path:
    return BUILD


def test_validate_empty_list(content_root: Path):
    assert validate_monster_specs(content_root, []) == "monster_specs required"


def test_validate_invalid_format(content_root: Path):
    err = validate_monster_specs(content_root, ["not a spec"])
    assert err is not None
    assert "invalid monster spec" in err


def test_validate_unknown_monster_json(content_root: Path):
    err = validate_monster_specs(content_root, ["hollow-knight:1"])
    assert err is not None
    assert "monster JSON not found: hollow-knight" in err


def test_validate_canon_grave_ghoul(content_root: Path):
    assert validate_monster_specs(content_root, ["grave-ghoul:1"]) is None
