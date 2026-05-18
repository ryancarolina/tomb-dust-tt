"""Deed promotion eligibility from build/data/deeds/promotions.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_promotions(content_root: Path) -> dict[str, Any]:
    path = content_root / "data" / "deeds" / "promotions.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _counter_met(sheet: dict[str, Any], account: dict[str, Any], spec: dict[str, Any]) -> bool:
    ctype = spec["type"]
    target = int(spec.get("target", 1))
    if ctype == "flag":
        name = spec.get("name", "")
        flags = {**sheet.get("flags", {}), **account.get("flags", {})}
        return bool(flags.get(name)) == bool(spec.get("value", True))
    counters = {**sheet.get("deed_counters", {}), **account.get("deed_counters", {})}
    return int(counters.get(ctype, 0)) >= target


def deeds_check(
    content_root: Path,
    *,
    sheet: dict[str, Any],
    account_state: dict[str, Any],
) -> dict[str, Any]:
    data = load_promotions(content_root)
    class_id = sheet.get("classId")
    tier = int(sheet.get("classTier", 1))
    eligible: list[dict[str, Any]] = []
    for promo in data.get("promotions", []):
        if promo.get("fromClassId") != class_id or int(promo.get("fromTier", 0)) != tier:
            continue
        reqs = promo.get("counters", [])
        if all(_counter_met(sheet, account_state, r) for r in reqs):
            eligible.append(
                {
                    "id": promo["id"],
                    "toClassId": promo["toClassId"],
                    "toTier": promo.get("toTier"),
                }
            )
    return {"ok": True, "eligible": eligible, "class_id": class_id, "class_tier": tier}
