from __future__ import annotations

from pathlib import Path

import pytest

from gm.image_prompt_builder import ImagePromptBuilder


def _builder() -> ImagePromptBuilder:
    root = Path(__file__).resolve().parents[2]
    return ImagePromptBuilder(root / "build")


def test_prompt_builder_npc_sanitizes_burn_scarred_wording():
    prompt = _builder().build_prompt("npc", "marshal-garrick-holt")
    lower = prompt.lower()
    assert "burn-scarred" not in lower
    assert "burn scarred" not in lower
    assert "weathered left gauntlet" in lower
    assert "1980s tabletop fantasy rpg cover painting" in lower


@pytest.mark.parametrize(
    ("entity_type", "entity_id"),
    [
        ("monster", "grave-ghoul"),
        ("location", "32-C"),
        ("site", "breley-undercrypt"),
        ("room", "breley-undercrypt__chapel-stairs"),
        ("item", "longsword"),
    ],
)
def test_prompt_builder_supports_all_entity_types(entity_type: str, entity_id: str):
    prompt = _builder().build_prompt(entity_type, entity_id)
    lower = prompt.lower()
    assert len(prompt.split()) >= 40
    assert "deckled edges" in lower
    assert "tsr" not in lower
    assert "dungeons and dragons" not in lower


def test_prompt_builder_rejects_unknown_entity_type():
    with pytest.raises(ValueError):
        _builder().build_prompt("unknown", "id-1")
