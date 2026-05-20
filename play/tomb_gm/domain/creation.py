"""Full character creation pipeline (canon-aligned)."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from tomb_gm.domain.character import ATTRIBUTE_ORDER, CharacterError, roll_attribute_scores

GENETIC_TABLE = {1: -1, 2: 0, 3: 1, 4: 2}
ATTR_FLOOR = 1
ATTR_CEILING = 30


def _clamp_attrs(attrs: dict[str, int]) -> dict[str, int]:
    return {k: max(ATTR_FLOOR, min(ATTR_CEILING, attrs[k])) for k in ATTRIBUTE_ORDER}


def _load_json(content_root: Path, *parts: str) -> dict[str, Any]:
    path = content_root.joinpath(*parts)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(encoding="utf-8"))


def load_race(content_root: Path, race_id: str) -> dict[str, Any]:
    data = _load_json(content_root, "data", "races", "races.json")
    race = data.get("races", {}).get(race_id.lower())
    if not race:
        raise CharacterError(f"Unknown race: {race_id}")
    return {"id": race_id.lower(), **race}


def apply_modifiers(attrs: dict[str, int], mods: dict[str, int]) -> dict[str, int]:
    out = dict(attrs)
    for key, delta in mods.items():
        attr = key.upper()
        if attr in out:
            out[attr] = out[attr] + int(delta)
    return _clamp_attrs(out)


def apply_flexible_bonus(
    attrs: dict[str, int], count: int, targets: list[str] | None
) -> dict[str, int]:
    if count <= 0:
        return attrs
    out = dict(attrs)
    picks = targets or []
    if len(picks) < count:
        raise CharacterError(f"Need {count} flexible attribute targets, got {len(picks)}")
    for attr in picks[:count]:
        key = attr.upper()
        if key not in out:
            raise CharacterError(f"Invalid attribute for flexible bonus: {attr}")
        out[key] = out[key] + 1
    return _clamp_attrs(out)


def roll_genetics(rng: random.Random) -> tuple[dict[str, int], list[dict[str, Any]]]:
    mods: dict[str, int] = {}
    detail: list[dict[str, Any]] = []
    for attr in ATTRIBUTE_ORDER:
        natural = rng.randint(1, 4)
        delta = GENETIC_TABLE[natural]
        mods[attr] = delta
        detail.append({"attribute": attr, "die": "1d4", "natural": natural, "modifier": delta})
    return mods, detail


def roll_life_event(rng: random.Random, content_root: Path) -> tuple[dict[str, Any], list[int]]:
    data = _load_json(content_root, "data", "character", "life-events.json")
    d1 = rng.randint(1, 20)
    d2 = rng.randint(1, 20)
    total = d1 + d2
    event = next(
        (e for e in data["events"] if e["min"] <= total <= e["max"]),
        None,
    )
    if not event:
        raise CharacterError(f"No life event for roll {total}")
    return {**event, "roll": total, "dice": [d1, d2]}, [d1, d2]


def apply_life_event(
    attrs: dict[str, int],
    event: dict[str, Any],
    *,
    flexible_targets: list[str] | None = None,
) -> dict[str, int]:
    out = apply_modifiers(attrs, event.get("attributes") or {})
    flex = int(event.get("flexibleAttributes") or 0)
    if flex:
        out = apply_flexible_bonus(out, flex, flexible_targets)
    return out


def roll_starting_gold(
    rng: random.Random,
    base_class: str,
    life_event: dict[str, Any],
    content_root: Path,
) -> tuple[int, dict[str, Any]]:
    kits = _load_json(content_root, "data", "character", "starting-kits.json")
    base_gp = int(kits["baseClassGp"].get(base_class.lower(), 10))
    modifier = int(life_event.get("goldGp", 0))
    multiplier = rng.randint(1, 6)
    total = max(0, (base_gp + modifier) * multiplier)
    return total, {
        "baseClassGp": base_gp,
        "lifeEventModifier": modifier,
        "multiplier": multiplier,
        "totalGp": total,
    }


def starting_kit(content_root: Path, base_class: str) -> dict[str, Any]:
    kits = _load_json(content_root, "data", "character", "starting-kits.json")
    kit = kits["kits"].get(base_class.lower())
    if not kit:
        raise CharacterError(f"No starting kit for class: {base_class}")
    return kit


def starting_kit_inventory(content_root: Path, base_class: str) -> dict[str, Any]:
    """Build unified v3 inventory from class starting kit."""
    from tomb_gm.domain.inventory import empty_inventory, kit_to_pack
    from tomb_gm.services.content import ContentService

    kit = starting_kit(content_root, base_class)
    content = ContentService(content_root)
    pack = kit_to_pack(kit.get("items", []), item_lookup=content.items_lookup())
    inv = empty_inventory()
    inv["pack"] = pack
    return inv


def run_creation_pipeline(
    *,
    content_root: Path,
    base_class: str,
    race_id: str | None,
    human_bonus: list[str] | None,
    life_event_flexible: list[str] | None,
    rng: random.Random,
    skip_genetics: bool = False,
    skip_life_event: bool = False,
    attributes: dict[str, int] | None = None,
) -> dict[str, Any]:
    """GM rolls full pipeline; returns audit trail + final attributes."""
    audit: dict[str, Any] = {}

    if attributes:
        attrs = _clamp_attrs({k: attributes[k] for k in ATTRIBUTE_ORDER})
        audit["attributes"] = {"method": "assigned", "scores": attrs}
    else:
        attrs, detail = roll_attribute_scores(rng)
        audit["attributes"] = {"method": "1d10", "scores": attrs, "detail": detail}

    if not skip_genetics:
        gmods, gdetail = roll_genetics(rng)
        attrs = apply_modifiers(attrs, gmods)
        audit["genetics"] = {"modifiers": gmods, "detail": gdetail}

    life_ev: dict[str, Any] | None = None
    if not skip_life_event:
        life_ev, dice = roll_life_event(rng, content_root)
        attrs = apply_life_event(attrs, life_ev, flexible_targets=life_event_flexible)
        audit["life_event"] = {"event": life_ev, "dice": dice}

    if race_id:
        race = load_race(content_root, race_id)
        attrs = apply_modifiers(attrs, race.get("adjustments") or {})
        flex = int(race.get("flexibleBonus") or 0)
        if flex:
            attrs = apply_flexible_bonus(attrs, flex, human_bonus)
        audit["race"] = {"id": race["id"], "displayName": race.get("displayName")}

    gold, gold_detail = roll_starting_gold(
        rng, base_class, life_ev or {"goldGp": 0}, content_root
    )
    kit = starting_kit(content_root, base_class)
    remaining_gp = max(0, gold - int(kit["costGp"]))

    audit["gold"] = gold_detail
    audit["kit"] = kit
    audit["remainingGp"] = remaining_gp
    audit["final_attributes"] = attrs

    return {
        "attributes": attrs,
        "raceId": race_id,
        "life_event": life_ev,
        "goldGp": remaining_gp,
        "kit": kit,
        "audit": audit,
    }
