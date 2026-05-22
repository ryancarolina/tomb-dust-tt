"""Bridge: direct Python API into the tomb_gm engine (no subprocess)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from tomb_gm.config import resolve_workspace, load_config
from tomb_gm.db.connection import run_migrations
from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.cmd_core import handle_init, handle_status, handle_check, handle_suggest, log_event


def _connect_threadsafe(db_path: Path) -> sqlite3.Connection:
    """Connect with check_same_thread=False for use from background threads."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


class GameBridge:
    """Provides direct access to tomb_gm mechanics without subprocess calls."""

    def __init__(self, workspace: str | Path | None = None):
        ws = resolve_workspace(str(workspace) if workspace else None)
        cfg = load_config(ws)
        conn = _connect_threadsafe(cfg.db_path)
        run_migrations(conn)
        self.ctx = CommandContext(config=cfg, conn=conn)
        self._ns = _FakeNamespace(str(ws))

    def status(self) -> dict:
        return handle_status(self._ns, None)

    def check(self) -> dict:
        return handle_check(self._ns, None)

    def suggest(self) -> dict:
        return handle_suggest(self._ns, None)

    def init(self) -> dict:
        return handle_init(self._ns, None)

    def roll_attributes(self, race: str = "human") -> dict:
        """Roll attributes per canon: 1d10 base + 1d4 genetic + 2d20 life event + racial."""
        import random

        RACES = {
            "human": {},
            "high-elf": {"INT": 2, "AGI": 1},
            "dark-elf": {"AGI": 2, "INT": 1, "SPI": -1},
            "wood-elf": {"AGI": 2, "SPI": 1},
            "dwarf": {"STA": 2, "STR": 1, "AGI": -1},
            "halfling": {"AGI": 2, "SPI": 1},
            "centaur": {"STR": 2, "AGI": 1, "INT": -1},
            "aquarid": {"AGI": 2, "SPI": 1, "STA": -1},
            "demonkin": {"SPI": 2, "STR": 1, "AGI": -1},
            "orc": {"STR": 2, "STA": 1, "INT": -1},
            "gnome": {"INT": 2, "AGI": 1, "STR": -1},
            "dragonkin": {"STR": 2, "SPI": 1, "AGI": -1},
            "faerie": {"AGI": 2, "INT": 1, "STR": -1},
            "minotaur": {"STR": 2, "STA": 1, "INT": -1},
            "undead": {"SPI": 2, "STA": 1, "AGI": -1},
            "troll": {"STR": 2, "AGI": 1, "INT": -1},
        }
        GENETIC_TABLE = {1: -1, 2: 0, 3: 1, 4: 2}
        LIFE_EVENTS = {
            2: {"STA": -2, "STR": -1}, 3: {"STR": 2, "AGI": -1},
            4: {"AGI": 2, "STA": 1}, 5: {"INT": 2, "STR": -1},
            6: {"SPI": 2, "INT": 1}, 7: {"SPI": -2, "STA": -1},
            8: {"AGI": 1, "STR": 1}, 9: {"INT": 2, "SPI": 1},
            10: {"STR": 1, "AGI": 1}, 11: {"SPI": -1, "AGI": -1},
            12: {"STR": 1, "STA": 1, "AGI": 1}, 13: {"INT": 2, "SPI": 2},
            14: {"SPI": -1, "STA": -1}, 15: {"STR": 1, "SPI": -1},
            16: {"STR": 1, "STA": 1}, 17: {"STA": 2, "SPI": 1},
            18: {"AGI": 2, "STA": -1}, 19: {"STR": 1, "AGI": 1, "STA": 1},
            20: {"AGI": -2, "STR": -1}, 21: {"INT": 2, "SPI": 1},
            22: {"STA": 1, "SPI": -1}, 23: {"AGI": 1, "INT": 1},
            24: {"STA": 1, "AGI": -1}, 25: {"INT": 2, "SPI": 1},
            26: {"STA": 1, "STR": 1}, 27: {"SPI": -1, "INT": -1},
            28: {"STR": 2, "AGI": 1}, 29: {"SPI": 2, "INT": 1},
            30: {"AGI": 1, "STA": 1}, 31: {"SPI": -2, "STA": -1},
            32: {"AGI": 1, "INT": 1}, 33: {"SPI": 1, "INT": 1},
            34: {"SPI": 2, "INT": 1}, 35: {"STA": 1, "SPI": -1},
            36: {"STA": 1, "AGI": 1}, 37: {"STR": 1, "SPI": -1},
            38: {"AGI": 1, "STA": 1}, 39: {"SPI": 1, "INT": 1},
            40: {"STA": 1, "STR": 1},
        }
        LIFE_EVENT_NAMES = {
            2: "Severe Illness", 3: "Grueling Labor", 4: "Athletic Training",
            5: "Intense Study", 6: "Mystical Encounter", 7: "Childhood Trauma",
            8: "Adventurous Upbringing", 9: "Scholarly Pursuits", 10: "Peaceful Life",
            11: "Isolated Childhood", 12: "Military Training", 13: "Magical Awakening",
            14: "Parental Loss", 15: "Orphaned Young", 16: "Hard Labor",
            17: "Blessed with Health", 18: "Nimble Childhood", 19: "Farm Life",
            20: "Severe Injury", 21: "Early Mentorship", 22: "Harsh Environment",
            23: "Frequent Travel", 24: "Sickness Recovery", 25: "Rich Education",
            26: "Desert Life", 27: "Lonely Upbringing", 28: "Combat Training",
            29: "Regular Meditation", 30: "Nomadic Life", 31: "Repeated Trauma",
            32: "Street Smarts", 33: "High Society", 34: "Religious Upbringing",
            35: "War Survivor", 36: "Jungle Life", 37: "Early Loss of Family",
            38: "Forest Dweller", 39: "Wealthy Childhood", 40: "Harsh Winters",
        }

        race_key = race.lower().replace(" ", "-")
        racial_mods = RACES.get(race_key, {})
        if race_key == "human":
            human_picks = random.sample(["STR", "AGI", "STA", "INT", "SPI"], 2)
            racial_mods = {a: 1 for a in human_picks}

        attrs = {}
        base_rolls = {}
        genetic_rolls = {}
        for attr in ("STR", "AGI", "STA", "INT", "SPI"):
            base = random.randint(1, 10)
            genetic_roll = random.randint(1, 4)
            genetic_mod = GENETIC_TABLE[genetic_roll]
            base_rolls[attr] = base
            genetic_rolls[attr] = {"roll": genetic_roll, "mod": genetic_mod}
            attrs[attr] = base + genetic_mod

        life_roll = random.randint(1, 20) + random.randint(1, 20)
        life_mods = LIFE_EVENTS.get(life_roll, {})
        life_name = LIFE_EVENT_NAMES.get(life_roll, "Unremarkable Youth")
        for attr, mod in life_mods.items():
            attrs[attr] = attrs.get(attr, 0) + mod

        for attr, mod in racial_mods.items():
            attrs[attr] = attrs.get(attr, 0) + mod

        # Clamp all attributes to minimum 1 (no negative scores)
        for attr in list(attrs.keys()):
            attrs[attr] = max(1, attrs[attr])

        attrs["LUC"] = max(1, random.randint(1, 10) + GENETIC_TABLE[random.randint(1, 4)])

        eligible_classes = ["peasant"]
        if attrs.get("STR", 0) >= 8:
            eligible_classes.append("laborer")
        if attrs.get("AGI", 0) >= 8:
            eligible_classes.append("urchin")
        if attrs.get("INT", 0) >= 8:
            eligible_classes.append("apprentice")
        if attrs.get("STR", 0) >= 8 or attrs.get("AGI", 0) >= 8:
            if "militia" not in eligible_classes:
                eligible_classes.append("militia")
        if attrs.get("SPI", 0) >= 8:
            eligible_classes.append("novice")

        return {
            "ok": True,
            "race": race_key,
            "racial_adjustments": racial_mods,
            "base_rolls": base_rolls,
            "genetic_factors": genetic_rolls,
            "life_event": {"roll": life_roll, "name": life_name, "mods": life_mods},
            "final_attributes": attrs,
            "eligible_classes": eligible_classes,
        }

    def roll_d20(self, mod: int = 0, dc: int = 10, reason: str = "") -> dict:
        from tomb_gm.services.simulation.rolls import perform_d20_roll
        from tomb_gm.cli.cmd_core import log_event
        session_id = self._active_session_id()
        result = perform_d20_roll(
            self.ctx.conn,
            log_event,
            session_id=session_id,
            mod=mod,
            dc=dc,
            reason=reason,
        )
        return result

    def process_beat(self, lines: list[dict], **flags) -> dict:
        from tomb_gm.services.beat import process_beat
        actions = {"lines": lines, **flags}
        return process_beat(self.ctx, actions)

    def world_travel(self, to_address: str) -> dict:
        from tomb_gm.services.world import WorldService, resolve_surface_address
        from tomb_gm.services.content import ContentService

        content = ContentService(self.ctx.config.content_root)
        world = WorldService(content)
        session_id = self._active_session_id()
        row = self.ctx.conn.execute(
            "SELECT address, stamp_json FROM party_state WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return {"ok": False, "error": "no active party state"}
        from_addr = row["address"]
        exits = world.legal_exits(from_addr) or []
        to_stripped = to_address.strip()
        resolved_from: str | None = None
        if to_stripped.lower() not in {e.lower() for e in exits}:
            resolved = resolve_surface_address(
                content, to_stripped, from_address=from_addr
            )
            if not resolved.get("ok"):
                return {**resolved, "from": from_addr, "to": to_address}
            to_address = resolved["address"]
            resolved_from = resolved.get("resolved_from")
        ok, code = world.can_travel(from_addr, to_address)
        if not ok:
            return {"ok": False, "error": code, "from": from_addr, "to": to_address}
        self.ctx.conn.execute(
            "UPDATE party_state SET address = ?, mode = 'surface', site_id = NULL, site_node_id = NULL WHERE session_id = ?",
            (to_address, session_id),
        )
        self.ctx.conn.commit()
        log_event(self.ctx.conn, session_id, "world_travel", {"from": from_addr, "to": to_address})
        cell = content.cell_payload(to_address)
        out: dict = {
            "ok": True,
            "action": "travel",
            "from": from_addr,
            "to": to_address,
            "cell": cell,
        }
        if resolved_from:
            out["resolved_from"] = resolved_from
        return out

    def site_enter(self, site_id: str) -> dict:
        from tomb_gm.services.site import enter_site, SiteError
        try:
            return {**enter_site(self.ctx, site_id), "action": "site_enter"}
        except SiteError as exc:
            return {"ok": False, "error": str(exc)}

    def site_move(self, node_id: str) -> dict:
        from tomb_gm.services.site import move_site, SiteError
        try:
            return {**move_site(self.ctx, node_id), "action": "site_move"}
        except SiteError as exc:
            return {"ok": False, "error": str(exc)}

    def start_combat(self, monster_specs: list[str], include_party: bool = True) -> dict:
        from tomb_gm.services.simulation.combat import start_combat, validate_monster_specs

        session_id = self._active_session_id()
        campaign_slug = self._campaign_slug()
        err = validate_monster_specs(self.ctx.config.content_root, monster_specs)
        if err:
            return {"ok": False, "error": err}
        try:
            result = start_combat(
                self.ctx.conn,
                session_id=session_id,
                content_root=self.ctx.config.content_root,
                monster_specs=monster_specs,
                include_party=include_party,
                campaign_slug=campaign_slug,
            )
            return {**result, "action": "combat_start"}
        except (ValueError, FileNotFoundError) as exc:
            return {"ok": False, "error": str(exc)}

    def combat_attack(self, attacker_id: str, target_id: str, weapon_id: str | None = None) -> dict:
        from tomb_gm.services.simulation.combat import combat_attack
        session_id = self._active_session_id()
        try:
            return combat_attack(
                self.ctx.conn,
                session_id,
                attacker_id,
                target_id,
                content_root=self.ctx.config.content_root,
                campaign_slug=self._campaign_slug(),
                weapon_id=weapon_id,
            )
        except (ValueError, KeyError) as exc:
            return {"ok": False, "error": str(exc)}

    def combat_end(self) -> dict:
        from tomb_gm.services.simulation.combat import end_combat
        session_id = self._active_session_id()
        return end_combat(self.ctx.conn, session_id, campaign_slug=self._campaign_slug())

    def combat_action(
        self,
        action: str,
        actor_id: str,
        target_id: str | None = None,
        weapon_id: str | None = None,
        spell_id: str | None = None,
    ) -> dict:
        from tomb_gm.cli.cmd_core import log_event
        from tomb_gm.services.simulation.combat import resolve_pc_action_and_advance

        session_id = self._active_session_id()
        try:
            return resolve_pc_action_and_advance(
                self.ctx.conn,
                session_id,
                action=action,
                actor_id=actor_id,
                content_root=self.ctx.config.content_root,
                campaign_slug=self._campaign_slug(),
                target_id=target_id,
                weapon_id=weapon_id,
                spell_id=spell_id,
                log_event=log_event,
            )
        except (ValueError, KeyError) as exc:
            return {"ok": False, "error": str(exc)}

    def run_combat_monster_turns(self) -> dict:
        from tomb_gm.services.simulation.combat import run_monster_turns_until_pc_or_end

        session_id = self._active_session_id()
        results = run_monster_turns_until_pc_or_end(
            self.ctx.conn,
            session_id,
            content_root=self.ctx.config.content_root,
            campaign_slug=self._campaign_slug(),
        )
        return {"ok": True, "mechanical": results}

    def start_combat_from_trigger(self, monster_specs: list[str]) -> dict:
        """Start combat with party included (FSM / beat trigger entry)."""
        existing = self.status().get("combat")
        if existing:
            return {"ok": False, "error": "combat already active"}
        return self.start_combat(monster_specs=monster_specs, include_party=True)

    def list_known_spells(self, character_id: str) -> dict:
        from tomb_gm.services.content import ContentService
        from tomb_gm.services.simulation.spell_service import ensure_spell_fields
        from tomb_gm.cli.cmd_core import _spell_display_lines

        campaign_slug = self._campaign_slug()
        row = self.ctx.conn.execute(
            "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
            (character_id, campaign_slug),
        ).fetchone()
        if not row:
            return {"ok": False, "error": f"Character not found: {character_id}"}
        sheet = json.loads(row["sheet_json"])
        if ensure_spell_fields(sheet):
            self.ctx.conn.execute(
                "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
                (json.dumps(sheet), character_id, campaign_slug),
            )
            self.ctx.conn.commit()
        content = ContentService(self.ctx.config.content_root)
        known = sheet.get("knownSpells") or []
        spells = []
        for sid in known:
            spell = content.load_spell(sid)
            if spell:
                spells.append({
                    "id": sid,
                    "displayName": spell.get("displayName", sid),
                    "tier": spell.get("tier"),
                    "mpCost": spell.get("mpCost"),
                    "school": spell.get("school"),
                    "effectType": spell.get("effectType"),
                })
        return {
            "ok": True,
            "character_id": character_id,
            "display_name": sheet.get("displayName", character_id),
            "spell_schools": sheet.get("spellSchools", []),
            "spells": spells,
            "spell_lines": _spell_display_lines(content, known),
        }

    def world_where(self) -> dict:
        from tomb_gm.services.world import WorldService
        from tomb_gm.services.content import ContentService

        content = ContentService(self.ctx.config.content_root)
        world = WorldService(content)
        session_id = self._active_session_id()
        row = self.ctx.conn.execute(
            "SELECT address, mode, stamp_json FROM party_state WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return {"ok": False, "error": "no party state"}
        payload = world.where_payload(row["address"], mode=row["mode"], stamp_json=row["stamp_json"])
        return {"ok": True, **(payload or {})}

    def world_exits(self) -> dict:
        from tomb_gm.services.world import WorldService
        from tomb_gm.services.content import ContentService

        content = ContentService(self.ctx.config.content_root)
        world = WorldService(content)
        session_id = self._active_session_id()
        row = self.ctx.conn.execute(
            "SELECT address FROM party_state WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return {"ok": False, "error": "no party state"}
        exits = world.legal_exits(row["address"])
        return {"ok": True, "address": row["address"], "exits": exits}

    def campaign_new(self, slug: str, display_name: str = "") -> dict:
        from tomb_gm.domain.campaign import create_campaign
        return create_campaign(self.ctx.conn, self.ctx.config, slug, display_name or slug)

    def session_start(self, campaign_slug: str) -> dict:
        from tomb_gm.domain.session import start_session
        return start_session(self.ctx.conn, self.ctx.config, campaign_slug)

    def session_resume(self) -> dict:
        from tomb_gm.domain.session import resume_session
        return resume_session(self.ctx.conn, self.ctx.config)

    def has_save(self) -> bool:
        from tomb_gm.domain.session import has_save_session
        return has_save_session(self.ctx.conn)

    def end_session(self) -> dict:
        from tomb_gm.domain.session import end_session
        try:
            result = end_session(self.ctx.conn, self.ctx.config)
            return result
        except Exception:
            return self.force_close_all_sessions()

    def force_close_all_sessions(self) -> dict:
        """Force-close all open sessions directly in the DB and remove active.json."""
        try:
            self.ctx.conn.execute(
                "UPDATE sessions SET ended_at = datetime('now') WHERE ended_at IS NULL"
            )
            self.ctx.conn.commit()
        except Exception:
            pass
        active_path = self.ctx.config.local_dir / "active.json"
        try:
            active_path.unlink(missing_ok=True)
        except Exception:
            pass
        return {"ok": True, "forced": True}

    def wipe_all_data(self):
        """Delete campaign/session data. World corpses persist for future runs."""
        tables = [
            "events", "combat_state", "party_state", "scene_summaries",
            "cell_features", "cell_visits", "site_rooms", "room_features",
            "characters", "sessions", "campaigns", "memories",
        ]
        conn = self.ctx.conn
        conn.execute("PRAGMA foreign_keys = OFF")
        for table in tables:
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
        conn.execute("PRAGMA foreign_keys = ON")
        active_path = self.ctx.config.local_dir / "active.json"
        try:
            active_path.unlink(missing_ok=True)
        except Exception:
            pass

    def character_create(self, **kwargs) -> dict:
        from tomb_gm.domain.character import create_character

        _CLASS_MAP = {
            "thief": "urchin", "rogue": "urchin", "sneak": "urchin",
            "soldier": "militia", "fighter": "militia", "warrior": "militia", "knight": "militia",
            "mage": "apprentice", "wizard": "apprentice", "scholar": "apprentice",
            "priest": "novice", "cleric": "novice", "healer": "novice",
            "farmer": "peasant", "hunter": "peasant", "ranger": "peasant",
            "smith": "laborer", "worker": "laborer", "builder": "laborer",
            "delver": "militia",
        }
        _ATTR_MAP = {
            "end_score": "STA", "sta_score": "STA", "endurance": "STA",
            "wil_score": "SPI", "spi_score": "SPI", "willpower": "SPI",
            "luc_score": "LUC", "luck": "LUC",
            "str_score": "STR", "strength": "STR",
            "agi_score": "AGI", "agility": "AGI",
            "int_score": "INT", "intelligence": "INT",
        }

        campaign_slug = self._campaign_slug()
        name = kwargs.pop("name", "Unnamed")
        background = kwargs.pop("background", "militia").lower()
        base_class = _CLASS_MAP.get(background, background)
        if base_class not in ("peasant", "laborer", "urchin", "apprentice", "militia", "novice"):
            base_class = "militia"

        attributes = {}
        for key, attr_name in _ATTR_MAP.items():
            if key in kwargs:
                attributes[attr_name] = int(kwargs.pop(key))

        skill_ids = kwargs.pop("skill_ids", None)
        race_id = kwargs.pop("race_id", None)
        gold_gp = int(kwargs.pop("gold_gp", 0) or 0)
        inventory = kwargs.pop("inventory", None)
        creation_audit = kwargs.pop("creation_audit", None)
        known_spell_ids = kwargs.pop("known_spell_ids", None)
        spell_school_ids = kwargs.pop("spell_school_ids", None)

        if inventory is None or not (inventory.get("pack") if isinstance(inventory, dict) else None):
            from tomb_gm.domain.creation import starting_kit_inventory

            inventory = starting_kit_inventory(self.ctx.config.content_root, base_class)

        if creation_audit and creation_audit.get("startingGold") and not creation_audit.get("remainingGp"):
            from tomb_gm.domain.creation import starting_kit

            kit = starting_kit(self.ctx.config.content_root, base_class)
            gold_gp = max(0, gold_gp - int(kit.get("costGp", 0)))

        try:
            result = create_character(
                self.ctx.conn,
                campaign_slug=campaign_slug,
                display_name=name,
                base_class=base_class,
                attributes=attributes or None,
                skill_ids=skill_ids,
                race_id=race_id,
                gold_gp=gold_gp,
                inventory=inventory,
                creation_audit=creation_audit,
                known_spell_ids=known_spell_ids,
                spell_school_ids=spell_school_ids,
            )
            char_id = result.get("id")
            if char_id:
                try:
                    self.roster_set(campaign_slug, 1, char_id)
                except Exception:
                    pass
            return {"ok": True, "base_class": base_class, **result}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def roster_set(self, campaign_slug: str, slot: int, character_id: str) -> dict:
        from tomb_gm.domain.character import set_roster_slot
        return set_roster_slot(self.ctx.conn, campaign_slug=campaign_slug, slot=slot, character_id=character_id)

    def memory_recall(self, query: str, top_k: int = 5) -> dict:
        from tomb_gm.services.memory import recall_facts
        campaign_slug = self._campaign_slug()
        facts = recall_facts(self.ctx.conn, campaign_slug, query, top=top_k)
        return {"ok": True, "facts": facts}

    def cast_spell(self, character_id: str, spell_id: str, target_id: str | None = None) -> dict:
        from tomb_gm.domain.spell_cast import cast_spell
        from tomb_gm.cli.cmd_core import log_event
        session_id = self._active_session_id()
        campaign_slug = self._campaign_slug()
        try:
            return cast_spell(
                self.ctx.conn, log_event,
                content_root=self.ctx.config.content_root,
                campaign_slug=campaign_slug,
                character_id=character_id,
                spell_id=spell_id,
                session_id=session_id,
                target_id=target_id,
            )
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def fortune_spend(self, character_id: str) -> dict:
        from tomb_gm.domain.combat_player import spend_fortune
        campaign_slug = self._campaign_slug()
        try:
            return spend_fortune(self.ctx.conn, campaign_slug, character_id)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def short_rest(self) -> dict:
        session_id = self._active_session_id()
        from tomb_gm.cli.cmd_core import log_event
        log_event(self.ctx.conn, session_id, "short_rest", {})
        return {"ok": True, "action": "short_rest", "note": "HP/MP recovery applied"}

    def set_phase(self, phase: str) -> dict:
        from tomb_gm.services.extraction import set_phase
        try:
            return set_phase(self.ctx, phase)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def clock_tick(self, clock: str, segments: int = 1) -> dict:
        from tomb_gm.services.extraction import clock_tick
        try:
            return clock_tick(self.ctx, clock, segments=segments)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def search_site(self, dc: int = 13, skill_mod: int = 0) -> dict:
        from tomb_gm.services.site import search_site
        try:
            return search_site(self.ctx, dc=dc, skill_mod=skill_mod)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def wilderness_encounter(self) -> dict:
        from tomb_gm.services.encounters import wilderness_travel_roll
        session_id = self._active_session_id()
        row = self.ctx.conn.execute(
            "SELECT address FROM party_state WHERE session_id = ?", (session_id,)
        ).fetchone()
        if not row:
            return {"ok": False, "error": "no party state"}
        from tomb_gm.services.content import ContentService
        content = ContentService(self.ctx.config.content_root)
        cell = content.cell_payload(row["address"])
        biomes = cell.get("biomes", ["HL"]) if cell else ["HL"]
        danger = cell.get("dangerRating", "skirmisher") if cell else "skirmisher"
        result = wilderness_travel_roll(
            self.ctx.config.content_root, biomes=biomes, danger=danger or "skirmisher"
        )
        return {"ok": True, **result}

    # ------------------------------------------------------------------
    # Exploration tools
    # ------------------------------------------------------------------

    def _exploration_service(self):
        from tomb_gm.services.exploration import ExplorationService
        from tomb_gm.services.content import ContentService
        content = ContentService(self.ctx.config.content_root)
        return ExplorationService(self.ctx.conn, content)

    def advance_scene(self, direction: str | None = None) -> dict:
        svc = self._exploration_service()
        session_id = self._active_session_id()
        campaign_slug = self._campaign_slug()
        return svc.advance_scene(session_id, campaign_slug, direction)

    def compass_exits(self) -> dict:
        svc = self._exploration_service()
        session_id = self._active_session_id()
        campaign_slug = self._campaign_slug()
        row = self.ctx.conn.execute(
            "SELECT address FROM party_state WHERE session_id = ?", (session_id,)
        ).fetchone()
        if not row:
            return {"ok": False, "error": "no party state"}
        exits = svc.compass_exits(row["address"], campaign_slug)
        return {"ok": True, "address": row["address"], "exits": exits}

    def enter_dungeon(
        self,
        site_address: str | None = None,
        site_id: str | None = None,
        **kwargs: Any,
    ) -> dict:
        from tomb_gm.services.content import ContentService
        from tomb_gm.services.extraction import advance_phase_for_dungeon_entry
        from tomb_gm.services.site_resolve import resolve_site_address

        query = (site_address or site_id or kwargs.get("site_address") or kwargs.get("site_id") or "").strip()
        if not query:
            return {"ok": False, "error": "site_address required (AV-GRID id, site slug, or display name)"}

        session_id = self._active_session_id()
        row = self.ctx.conn.execute(
            "SELECT address FROM party_state WHERE session_id = ?", (session_id,)
        ).fetchone()
        surface_address = row["address"] if row else None

        content = ContentService(self.ctx.config.content_root)
        resolved = resolve_site_address(content, query, current_surface_address=surface_address)
        if not resolved.get("ok"):
            return resolved

        address = resolved["site_address"]
        svc = self._exploration_service()
        result = svc.enter_site(session_id, address)
        if not result.get("ok"):
            return result

        phase_result = advance_phase_for_dungeon_entry(self.ctx)
        if not phase_result.get("ok"):
            return {**result, "phase_error": phase_result}

        result["phase"] = phase_result.get("phase")
        if resolved.get("resolved_from") and resolved["resolved_from"] != address:
            result["resolved_from"] = resolved["resolved_from"]
        return result

    def move_room(self, direction: str) -> dict:
        svc = self._exploration_service()
        session_id = self._active_session_id()
        return svc.move_room(session_id, direction)

    def exit_dungeon(self) -> dict:
        svc = self._exploration_service()
        session_id = self._active_session_id()
        return svc.exit_site(session_id)

    def interact_feature(self, feature_id: str, action: str) -> dict:
        from tomb_gm.services.death import loot_corpse, resolve_corpse_id

        svc = self._exploration_service()
        session_id = self._active_session_id()
        ps = self.ctx.conn.execute(
            "SELECT site_id, dungeon_room_id, mode FROM party_state WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        site_address = ps["site_id"] if ps and ps["mode"] == "dungeon" else None
        room_id = ps["dungeon_room_id"] if ps else None

        corpse_id = resolve_corpse_id(
            self.ctx.conn,
            feature_id,
            site_address=site_address,
            room_id=room_id,
        )
        if action == "loot" and corpse_id:
            chars = self.ctx.conn.execute(
                "SELECT id FROM characters WHERE campaign_slug = ? AND slot IS NOT NULL AND alive = 1 LIMIT 1",
                (self._campaign_slug(),),
            ).fetchone()
            if not chars:
                return {"ok": False, "error": "no living character to loot with"}
            return loot_corpse(
                self.ctx.conn,
                corpse_id=corpse_id,
                campaign_slug=self._campaign_slug(),
                character_id=chars["id"],
                content_root=self.ctx.config.content_root,
            )

        if action == "loot":
            row = self.ctx.conn.execute(
                "SELECT id FROM world_corpses WHERE id = ? OR display_name LIKE ?",
                (feature_id, f"%{feature_id}%"),
            ).fetchone()
            if row:
                return {
                    "ok": False,
                    "error": f"Use corpse id {row['id']} for delver corpse loot",
                    "corpse_id": row["id"],
                }
            svc.update_feature_state(feature_id, "looted")
            return {"ok": True, "feature_id": feature_id, "new_state": "looted", "action": action}
        elif action == "destroy":
            svc.update_feature_state(feature_id, "destroyed")
            return {"ok": True, "feature_id": feature_id, "new_state": "destroyed", "action": action}
        elif action == "activate":
            svc.update_feature_state(feature_id, "activated")
            return {"ok": True, "feature_id": feature_id, "new_state": "activated", "action": action}
        else:
            if corpse_id and action in ("examine", "search"):
                row = self.ctx.conn.execute(
                    "SELECT loot_json, display_name, state FROM world_corpses WHERE id = ?",
                    (corpse_id,),
                ).fetchone()
                if row:
                    import json

                    loot = json.loads(row["loot_json"] or "{}")
                    return {
                        "ok": True,
                        "feature_id": corpse_id,
                        "action": action,
                        "corpse": True,
                        "state": row["state"],
                        "loot_summary": loot,
                    }
            return {
                "ok": True,
                "feature_id": feature_id,
                "state": "pristine",
                "action": action,
                "message": "Feature examined — narrate what the player finds based on its description",
            }

    def list_inventory(self, character_id: str | None = None) -> dict:
        from tomb_gm.domain.inventory import ensure_normalized, format_inventory_summary
        from tomb_gm.services.content import ContentService

        campaign_slug = self._campaign_slug()
        if not character_id:
            row = self.ctx.conn.execute(
                "SELECT id, sheet_json FROM characters "
                "WHERE campaign_slug = ? AND slot IS NOT NULL AND alive = 1 "
                "ORDER BY slot ASC LIMIT 1",
                (campaign_slug,),
            ).fetchone()
        else:
            row = self.ctx.conn.execute(
                "SELECT id, sheet_json FROM characters WHERE id = ? AND campaign_slug = ? AND alive = 1",
                (character_id, campaign_slug),
            ).fetchone()
        if not row:
            return {"ok": False, "error": "no living character found"}
        sheet = json.loads(row["sheet_json"])
        content = ContentService(self.ctx.config.content_root)
        lookup = content.items_lookup()
        before = json.dumps(sheet, sort_keys=True)
        ensure_normalized(sheet, item_lookup=lookup)
        if json.dumps(sheet, sort_keys=True) != before:
            self.ctx.conn.execute(
                "UPDATE characters SET sheet_json = ? WHERE id = ?",
                (json.dumps(sheet), row["id"]),
            )
            self.ctx.conn.commit()
        display = {iid: content.item_display_name(iid) for iid in lookup}
        return {
            "ok": True,
            "character_id": row["id"],
            "goldGp": int(sheet.get("goldGp", 0)),
            "pack": sheet.get("inventory", {}).get("pack", []),
            "summary": format_inventory_summary(sheet, item_display=display),
        }

    def equip_item(self, instance_id: str, slot: str, character_id: str | None = None) -> dict:
        from tomb_gm.domain.inventory import ensure_normalized, equip, get_pack
        from tomb_gm.services.content import ContentService

        campaign_slug = self._campaign_slug()
        char_id = character_id
        if not char_id:
            row = self.ctx.conn.execute(
                "SELECT id FROM characters WHERE campaign_slug = ? AND slot IS NOT NULL AND alive = 1 "
                "ORDER BY slot ASC LIMIT 1",
                (campaign_slug,),
            ).fetchone()
            if not row:
                return {"ok": False, "error": "no living character found"}
            char_id = row["id"]
        row = self.ctx.conn.execute(
            "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
            (char_id, campaign_slug),
        ).fetchone()
        if not row:
            return {"ok": False, "error": f"Character not found: {char_id}"}
        content = ContentService(self.ctx.config.content_root)
        lookup = content.items_lookup()
        sheet = json.loads(row["sheet_json"])
        ensure_normalized(sheet, item_lookup=lookup)
        result = equip(get_pack(sheet), instance_id, slot, item_lookup=lookup)
        if not result.get("ok"):
            return result
        self.ctx.conn.execute(
            "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
            (json.dumps(sheet), char_id, campaign_slug),
        )
        self.ctx.conn.commit()
        return {"ok": True, "character_id": char_id, **result}

    def unequip_item(self, instance_id: str, character_id: str | None = None) -> dict:
        from tomb_gm.domain.inventory import ensure_normalized, get_pack, unequip

        campaign_slug = self._campaign_slug()
        char_id = character_id
        if not char_id:
            row = self.ctx.conn.execute(
                "SELECT id FROM characters WHERE campaign_slug = ? AND slot IS NOT NULL AND alive = 1 "
                "ORDER BY slot ASC LIMIT 1",
                (campaign_slug,),
            ).fetchone()
            if not row:
                return {"ok": False, "error": "no living character found"}
            char_id = row["id"]
        row = self.ctx.conn.execute(
            "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
            (char_id, campaign_slug),
        ).fetchone()
        if not row:
            return {"ok": False, "error": f"Character not found: {char_id}"}
        sheet = json.loads(row["sheet_json"])
        ensure_normalized(sheet)
        result = unequip(get_pack(sheet), instance_id)
        if not result.get("ok"):
            return result
        self.ctx.conn.execute(
            "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
            (json.dumps(sheet), char_id, campaign_slug),
        )
        self.ctx.conn.commit()
        return {"ok": True, "character_id": char_id, **result}

    def use_item(
        self,
        instance_id: str,
        quantity: int = 1,
        character_id: str | None = None,
    ) -> dict:
        from tomb_gm.domain.inventory import ensure_normalized, get_pack, use_item
        from tomb_gm.services.content import ContentService

        campaign_slug = self._campaign_slug()
        char_id = character_id
        if not char_id:
            row = self.ctx.conn.execute(
                "SELECT id FROM characters WHERE campaign_slug = ? AND slot IS NOT NULL AND alive = 1 "
                "ORDER BY slot ASC LIMIT 1",
                (campaign_slug,),
            ).fetchone()
            if not row:
                return {"ok": False, "error": "no living character found"}
            char_id = row["id"]
        row = self.ctx.conn.execute(
            "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
            (char_id, campaign_slug),
        ).fetchone()
        if not row:
            return {"ok": False, "error": f"Character not found: {char_id}"}
        content = ContentService(self.ctx.config.content_root)
        lookup = content.items_lookup()
        sheet = json.loads(row["sheet_json"])
        ensure_normalized(sheet, item_lookup=lookup)
        result = use_item(
            get_pack(sheet),
            instance_id,
            quantity=quantity,
            item_lookup=lookup,
        )
        if not result.get("ok"):
            return result
        self.ctx.conn.execute(
            "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
            (json.dumps(sheet), char_id, campaign_slug),
        )
        self.ctx.conn.commit()
        return {"ok": True, "character_id": char_id, **result}

    def grant_loot(self, tier: str | None = None, character_id: str | None = None) -> dict:
        from tomb_gm.services.content import ContentService
        from tomb_gm.services.loot_resolver import LootResolver, grant_loot as persist_loot

        campaign_slug = self._campaign_slug()
        content = ContentService(self.ctx.config.content_root)
        resolver = LootResolver(self.ctx.config.content_root)
        rolled = resolver.roll(tier=tier or "skirmisher")
        if not rolled.get("ok"):
            return rolled
        granted = persist_loot(
            self.ctx.conn,
            content,
            campaign_slug=campaign_slug,
            loot_result=rolled,
            character_id=character_id,
        )
        return {"ok": True, "loot": rolled, "granted": granted}

    def buy_item(
        self,
        item_id: str,
        quantity: int = 1,
        vendor_id: str = "registry-quartermaster",
        character_id: str | None = None,
    ) -> dict:
        from tomb_gm.services import economy as econ
        from tomb_gm.services.content import ContentService
        from tomb_gm.services.hub import active_delver_id

        campaign_slug = self._campaign_slug()
        char_id = character_id or active_delver_id(self.ctx.conn, campaign_slug)
        if not char_id:
            return {"ok": False, "error": "no living character"}
        try:
            return econ.buy_from_vendor(
                self.ctx.conn,
                ContentService(self.ctx.config.content_root),
                campaign_slug=campaign_slug,
                session_id=self._active_session_id(),
                character_id=char_id,
                vendor_id=vendor_id,
                item_id=item_id,
                quantity=quantity,
            )
        except econ.EconomyError as exc:
            return {"ok": False, "error": str(exc)}

    def sell_item(
        self,
        instance_id: str,
        quantity: int | None = None,
        vendor_id: str | None = None,
        character_id: str | None = None,
    ) -> dict:
        from tomb_gm.services import economy as econ
        from tomb_gm.services.content import ContentService
        from tomb_gm.services.hub import active_delver_id

        campaign_slug = self._campaign_slug()
        char_id = character_id or active_delver_id(self.ctx.conn, campaign_slug)
        if not char_id:
            return {"ok": False, "error": "no living character"}
        try:
            return econ.sell_item(
                self.ctx.conn,
                ContentService(self.ctx.config.content_root),
                campaign_slug=campaign_slug,
                session_id=self._active_session_id(),
                character_id=char_id,
                instance_id=instance_id,
                quantity=quantity,
                vendor_id=vendor_id,
            )
        except econ.EconomyError as exc:
            return {"ok": False, "error": str(exc)}

    def list_stash(self) -> dict:
        from tomb_gm.services import economy as econ

        try:
            return econ.list_stash(self.ctx.conn, self._campaign_slug())
        except econ.EconomyError as exc:
            return {"ok": False, "error": str(exc)}

    def list_vendor(self, vendor_id: str = "registry-quartermaster") -> dict:
        from tomb_gm.services.content import ContentService

        content = ContentService(self.ctx.config.content_root)
        vendor = content.load_vendor(vendor_id)
        if not vendor:
            return {"ok": False, "error": f"Unknown vendor: {vendor_id}"}
        stock = []
        for entry in vendor.get("stock", []):
            item_id = entry.get("itemId")
            catalog = content.load_item(str(item_id)) if item_id else None
            stock.append(
                {
                    **entry,
                    "displayName": (catalog or {}).get("displayName", item_id),
                    "costGp": (catalog or {}).get("costGp"),
                }
            )
        return {"ok": True, "vendor": vendor, "stock": stock}

    def process_delver_death(self, character_id: str, cause: str = "slain in the delve") -> dict:
        from tomb_gm.services.death import process_delver_death

        return process_delver_death(
            self.ctx.conn,
            campaign_slug=self._campaign_slug(),
            character_id=character_id,
            session_id=self._active_session_id(),
            cause=cause,
        )

    def extract_death_from_mechanical(self, mechanical: list[dict]) -> dict | None:
        """Scan combat mechanical results for PC death."""
        for item in mechanical or []:
            for dr in item.get("death_results") or []:
                if dr.get("ok"):
                    return {
                        "character_id": dr.get("dead_character_id"),
                        "corpse": (dr.get("corpse") or {}),
                        "already_processed": True,
                    }
            char = (item.get("damage_applied") or {}).get("character") or item.get("character")
            if isinstance(char, dict) and char.get("died"):
                return char
            if item.get("target_dead"):
                dmg = item.get("damage_applied") or {}
                char = dmg.get("character") or {}
                if char.get("character_id"):
                    return char
        return None

    def ensure_cell_initialized(self) -> None:
        """Call at the start of each turn to ensure current cell has features generated."""
        try:
            svc = self._exploration_service()
            session_id = self._active_session_id()
            campaign_slug = self._campaign_slug()
            row = self.ctx.conn.execute(
                "SELECT address FROM party_state WHERE session_id = ?", (session_id,)
            ).fetchone()
            if row:
                svc.ensure_cell_initialized(row["address"], campaign_slug, session_id)
        except Exception:
            pass

    def remember_fact(self, fact: str, entities: list[str] | None = None, importance: int = 3) -> dict:
        from tomb_gm.services.memory import remember_fact
        campaign_slug = self._campaign_slug()
        session_id = self._active_session_id()
        address = None
        try:
            row = self.ctx.conn.execute(
                "SELECT address FROM party_state WHERE session_id = ?", (session_id,)
            ).fetchone()
            if row:
                address = row["address"]
        except Exception:
            pass
        memory_id = remember_fact(
            self.ctx.conn, campaign_slug, fact,
            entities=entities, address=address,
            importance=importance, session_id=session_id,
        )
        return {"ok": True, "memory_id": memory_id}

    def build_recap(self) -> dict:
        from tomb_gm.services.memory import build_recap
        try:
            campaign_slug = self._campaign_slug()
            session_id = self._active_session_id()
            party = None
            roster_names: list[str] = []
            row = self.ctx.conn.execute(
                "SELECT address, phase FROM party_state WHERE session_id = ?", (session_id,)
            ).fetchone()
            if row:
                party = {"address": row["address"], "phase": row["phase"] if "phase" in row.keys() else None}
            chars = self.ctx.conn.execute(
                "SELECT sheet_json FROM characters WHERE campaign_slug = ? AND slot IS NOT NULL",
                (campaign_slug,),
            ).fetchall()
            for c in chars:
                sheet = json.loads(c["sheet_json"])
                name = sheet.get("displayName") or sheet.get("id")
                if name:
                    roster_names.append(str(name))
            return build_recap(
                self.ctx.conn,
                campaign_slug=campaign_slug,
                session_id=session_id,
                party=party,
                roster_names=roster_names,
            )
        except Exception:
            return {}

    def _active_session_id(self) -> str:
        active_path = self.ctx.config.active_path
        if not active_path.exists():
            raise ValueError("NO_ACTIVE_SESSION")
        data = json.loads(active_path.read_text(encoding="utf-8"))
        sid = data.get("session_id")
        if not sid:
            raise ValueError("NO_ACTIVE_SESSION")
        return sid

    def _campaign_slug(self) -> str:
        session_id = self._active_session_id()
        row = self.ctx.conn.execute(
            "SELECT campaign_slug FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not row:
            raise ValueError("NO_CAMPAIGN")
        return row["campaign_slug"]


class _FakeNamespace:
    """Mimics argparse.Namespace for handlers that expect args.workspace."""

    def __init__(self, workspace: str):
        self.workspace = workspace
        self.seed = None
