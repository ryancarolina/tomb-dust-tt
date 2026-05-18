"""Loot table rolls for site search and post-combat."""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any

DICE_RE = re.compile(r"^(\d+)d(\d+)(?:\+(\d+))?$")


def _roll_dice(expr: str, rng: random.Random) -> int:
    expr = expr.strip().lower()
    m = DICE_RE.match(expr)
    if not m:
        return int(expr)
    count, sides, bonus = m.groups()
    total = sum(rng.randint(1, int(sides)) for _ in range(int(count)))
    if bonus:
        total += int(bonus)
    return total


def _weighted_pick(items: list[dict[str, Any]], rng: random.Random) -> str | None:
    if not items:
        return None
    weights = [int(i.get("weight", 1)) for i in items]
    total = sum(weights)
    roll = rng.randint(1, total)
    acc = 0
    for item, w in zip(items, weights):
        acc += w
        if roll <= acc:
            return str(item["id"])
    return str(items[-1]["id"])


def roll_loot_table(
    content_root: Path,
    tier: str,
    *,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    roller = rng or random.Random()
    path = content_root / "data" / "loot" / "tables.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    table = data.get("tables", {}).get(tier)
    if not table:
        return {"ok": False, "error": f"unknown loot tier: {tier}"}

    natural = roller.randint(1, 6)
    gp = 0
    items: list[str] = []
    currency = table.get("currencyGp") or {}
    item_pool = table.get("items") or []

    if natural <= 3:
        gp = roller.randint(int(currency.get("min", 0)), int(currency.get("max", 0)))
    elif natural <= 5:
        picked = _weighted_pick(item_pool, roller)
        if picked:
            items.append(picked)
    else:
        gp = roller.randint(int(currency.get("min", 0)), int(currency.get("max", 0)))
        picked = _weighted_pick(item_pool, roller)
        if picked:
            items.append(picked)

    if currency.get("dice") and gp == 0:
        gp = _roll_dice(str(currency["dice"]), roller)

    return {
        "ok": True,
        "tier": tier,
        "procedure_die": natural,
        "gp": gp,
        "items": items,
        "rollProcedure": table.get("rollProcedure"),
    }
