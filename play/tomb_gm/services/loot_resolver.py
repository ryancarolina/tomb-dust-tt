"""Composable loot resolution and mechanical grant to character sheets."""

from __future__ import annotations

import json
import random
import sqlite3
from pathlib import Path
from typing import Any

from tomb_gm.domain.inventory import add_item, ensure_normalized
from tomb_gm.services.content import ContentService
from tomb_gm.services.hub import active_delver_id


def load_loot_id_migration(content_root: Path) -> dict[str, str]:
    path = content_root / "data" / "loot" / "lootIdMigration.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    migrations = data.get("migrations") or {}
    return {str(k): str(v) for k, v in migrations.items()}


def migrate_loot_item_id(item_id: str, migration: dict[str, str]) -> str:
    return migration.get(item_id, item_id)


class LootResolver:
    """Roll loot tables (v1 adapter today; v2 refs reserved)."""

    def __init__(self, content_root: Path) -> None:
        self.content_root = content_root
        self._migration: dict[str, str] | None = None

    @property
    def migration(self) -> dict[str, str]:
        if self._migration is None:
            self._migration = load_loot_id_migration(self.content_root)
        return self._migration

    def roll(
        self,
        *,
        tier: str | None = None,
        loot_table_ref: str | None = None,
        danger_rating: str | None = None,
        rng: random.Random | None = None,
    ) -> dict[str, Any]:
        from tomb_gm.services.loot import roll_loot_table

        resolved_tier = tier or danger_rating or "skirmisher"
        if loot_table_ref:
            tables_path = self.content_root / "data" / "loot" / "tables.json"
            if tables_path.is_file():
                site_links = json.loads(tables_path.read_text(encoding="utf-8")).get("siteLinks") or {}
                resolved_tier = site_links.get(loot_table_ref, resolved_tier)

        result = roll_loot_table(self.content_root, resolved_tier, rng=rng)
        if not result.get("ok"):
            return result

        grants: list[dict[str, Any]] = []
        for raw_id in result.get("items") or []:
            item_id = migrate_loot_item_id(str(raw_id), self.migration)
            grants.append({"itemId": item_id, "quantity": 1})

        return {
            "ok": True,
            "tier": resolved_tier,
            "gp": int(result.get("gp", 0)),
            "grants": grants,
            "procedure_die": result.get("procedure_die"),
            "rollProcedure": result.get("rollProcedure"),
        }


def grant_loot(
    conn: sqlite3.Connection,
    content: ContentService,
    *,
    campaign_slug: str,
    loot_result: dict[str, Any],
    character_id: str | None = None,
) -> dict[str, Any]:
    """Persist rolled loot onto a living character sheet (default: active delver)."""
    char_id = character_id or active_delver_id(conn, campaign_slug)
    if not char_id:
        return {"ok": False, "error": "no living character for loot grant"}

    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ? AND alive = 1",
        (char_id, campaign_slug),
    ).fetchone()
    if not row:
        return {"ok": False, "error": f"Character not found or dead: {char_id}"}

    sheet = json.loads(row["sheet_json"])
    lookup = content.items_lookup()
    ensure_normalized(sheet, item_lookup=lookup)

    gp_gain = int(loot_result.get("gp", 0))
    if gp_gain:
        sheet["goldGp"] = int(sheet.get("goldGp", 0)) + gp_gain

    granted: list[dict[str, Any]] = []
    for grant in loot_result.get("grants") or []:
        item_id = migrate_loot_item_id(str(grant["itemId"]), load_loot_id_migration(content.content_root))
        qty = int(grant.get("quantity", 1))
        catalog = content.load_item(item_id)
        instance_ids = add_item(sheet, item_id, quantity=qty, catalog=catalog)
        granted.append({"itemId": item_id, "quantity": qty, "instanceIds": instance_ids})

    conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
        (json.dumps(sheet), char_id, campaign_slug),
    )
    conn.commit()
    return {
        "ok": True,
        "character_id": char_id,
        "gp": gp_gain,
        "grants": granted,
        "goldGp": int(sheet.get("goldGp", 0)),
    }
