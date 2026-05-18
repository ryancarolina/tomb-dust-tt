"""Wilderness and encounter table resolution."""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any

MONSTER_COUNT_RE = re.compile(
    r"(?:(\d+)d(\d+))?\s*([a-z0-9-]+)",
    re.IGNORECASE,
)


def load_wilderness(content_root: Path) -> dict[str, Any]:
    path = content_root / "data" / "encounters" / "wilderness.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_roll_range(spec: str) -> tuple[int, int]:
    if "-" in spec:
        a, b = spec.split("-", 1)
        return int(a), int(b)
    n = int(spec)
    return n, n


def _match_d6_entry(table: list[dict[str, Any]], natural: int) -> dict[str, Any]:
    for row in table:
        lo, hi = _parse_roll_range(str(row["roll"]))
        if lo <= natural <= hi:
            return row
    return table[-1]


def parse_monster_specs(result_text: str) -> list[str]:
    """Parse encounter result like '1d2 thornwolf' into monster CLI specs."""
    text = result_text.strip().lower()
    if "no encounter" in text:
        return []
    specs: list[str] = []
    for part in re.split(r"\s*\+\s*|\s+and\s+", text):
        part = part.strip()
        if not part or part in ("skirmisher", "hazard", "elite", "rogue"):
            continue
        m = MONSTER_COUNT_RE.search(part)
        if not m:
            continue
        dice, sides, mid = m.groups()
        if dice and sides:
            count = sum(random.randint(1, int(sides)) for _ in range(int(dice)))
        else:
            count = 1
        if count > 0:
            specs.append(f"{mid}:{count}")
    return specs


def wilderness_travel_roll(
    content_root: Path,
    *,
    biomes: list[str],
    danger: str,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    roller = rng or random.Random()
    data = load_wilderness(content_root)
    biome_code = biomes[0] if biomes else "HL"
    biome = data.get("biomes", {}).get(biome_code)
    if not biome:
        return {"ok": False, "error": f"unknown biome: {biome_code}"}

    travel_die = roller.randint(1, 6)
    out: dict[str, Any] = {
        "ok": True,
        "procedure": data.get("procedure"),
        "biome": biome_code,
        "danger": danger,
        "travel_die": travel_die,
        "encounter_triggered": travel_die == 1,
    }
    if travel_die != 1:
        out["result"] = "No encounter on travel die"
        return out

    table = biome.get("tables", {}).get(danger) or biome.get("tables", {}).get("skirmisher")
    if not table:
        return {"ok": False, "error": f"no table for danger {danger}"}

    encounter_die = roller.randint(1, 6)
    row = _match_d6_entry(table["d6"], encounter_die)
    out["encounter_die"] = encounter_die
    out["result"] = row.get("result", "")
    out["monster_specs"] = parse_monster_specs(out["result"])
    return out
