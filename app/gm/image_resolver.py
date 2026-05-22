"""Entity trigger resolver for IllustrationPanel image requests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tomb_gm.services.content import ContentService


class ImageResolver:
    KEY_NPC_VOICES = {
        "marshal-garrick-holt",
        "isla-brack",
        "elder-marin",
        "mira-ashret",
        "archivist-thessaly-vorn",
        "lyra-the-stormcaller",
    }

    SKIP_VOICES = {
        "narrator",
        "gm",
        "player",
        "npc",
        "postern-clerk",
        "breley-sergeant",
        "npc-male",
        "npc-female",
    }

    PRIORITY_MONSTER = 2
    PRIORITY_NPC = 3
    PRIORITY_ROOM = 4
    PRIORITY_SITE = 5
    PRIORITY_LOCATION = 5

    def __init__(self, content_root: Path | None = None) -> None:
        root = content_root or (Path(__file__).resolve().parents[2] / "build")
        self._content = ContentService(root)
        self._site_slug_by_primary_address: dict[str, str] | None = None

    def voice_to_npc_id(self, voice: str | None) -> str | None:
        if not voice:
            return None
        normalized = str(voice).strip().lower()
        if normalized in self.SKIP_VOICES:
            return None
        if normalized in self.KEY_NPC_VOICES:
            return normalized
        return None

    def primary_key_npc_from_lines(self, lines: list[dict[str, Any]]) -> str | None:
        for line in reversed(lines or []):
            npc_id = self.voice_to_npc_id(line.get("voice"))
            if npc_id:
                return npc_id
        return None

    def detect_entities(
        self,
        prev: dict[str, Any] | None,
        curr: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Detect status-delta entity triggers for IllustrationPanel."""
        prev = prev or {}
        curr = curr or {}
        out: list[dict[str, Any]] = []

        prev_combat = prev.get("combat") if isinstance(prev.get("combat"), dict) else None
        curr_combat = curr.get("combat") if isinstance(curr.get("combat"), dict) else None
        combat_appeared = prev_combat is None and curr_combat is not None
        monster_turn = self._is_monster_turn(curr_combat)
        if curr_combat and (combat_appeared or monster_turn):
            monster_id = self._monster_id_for_active_turn(curr_combat)
            if not monster_id:
                monster_ids = self._monster_ids_from_combatants(curr_combat)
                monster_id = monster_ids[0] if monster_ids else None
            if monster_id:
                out.append(
                    {
                        "entity_type": "monster",
                        "entity_id": monster_id,
                        "priority": self.PRIORITY_MONSTER,
                    }
                )

        prev_party = prev.get("party") if isinstance(prev.get("party"), dict) else {}
        curr_party = curr.get("party") if isinstance(curr.get("party"), dict) else {}
        prev_mode = str(prev_party.get("mode") or "").lower()
        curr_mode = str(curr_party.get("mode") or "").lower()
        prev_address = str(prev_party.get("address") or "").strip()
        curr_address = str(curr_party.get("address") or "").strip()
        if (
            curr_mode == "surface"
            and curr_address
            and curr_address != prev_address
        ):
            out.append(
                {
                    "entity_type": "location",
                    "entity_id": curr_address,
                    "priority": self.PRIORITY_LOCATION,
                }
            )

        prev_site_id = str(prev_party.get("site_id") or "").strip()
        curr_site_id = str(curr_party.get("site_id") or "").strip()
        entered_dungeon = curr_mode == "dungeon" and prev_mode != "dungeon"
        site_newly_set = bool(curr_site_id and curr_site_id != prev_site_id)
        site_slug = self._resolve_site_slug(curr_party)
        if site_slug and (entered_dungeon or site_newly_set):
            out.append(
                {
                    "entity_type": "site",
                    "entity_id": site_slug,
                    "priority": self.PRIORITY_SITE,
                }
            )

        prev_room_id = str(prev_party.get("dungeon_room_id") or "").strip()
        curr_room_id = str(curr_party.get("dungeon_room_id") or "").strip()
        if site_slug and curr_room_id and curr_room_id != prev_room_id:
            out.append(
                {
                    "entity_type": "room",
                    "entity_id": f"{site_slug}__{curr_room_id}",
                    "priority": self.PRIORITY_ROOM,
                }
            )
        return out

    def pick_winner(
        self,
        entities: list[dict[str, Any]],
        *,
        item_selected: bool,
        npc_id: str | None,
    ) -> dict[str, Any] | None:
        if item_selected:
            return None
        candidates = list(entities or [])
        if npc_id:
            candidates.append(
                {
                    "entity_type": "npc",
                    "entity_id": npc_id,
                    "priority": self.PRIORITY_NPC,
                }
            )
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda entry: (
                int(entry.get("priority", 99)),
                str(entry.get("entity_type", "")),
                str(entry.get("entity_id", "")),
            ),
        )

    def _is_monster_turn(self, combat: dict[str, Any] | None) -> bool:
        if not combat:
            return False
        if str(combat.get("turn_kind") or "").lower() == "monster":
            return True
        turn_id = str(combat.get("turn_id") or "")
        if not turn_id:
            return False
        for combatant in combat.get("combatants") or []:
            if str(combatant.get("id") or "") == turn_id:
                return str(combatant.get("kind") or "").lower() == "monster"
        return False

    def _monster_id_for_active_turn(self, combat: dict[str, Any]) -> str | None:
        turn_id = str(combat.get("turn_id") or "")
        if not turn_id:
            return None
        for combatant in combat.get("combatants") or []:
            if str(combatant.get("id") or "") != turn_id:
                continue
            monster_id = str(combatant.get("monsterId") or "").strip()
            if monster_id:
                return monster_id
        return None

    def _monster_ids_from_combatants(self, combat: dict[str, Any]) -> list[str]:
        ids: list[str] = []
        seen: set[str] = set()
        for combatant in combat.get("combatants") or []:
            monster_id = str(combatant.get("monsterId") or "").strip()
            if not monster_id or monster_id in seen:
                continue
            ids.append(monster_id)
            seen.add(monster_id)
        return ids

    def _resolve_site_slug(self, party: dict[str, Any]) -> str | None:
        site_id = str(party.get("site_id") or "").strip()
        if site_id and self._content.load_site(site_id):
            return site_id
        for address in (site_id, str(party.get("address") or "").strip()):
            if not address:
                continue
            slug = self._site_map().get(address)
            if slug:
                return slug
        return None

    def _site_map(self) -> dict[str, str]:
        if self._site_slug_by_primary_address is not None:
            return self._site_slug_by_primary_address
        lookup: dict[str, str] = {}
        sites_dir = self._content.content_root / "data" / "sites"
        for path in sorted(sites_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            slug = str(data.get("id") or path.stem).strip()
            primary = str(data.get("primaryAddress") or "").strip()
            if slug and primary:
                lookup[primary] = slug
        self._site_slug_by_primary_address = lookup
        return lookup
