"""Canon-driven prompt builder for AI image generation."""

from __future__ import annotations

import re
from pathlib import Path

from tomb_gm.services.content import ContentService

ENTITY_TYPES = {"npc", "monster", "location", "site", "room", "item"}

_STYLE_SUFFIX = (
    "Hand-painted oil illustration on worn illustration board with subtle paper grain "
    "and deckled edges, 1980s tabletop fantasy RPG cover painting, heroic Western "
    "fantasy realism, visible brushstrokes, dramatic directional lighting and "
    "chiaroscuro, natural saturated tones, detailed armor engravings, muted earth "
    "palette with {accent} accent, painterly skin and weathered metal, {environment}, "
    "plain textured background without written words."
)

_BANNED_TERMS = (
    "tsr",
    "advanced dungeons and dragons",
    "dungeons and dragons",
    "larry elmore",
    "jeff easley",
    "burn-scarred",
    "burn scarred",
)


def _safe_text(value: str) -> str:
    text = " ".join((value or "").split())
    text = text.replace("burn-scarred", "weathered left gauntlet with old battle marks")
    text = text.replace("burn scarred", "weathered left gauntlet with old battle marks")
    text = text.replace("TSR", "tabletop")
    text = text.replace("tsr", "tabletop")
    for phrase in (
        "Advanced Dungeons and Dragons",
        "Dungeons and Dragons",
        "Larry Elmore",
        "Jeff Easley",
    ):
        text = text.replace(phrase, "classic fantasy")
    return text


def _titleize(token: str) -> str:
    return token.replace("-", " ").replace("_", " ").title()


class ImagePromptBuilder:
    def __init__(self, content_root: Path) -> None:
        self._content = ContentService(content_root)

    def sanitize_prompt(self, prompt: str) -> str:
        sanitized = _safe_text(prompt)
        for term in _BANNED_TERMS:
            sanitized = re.sub(re.escape(term), "weathered", sanitized, flags=re.IGNORECASE)
        return " ".join(sanitized.split())

    def build_prompt(self, entity_type: str, entity_id: str) -> str:
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        if entity_type == "npc":
            prompt = self._build_npc_prompt(entity_id)
        elif entity_type == "monster":
            prompt = self._build_monster_prompt(entity_id)
        elif entity_type == "location":
            prompt = self._build_location_prompt(entity_id)
        elif entity_type == "site":
            prompt = self._build_site_prompt(entity_id)
        elif entity_type == "room":
            prompt = self._build_room_prompt(entity_id)
        else:
            prompt = self._build_item_prompt(entity_id)
        return self.sanitize_prompt(prompt)

    def build_item(self, item_id: str) -> str:
        """Build and sanitize an item-specific illustration prompt."""
        return self.sanitize_prompt(self._build_item_prompt(item_id))

    def _style_suffix(self, *, accent: str, environment: str) -> str:
        return _STYLE_SUFFIX.format(accent=accent, environment=environment)

    def _build_npc_prompt(self, npc_id: str) -> str:
        doc = self._content.load_npc_doc(npc_id) or {}
        name = str(doc.get("displayName") or _titleize(npc_id))
        excerpt = str(doc.get("excerpt") or "")
        appearance = ""
        m = re.search(r"\*\*Appearance:\*\*\s*(.+)", excerpt)
        if m:
            appearance = m.group(1).strip()
        appearance = _safe_text(appearance or "battle-worn delver marshal in practical armor.")
        subject = (
            f"{name}, three-quarter portrait bust, calm commanding stance, "
            f"{appearance}."
        )
        return f"{subject} {self._style_suffix(accent='Breley blue', environment='stone keep ward interior')}"

    def _build_monster_prompt(self, monster_id: str) -> str:
        monster, _blocker = self._content.load_monster(monster_id)
        display = _titleize(monster_id)
        desc = ""
        if monster:
            display = str(monster.get("displayName") or display)
            lore = monster.get("lore") or {}
            desc = str(lore.get("description") or "")
        subject = (
            f"{display}, menacing full-body portrait with grim posture, "
            f"{_safe_text(desc) or 'predatory undead menace with ritual grime and cracked claws.'}"
        )
        return f"{subject} {self._style_suffix(accent='sickly moonlight green', environment='ruined crypt atmosphere')}"

    def _build_location_prompt(self, address: str) -> str:
        cell = self._content.cell_payload(address) or {}
        display = str(cell.get("displayName") or address)
        summary = _safe_text(str(cell.get("summary") or "windswept extraction frontier cell."))
        biomes = cell.get("biomes") or []
        biome_text = ", ".join(str(b) for b in biomes[:2]) if biomes else "scrubland"
        subject = (
            f"{display} ({address}), wide environmental scene with no characters, "
            f"{summary} Foreground terrain shows {biome_text} features and Registry trail markers."
        )
        return f"{subject} {self._style_suffix(accent='ashen amber', environment='storm-lit wilderness horizon')}"

    def _build_site_prompt(self, site_id: str) -> str:
        site = self._content.load_site(site_id) or {}
        display = str(site.get("displayName") or _titleize(site_id))
        danger = str(site.get("dangerRating") or "skirmisher")
        subject = (
            f"{display}, dungeon entry vista at twilight, collapsed masonry and ward sigils, "
            f"threat level evokes {danger} danger in an extraction delver campaign."
        )
        return f"{subject} {self._style_suffix(accent='cold teal', environment='subterranean gate with torch haze')}"

    def _build_room_prompt(self, room_id: str) -> str:
        site_slug, node_id = self._split_room_id(room_id)
        site = self._content.load_site(site_slug) or {}
        node_display = _titleize(node_id)
        for node in site.get("nodes") or []:
            if str(node.get("id")) == node_id:
                node_display = str(node.get("displayName") or node_display)
                break
        subject = (
            f"{node_display} inside {str(site.get('displayName') or _titleize(site_slug))}, "
            "interior room scene with carved stone, relic clutter, and cautious delver route markings."
        )
        return f"{subject} {self._style_suffix(accent='torch gold', environment='tight chamber lit by braziers and dust')}"

    def _build_item_prompt(self, item_id: str) -> str:
        item = self._content.load_item(item_id) or {}
        display = str(item.get("displayName") or _titleize(item_id))
        desc = _safe_text(str(item.get("description") or "field-ready adventuring equipment."))
        subject = (
            f"{display}, isolated item study with parchment-framed composition on a worn timber tabletop, "
            f"{desc} Emphasize material wear, practical craftsmanship, and delver utility."
        )
        return f"{subject} {self._style_suffix(accent='iron-gray', environment='quiet workshop backdrop')}"

    @staticmethod
    def _split_room_id(room_id: str) -> tuple[str, str]:
        if "__" not in room_id:
            raise ValueError("Room ids must be '<site_slug>__<room_id>'")
        return tuple(room_id.split("__", 1))  # type: ignore[return-value]
