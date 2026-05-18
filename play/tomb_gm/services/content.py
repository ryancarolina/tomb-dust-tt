from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


class ContentService:
    """Read-only loaders for build/data JSON under content_root."""

    def __init__(self, content_root: Path) -> None:
        self.content_root = content_root.resolve()

    @lru_cache(maxsize=1)
    def load_av_grid(self) -> dict[str, Any]:
        path = self.content_root / "data" / "av-grid" / "av-grid.json"
        if not path.is_file():
            raise FileNotFoundError(f"Missing AV-GRID: {path}")
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)

    @lru_cache(maxsize=1)
    def load_av_grid_index(self) -> dict[str, Any]:
        path = self.content_root / "data" / "av-grid" / "index.json"
        if not path.is_file():
            raise FileNotFoundError(f"Missing AV-GRID index: {path}")
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)

    def get_cell(self, address: str) -> dict[str, Any] | None:
        return self.load_av_grid().get("addresses", {}).get(address)

    def list_address_ids(self) -> list[str]:
        return list(self.load_av_grid_index().get("addressIds", []))

    def cell_payload(self, address: str) -> dict[str, Any] | None:
        entry = self.get_cell(address)
        if entry is None:
            return None
        return {
            "address": entry["id"],
            "displayName": entry.get("displayName"),
            "summary": entry.get("summary"),
            "column": entry.get("column"),
            "row": entry.get("row"),
            "surfaceRoot": entry.get("surfaceRoot"),
            "layerStack": entry.get("layerStack", []),
            "biomes": entry.get("biomes", []),
            "region": entry.get("region"),
            "dangerRating": entry.get("dangerRating"),
            "registry": entry.get("registry"),
            "links": entry.get("links", {}),
            "tags": entry.get("tags", []),
            "parent": entry.get("parent"),
            "childAddresses": entry.get("childAddresses", []),
        }

    def load_monster(
        self, monster_id: str, *, tier: str | None = None
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """Return (monster_json, blocker) — blocker set when JSON file is missing."""
        path = self.content_root / "data" / "monsters" / f"{monster_id}.json"
        if not path.is_file():
            return None, {
                "code": "MISSING_MONSTER_JSON",
                "monster_id": monster_id,
                "message": (
                    f"Add build/data/monsters/{monster_id}.json "
                    "or remove from encounter table"
                ),
            }
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        if tier:
            blocks = data.get("statBlocks", [])
            match = next((b for b in blocks if b.get("tier") == tier or b.get("id") == tier), None)
            if match:
                data = {**data, "selectedStatBlock": match}
        return data, None

    @lru_cache(maxsize=1)
    def _weapons_index(self) -> dict[str, dict[str, Any]]:
        path = self.content_root / "data" / "weapons" / "weapons.json"
        if not path.is_file():
            return {}
        with path.open(encoding="utf-8") as fh:
            items = json.load(fh)
        return {w["id"]: w for w in items if isinstance(w, dict) and "id" in w}

    def load_weapon(self, weapon_id: str) -> dict[str, Any] | None:
        return self._weapons_index().get(weapon_id)

    @lru_cache(maxsize=1)
    def _spells_index(self) -> dict[str, dict[str, Any]]:
        path = self.content_root / "data" / "spells" / "spells.json"
        if not path.is_file():
            return {}
        with path.open(encoding="utf-8") as fh:
            items = json.load(fh)
        return {s["id"]: s for s in items if isinstance(s, dict) and "id" in s}

    def load_spell(self, spell_id: str) -> dict[str, Any] | None:
        return self._spells_index().get(spell_id)

    def load_site(self, site_id: str) -> dict[str, Any] | None:
        path = self.content_root / "data" / "sites" / f"{site_id}.json"
        if not path.is_file():
            return None
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)

    def load_npc_doc(self, npc_id: str) -> dict[str, Any] | None:
        path = self.content_root / "systems" / "npcs" / f"{npc_id}.md"
        if not path.is_file():
            return None
        text = path.read_text(encoding="utf-8")
        title = npc_id
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        return {
            "id": npc_id,
            "displayName": title,
            "path": str(path.relative_to(self.content_root)).replace("\\", "/"),
            "excerpt": text[:1200],
        }

    def search_cells_by_region(self, region: str) -> list[dict[str, Any]]:
        region_lower = region.lower()
        out: list[dict[str, Any]] = []
        for addr in self.list_address_ids():
            cell = self.cell_payload(addr)
            if cell and str(cell.get("region", "")).lower() == region_lower:
                out.append(cell)
        return out
