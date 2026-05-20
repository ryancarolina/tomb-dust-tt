"""Combat sheet resolves weapon skillId from catalog."""

from __future__ import annotations

from pathlib import Path

from tomb_gm.domain.combat_sheet import attack_modifiers_from_sheet
from tomb_gm.domain.inventory import new_instance

ROOT = Path(__file__).resolve().parents[3]
CONTENT = ROOT / "build"


def test_attack_uses_weapon_skill_id_from_catalog():
    from tomb_gm.services.content import ContentService

    content = ContentService(CONTENT)
    lookup = content.items_lookup()
    pack = [
        new_instance("spear", kind="weapon", equipped=True, slot="mainHand", catalog=lookup["spear"]),
    ]
    sheet = {
        "classTier": 1,
        "attributes": {"STR": 14, "AGI": 10},
        "skills": [{"skillId": "polearm-proficiency", "level": 4}],
        "inventory": {"inventoryVersion": 3, "pack": pack},
    }
    mods = attack_modifiers_from_sheet(sheet, content_root=CONTENT)
    assert mods["skill_id"] == "polearm-proficiency"
    assert mods["skill_level"] == 4
    assert mods["weapon_id"] == "spear"
