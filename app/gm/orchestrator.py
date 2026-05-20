"""GM Orchestrator: turn loop connecting player input → LLM → tools → narration."""

from __future__ import annotations

import json
import re
from typing import Any

from gm.bridge import GameBridge
from gm.combat_fsm import (
    CombatState,
    format_initiative_table,
    get_combat_step_prompt,
    is_pc_turn,
)
from gm.creation import (
    CreationState,
    RACES,
    CLASS_INFO,
    format_skills_table,
    format_schools_table,
    format_spells_table,
    format_races_table,
    format_classes_table,
    format_equipment_summary,
    format_creation_status,
    strip_llm_status_tags,
    ensure_equipment_gold,
    is_equipment_confirm,
    is_equipment_objection,
    parse_player_race,
    parse_player_class,
    parse_player_skills,
    parse_player_schools,
    parse_player_spells,
    normalize_skill_slug,
    validate_skill_picks,
    validate_school_picks,
    validate_spell_picks,
    needs_spell_picks,
    skip_inapplicable_spell_steps,
)
from gm.choice_memory import creation_choice_fact
from tomb_gm.services.memory.choice_facts import tool_impact_fact
from gm.openrouter import create_client, chat_completion
from gm.system_prompt import SYSTEM_PROMPT
from gm.tools import TOOLS, SET_CREATION_CHOICE_TOOL, COMBAT_ACTION_TOOL
from gm.context import build_state_context, build_messages
from gm.logger import (
    log_player_input,
    log_gm_narration,
    log_creation_advanced,
    log_creation_drift,
    log_creation_finalize,
    log_creation_step,
    parse_narration_status_line,
    log_tool_call,
    log_llm_request,
    log_llm_response,
    log_error,
)

_PREMATURE_EXPLORE_PHASES = frozenset({"delve", "ingress", "extract", "aftermath"})
_CREATION_FLAVOR_MAX_TOKENS = 120

SPELL_QUERY_RE = re.compile(
    r"\b(what spells|spells do i know|my spells|known spells|spell list|do i know any spells)\b",
    re.I,
)


class Orchestrator:
    """Manages the GM turn loop."""

    def __init__(self, config: dict):
        self.config = config
        llm_cfg = config.get("llm", {})
        self.model = llm_cfg.get("model", "anthropic/claude-sonnet-4")
        self.max_tokens = llm_cfg.get("max_tokens", 1024)
        self.temperature = llm_cfg.get("temperature", 0.8)

        self.client = create_client()
        self.bridge = GameBridge()
        self.history: list[dict[str, str]] = []
        self._last_content = ""
        self._last_tool_results: dict = {}
        self.creation = CreationState()
        self.combat = CombatState()

    def get_status(self) -> dict:
        return self.bridge.status()

    def _restore_history(self):
        """Load orchestrator history and creation state from session_state.json."""
        from pathlib import Path
        save_path = Path(__file__).resolve().parents[1] / "session_state.json"
        if not save_path.exists():
            return
        try:
            data = json.loads(save_path.read_text(encoding="utf-8"))
            if not self.history:
                saved = data.get("orchestrator_history", [])
                if saved:
                    self.history = saved[-20:]
            creation_data = data.get("creation_state")
            if creation_data and creation_data.get("active"):
                self.creation = CreationState.from_dict(creation_data)
            combat_data = data.get("combat_state")
            if combat_data and combat_data.get("active"):
                self.combat = CombatState.from_dict(combat_data)
        except Exception:
            pass

    def _sync_combat_from_status(self) -> None:
        try:
            status = self.bridge.status()
        except Exception:
            return
        if status.get("combat"):
            self.combat.active = True
            combat = status["combat"]
            self.combat.round = int(combat.get("round") or 0)
            self.combat.turn_id = combat.get("turn_id")
            if is_pc_turn(status):
                self.combat.step = "COMBAT_PC_ACTION"
            elif combat.get("turn_id"):
                self.combat.step = "COMBAT_MONSTER_ACT"
        else:
            self.combat.active = False
            self.combat.step = "COMBAT_IDLE"

    def export_combat_state(self) -> dict | None:
        if not self.combat.active:
            return None
        return self.combat.to_dict()

    def import_combat_state(self, data: dict | None) -> None:
        if data and data.get("active"):
            self.combat = CombatState.from_dict(data)

    def _combat_active_in_db(self) -> bool:
        try:
            return bool(self.bridge.status().get("combat"))
        except Exception:
            return False

    def _sync_creation_from_status(self) -> None:
        """Ensure we do not stay in creation mode when a roster already exists."""
        try:
            status = self.bridge.status()
        except Exception:
            return
        if status.get("roster"):
            self.creation.active = False
            self.creation.step = "WORLD_INTRO"
        elif status.get("awaiting") == "CHARACTER_CREATION" and not status.get("characters"):
            self.creation.active = True
            if self.creation.step == "WORLD_INTRO":
                self.creation.step = "NAME"
        else:
            self.creation.active = False

    def export_creation_state(self) -> dict | None:
        if not self.creation.active:
            return None
        return self.creation.to_dict()

    def import_creation_state(self, data: dict | None) -> None:
        if data and data.get("active"):
            self.creation = CreationState.from_dict(data)

    def _creation_drift_scope(self) -> bool:
        if self.creation.active:
            return True
        try:
            status = self.bridge.status()
        except Exception:
            return False
        return (
            status.get("awaiting") == "CHARACTER_CREATION"
            and not (status.get("roster") or [])
        )

    def _check_creation_drift(self, narration: str) -> None:
        if not self._creation_drift_scope():
            return
        narrated = parse_narration_status_line(narration)
        if not narrated.get("phase") and not narrated.get("awaiting"):
            return
        try:
            status = self.bridge.status()
        except Exception:
            status = {}
        roster = status.get("roster") or []
        party = status.get("party") or {}
        engine_phase = str(party.get("phase") or "").strip().lower()
        engine_awaiting = str(status.get("awaiting") or "").strip().upper()
        narrated_phase = str(narrated.get("phase") or "").strip().lower()
        narrated_awaiting = str(narrated.get("awaiting") or "").strip().upper()

        reasons: list[str] = []
        if narrated_awaiting and narrated_awaiting != engine_awaiting:
            reasons.append("awaiting_mismatch")
        if narrated_phase and engine_phase and narrated_phase != engine_phase:
            reasons.append("phase_mismatch")
        if self.creation.active and narrated_phase in _PREMATURE_EXPLORE_PHASES:
            reasons.append("premature_exploration_phase")

        if not reasons:
            return

        log_creation_drift({
            "step": self.creation.step,
            "roster_len": len(roster),
            "awaiting": status.get("awaiting"),
            "creation.active": self.creation.active,
            "narrated_phase": narrated.get("phase"),
            "narrated_awaiting": narrated.get("awaiting"),
            "engine_phase": party.get("phase"),
            "reasons": reasons,
        })

    def _log_creation_step_snapshot(self) -> None:
        try:
            status = self.bridge.status()
        except Exception:
            status = {}
        roster = status.get("roster") or []
        log_creation_step({
            "step": self.creation.step,
            "roster_len": len(roster),
            "awaiting": status.get("awaiting"),
            "creation.active": self.creation.active,
        })

    def _log_creation_finalize_status(self, create_result: dict) -> None:
        try:
            status = self.bridge.status()
        except Exception as exc:
            status = {"_error": str(exc)}
        log_creation_finalize({
            "character_create_ok": create_result.get("ok"),
            "character_create_error": create_result.get("error"),
            "engine_status": status,
        })

    def _emit_narration(self, narration: str) -> None:
        log_gm_narration(narration)
        self._check_creation_drift(narration)

    def setup_new_game(self, campaign_slug: str = "salt-road") -> dict:
        """Wipe session/campaign data and start completely fresh. World corpses persist."""
        self.bridge.wipe_all_data()
        self.bridge.init()
        result = self.bridge.campaign_new(campaign_slug, campaign_slug.replace("-", " ").title())
        if not result.get("ok") and "already exists" in result.get("error", ""):
            pass
        elif not result.get("ok"):
            return result
        session = self.bridge.session_start(campaign_slug)
        self.history.clear()
        self.creation = CreationState(active=True, step="NAME")
        self._delete_save_file()
        return session

    def _handle_player_death(self, mechanical: list[dict]) -> str | None:
        """If mechanical results include PC death, spawn corpse and restart."""
        death_hit = self.bridge.extract_death_from_mechanical(mechanical)
        if not death_hit:
            return None
        char_id = death_hit.get("character_id")
        if not char_id:
            return None
        try:
            campaign_slug = self.bridge._campaign_slug()
        except Exception:
            campaign_slug = "salt-road"

        if death_hit.get("already_processed"):
            corpse_result = {"ok": True, "corpse": death_hit.get("corpse") or {}}
        else:
            corpse_result = self.bridge.process_delver_death(char_id)
        if not corpse_result.get("ok"):
            return None
        self.combat.active = False
        self.setup_new_game(campaign_slug)
        corpse = corpse_result.get("corpse") or {}
        name = corpse.get("display_name", "The delver")
        site = corpse.get("site_address") or corpse.get("cell_address") or "the site"
        room = corpse.get("room_id")
        where = f"{site} / {room}" if room else str(site)
        return (
            f"**{name}** is dead. The body remains in **{where}** — gear still on the corpse for anyone who finds it.\n\n"
            "This run is over. A **new game** has started. Welcome to the Registry, delver. What is your name?"
        )

    def _delete_save_file(self):
        """Remove the UI session state file."""
        from pathlib import Path
        save_path = Path(__file__).resolve().parents[1] / "session_state.json"
        try:
            save_path.unlink(missing_ok=True)
        except Exception:
            pass

    def _remember_player_choice(
        self,
        fact: str,
        *,
        entities: list[str] | None = None,
        importance: int = 4,
    ) -> None:
        """Persist a player choice and its impact to campaign memory."""
        if not fact:
            return
        try:
            self.bridge.remember_fact(fact, entities=entities, importance=importance)
        except Exception:
            pass

    def _remember_creation_step(self, completed_step: str) -> None:
        fact = creation_choice_fact(completed_step, self.creation)
        if not fact:
            return
        entities = [self.creation.name] if self.creation.name else None
        self._remember_player_choice(fact, entities=entities, importance=5)

    def _build_exploration_context(self) -> dict | None:
        """Build exploration context (scene, surroundings, features) for the current turn."""
        try:
            self.bridge.ensure_cell_initialized()

            session_id = self.bridge._active_session_id()
            campaign_slug = self.bridge._campaign_slug()
            conn = self.bridge.ctx.conn

            ps = conn.execute(
                "SELECT address, scene_index, scene_max, heading, mode, site_id, dungeon_room_id FROM party_state WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if not ps:
                return None

            from tomb_gm.services.content import ContentService
            content = ContentService(self.bridge.ctx.config.content_root)

            result: dict = {}

            if ps["mode"] == "dungeon":
                # Dungeon mode — show room info
                from tomb_gm.services.exploration import ExplorationService
                svc = ExplorationService(conn, content)
                room_info = svc.current_room_info(session_id)
                if room_info:
                    result["dungeon_info"] = room_info
            else:
                # Surface mode — show scene, features, compass
                result["scene_info"] = {
                    "scene_index": ps["scene_index"],
                    "scene_max": ps["scene_max"],
                    "heading": ps["heading"],
                }

                cell = content.get_cell(ps["address"])
                if cell:
                    result["cell_info"] = {
                        "terrain": cell.get("terrain", "unknown"),
                        "population": cell.get("population", "unknown"),
                        "displayName": cell.get("displayName", ps["address"]),
                        "loreHooks": cell.get("loreHooks", []),
                        "dangerRating": cell.get("dangerRating"),
                    }

                # Get discovered features in current cell
                rows = conn.execute(
                    "SELECT * FROM cell_features WHERE cell_address = ? AND discovered = 1 ORDER BY scene_position",
                    (ps["address"],),
                ).fetchall()
                if rows:
                    result["discovered_features"] = [dict(r) for r in rows]

                # Compass exits
                from tomb_gm.services.exploration import ExplorationService
                svc = ExplorationService(conn, content)
                compass = svc.compass_exits(ps["address"], campaign_slug)
                if compass:
                    result["compass"] = compass

            return result if result else None
        except Exception:
            return None

    def process_turn(self, player_input: str) -> str:
        """Process a player turn and return GM narration text."""
        log_player_input(player_input)

        lower = player_input.lower().strip()
        if lower in ("new game", "start", "new"):
            result = self.setup_new_game()
            if not result.get("ok"):
                log_error("setup_new_game", result.get("error", "unknown"))
                return f"Could not start game: {result.get('error', 'unknown')}"
            return self._creation_turn("[SYSTEM: New game started. Begin character creation.]")

        elif lower in ("continue", "resume", "load", "load game"):
            result = self.bridge.session_resume()
            if not result.get("ok"):
                log_error("session_resume", result.get("error", "unknown"))
                return f"Could not resume: {result.get('error', 'unknown')}. Try 'new game' instead."
            if result.get("run_ended"):
                campaign_slug = result.get("campaign_slug", "salt-road")
                corpses = result.get("corpses") or []
                where = "the delve"
                if corpses:
                    c0 = corpses[0] or {}
                    site = c0.get("site_address") or c0.get("cell_address") or where
                    room = c0.get("room_id")
                    where = f"{site} / {room}" if room else str(site)
                self.setup_new_game(campaign_slug)
                death_msg = (
                    f"Your previous delver did not survive (0 HP after the last fight). "
                    f"The body remains in **{where}** with all carried gear.\n\n"
                    "This run is over. A **new game** has started. What is your delver's name?"
                )
                self._emit_narration(death_msg)
                return death_msg
            self._restore_history()
            self._sync_creation_from_status()
            self._sync_combat_from_status()
            status = self.bridge.status()
            if result.get("recovered_campaign"):
                log_error("session_resume", f"recovered save campaign: {result.get('campaign_slug')}")
            if status.get("awaiting") == "CHARACTER_CREATION" and not status.get("roster"):
                if not self.creation.active:
                    self._restore_history()
                if not self.creation.active:
                    self.creation = CreationState(active=True, step="NAME")
                return self._creation_turn(
                    "[SYSTEM: Resume character creation. Continue from the current step.]"
                )
            if status.get("awaiting") == "COMBAT_TURN" or status.get("combat"):
                return self._combat_turn(player_input)

            recap = self.bridge.build_recap()
            recap_text = recap.get("recap_text", "")
            recent = recap.get("recent_events", [])
            summary_parts = ["[SYSTEM: Session resumed from database.]"]
            if recap_text:
                summary_parts.append(f"Campaign memory: {recap_text}")
            if recent:
                last_events = [e.get("event_type", "?") + ": " + str(e.get("payload", {}))[:60] for e in recent[-5:]]
                summary_parts.append(f"Recent events: {'; '.join(last_events)}")
            player_input = "\n".join(summary_parts) + "\n\nWelcome me back and remind me where I am and what's happening."

        if self.creation.active:
            return self._creation_turn(player_input)

        self._sync_combat_from_status()
        if self.combat.active or self._combat_active_in_db():
            return self._combat_turn(player_input)

        status = self.bridge.status()
        check = self.bridge.check()
        suggest = self.bridge.suggest()
        recap = self.bridge.build_recap()

        # Build exploration context (surroundings, scene, features)
        exploration = self._build_exploration_context()

        inv = self.bridge.list_inventory()
        inventory_summary = inv.get("summary") if inv.get("ok") else None

        state_context = build_state_context(
            status, recap, check, suggest, exploration, inventory_summary=inventory_summary
        )

        if SPELL_QUERY_RE.search(player_input):
            roster = status.get("roster") or []
            if roster:
                char_id = roster[0].get("character_id")
                spell_info = self.bridge.list_known_spells(char_id)
                if spell_info.get("ok"):
                    lines = spell_info.get("spell_lines") or []
                    state_context += (
                        "\n\n## Known Spells (authoritative — do NOT invent others)\n"
                        + "\n".join(f"  - {line}" for line in lines)
                    )

        messages = build_messages(
            SYSTEM_PROMPT,
            state_context,
            self.history,
            player_input,
        )

        narration = self._llm_loop(messages)
        self._emit_narration(narration)

        self.history.append({"role": "user", "content": player_input})
        self.history.append({"role": "assistant", "content": narration})

        if len(self.history) > 40:
            self.history = self.history[-30:]

        return narration

    def _compose_creation_narration(
        self,
        flavor: str,
        body: str = "",
        *,
        footer: str | None = None,
    ) -> str:
        """Thin LLM flavor + code body + code-owned status footer."""
        parts: list[str] = []
        cleaned = strip_llm_status_tags(flavor)
        if cleaned:
            parts.append(cleaned)
        if body.strip():
            parts.append(body.strip())
        status_line = footer if footer is not None else format_creation_status(self.creation)
        if status_line:
            parts.append(status_line)
        return "\n\n".join(parts)

    def _creation_flavor_messages(self, instruction: str, player_input: str) -> list[dict[str, Any]]:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "system",
                "content": (
                    "You are the GM for Tomb Dust at the Registry desk in Breley Keep.\n"
                    f"Character: {self.creation.name or '(unnamed)'}\n"
                    f"Creation step: {self.creation.step}\n\n"
                    f"{instruction}\n\n"
                    "Write 1-2 short sentences of in-character flavor ONLY.\n"
                    "Do NOT include markdown tables, status lines, [Location:...], Phase, Awaiting, "
                    "or mechanical numbers — code appends those."
                ),
            },
            *self.history[-4:],
            {"role": "user", "content": player_input},
        ]

    def _narrate_flavor(self, messages: list[dict[str, Any]]) -> str:
        """Short LLM flavor during creation (~120 tokens, no tools)."""
        log_llm_request(len(messages), self.model, 0)
        try:
            response = chat_completion(
                self.client,
                model=self.model,
                messages=messages,
                tools=None,
                max_tokens=_CREATION_FLAVOR_MAX_TOKENS,
                temperature=self.temperature,
            )
        except Exception as exc:
            log_error("narrate_flavor", str(exc))
            return "The clerk glances up from the ledger."
        content = response.get("content", "") or "The clerk glances up from the ledger."
        log_llm_response(content, [], response.get("finish_reason", ""))
        return content

    # ─── Creation State Machine (code-enforced) ───────────────────────────

    def _creation_turn(self, player_input: str) -> str:
        """State-machine-driven creation turn. Code decides what happens; LLM narrates."""
        try:
            return self._creation_turn_body(player_input)
        finally:
            self._log_creation_step_snapshot()

    def _creation_turn_body(self, player_input: str) -> str:
        if self.creation.step == "WORLD_INTRO" and not self.creation.active:
            return self.process_turn("look around")

        is_system_trigger = player_input.startswith("[SYSTEM:") or player_input.startswith("[Step advanced")

        if self.creation.step == "ROLL_STATS":
            narration = self._auto_roll_stats(player_input)
        elif self.creation.step == "FINALIZE":
            narration = self._auto_finalize(player_input)
        elif self.creation.step == "NAME" and (is_system_trigger or player_input.startswith("[SYSTEM:")):
            narration = self._auto_present_name(player_input)
        elif self.creation.step == "NAME":
            narration = self._handle_creation_response(player_input) or self._auto_present_name(
                player_input,
                error="Give a name of at least two characters for the Registry ledger.",
            )
        elif self.creation.step == "RACE" and (is_system_trigger or not self.creation.race):
            narration = self._auto_present_race(player_input)
        elif self.creation.step == "RACE":
            narration = self._handle_creation_response(player_input) or self._auto_present_race(
                player_input,
                error="Pick one race from the table.",
            )
        elif self.creation.step == "CLASS" and (is_system_trigger or not self.creation.chosen_class):
            narration = self._auto_present_class(player_input)
        elif self.creation.step == "CLASS":
            narration = self._handle_creation_response(player_input) or self._auto_present_class(
                player_input,
                error="Pick one eligible class from the table.",
            )
        elif self.creation.step == "SKILLS" and (is_system_trigger or not self.creation.skills_table_shown):
            narration = self._auto_present_skills(player_input)
        elif self.creation.step == "SKILLS":
            narration = self._handle_creation_response(player_input) or self._auto_present_skills(
                player_input,
                error="Pick exactly 3 skills from the table, comma-separated.",
            )
        elif self.creation.step == "SPELL_SCHOOLS" and (is_system_trigger or not self.creation.schools_table_shown):
            narration = self._auto_present_schools(player_input)
        elif self.creation.step == "SPELL_SCHOOLS":
            narration = self._handle_creation_response(player_input) or self._auto_present_schools(
                player_input,
                error="Pick exactly 2 spell schools from the table, comma-separated.",
            )
        elif self.creation.step == "SPELLS" and (is_system_trigger or not self.creation.spells_table_shown):
            narration = self._auto_present_spells(player_input)
        elif self.creation.step == "SPELLS":
            narration = self._handle_creation_response(player_input) or self._auto_present_spells(
                player_input,
                error="Pick exactly 2 tier-1 spells from the table, comma-separated.",
            )
        elif self.creation.step == "EQUIPMENT_GOLD" and is_system_trigger:
            ensure_equipment_gold(self.creation)
            narration = self._auto_present_equipment(player_input)
        elif self.creation.step == "EQUIPMENT_GOLD":
            narration = self._handle_creation_response(player_input) or self._auto_present_equipment(
                player_input,
                error="Say yes or ready when you accept the kit and starting gold.",
            )
        elif is_system_trigger:
            narration = self._auto_present_step_fallback(player_input)
        else:
            direct = self._handle_creation_response(player_input)
            if direct is not None:
                narration = direct
            elif self.creation.step in ("SKILLS", "SPELL_SCHOOLS", "SPELLS", "EQUIPMENT_GOLD"):
                narration = "The clerk taps the form. That choice is not on the ledger — follow the instructions on the table."
            else:
                narration = self._auto_present_step_fallback(
                    player_input,
                    error="That response does not match this step — follow the table or prompt.",
                )

        self._emit_narration(narration)
        self.history.append({"role": "user", "content": player_input})
        self.history.append({"role": "assistant", "content": narration})
        return narration

    def _auto_present_step_fallback(self, player_input: str, error: str | None = None) -> str:
        step = self.creation.step
        if step == "NAME":
            return self._auto_present_name(player_input, error=error)
        if step == "RACE":
            return self._auto_present_race(player_input, error=error)
        if step == "CLASS":
            return self._auto_present_class(player_input, error=error)
        if step == "SKILLS":
            return self._auto_present_skills(player_input, error=error)
        if step == "SPELL_SCHOOLS":
            return self._auto_present_schools(player_input, error=error)
        if step == "SPELLS":
            return self._auto_present_spells(player_input, error=error)
        if step == "EQUIPMENT_GOLD":
            return self._auto_present_equipment(player_input, error=error)
        return "The clerk waits for your next answer on the form."

    def _auto_present_name(self, player_input: str, error: str | None = None) -> str:
        err = f"**Note:** {error}\n\n" if error else ""
        flavor = self._narrate_flavor(
            self._creation_flavor_messages(
                "A Registry clerk asks a new delver for their legal name.",
                player_input,
            )
        )
        body = f"{err}What name shall I put on the Registry ledger?"
        return self._compose_creation_narration(flavor, body)

    def _auto_present_race(self, player_input: str, error: str | None = None) -> str:
        err = f"**Note:** {error}\n\n" if error else ""
        flavor = self._narrate_flavor(
            self._creation_flavor_messages(
                f"The clerk writes down '{self.creation.name}' and asks about lineage.",
                player_input,
            )
        )
        body = err + format_races_table()
        return self._compose_creation_narration(flavor, body)

    def _auto_present_class(self, player_input: str, error: str | None = None) -> str:
        err = f"**Note:** {error}\n\n" if error else ""
        eligible = self.creation.roll_result.get("eligible_classes", ["peasant"])
        attrs = self.creation.roll_result.get("final_attributes", {})
        flavor = self._narrate_flavor(
            self._creation_flavor_messages(
                "Present the stat results briefly, then ask which tier-1 class path the delver chooses.",
                player_input,
            )
        )
        stat_bits = ", ".join(f"{k} {v}" for k, v in sorted(attrs.items()))
        body = f"{err}**Final attributes:** {stat_bits}\n\n{format_classes_table(eligible)}"
        return self._compose_creation_narration(flavor, body)

    def _handle_creation_response(self, player_input: str) -> str | None:
        """Code-first handling for gated steps. Returns narration or None to defer."""
        step = self.creation.step

        if step == "NAME":
            text = player_input.strip()
            if text.startswith("[") or len(text) < 2:
                return None
            if is_equipment_confirm(text):
                return self._auto_present_name(
                    player_input,
                    error="A name is required — yes/ready is not valid here.",
                )
            result = self._execute_creation_choice("NAME", text, player_input=player_input)
            if not result.get("ok"):
                return self._auto_present_name(player_input, error=result.get("error"))
            return self._chain_after_creation_choice("")

        if step == "RACE":
            if is_equipment_confirm(player_input):
                return self._auto_present_race(
                    player_input,
                    error="Pick a race from the table — yes/ready is not valid here.",
                )
            race = parse_player_race(player_input)
            if not race:
                return None
            result = self._execute_creation_choice("RACE", race, player_input=player_input)
            if not result.get("ok"):
                return self._auto_present_race(player_input, error=result.get("error"))
            return self._chain_after_creation_choice("")

        if step == "CLASS":
            if is_equipment_confirm(player_input):
                return self._auto_present_class(
                    player_input,
                    error="Pick a class from the table — yes/ready is not valid here.",
                )
            eligible = self.creation.roll_result.get("eligible_classes", ["peasant"])
            chosen = parse_player_class(player_input, eligible)
            if not chosen:
                return None
            result = self._execute_creation_choice("CLASS", chosen, player_input=player_input)
            if not result.get("ok"):
                return self._auto_present_class(player_input, error=result.get("error"))
            return self._chain_after_creation_choice("")

        if step == "SKILLS":
            if is_equipment_confirm(player_input):
                return self._auto_present_skills(
                    player_input,
                    error="Name three skills from the table — yes/ready is not valid here.",
                )
            skills = parse_player_skills(player_input, self.creation.chosen_class)
            if not skills:
                return self._auto_present_skills(
                    player_input,
                    error="Name exactly 3 skills from the table, comma-separated.",
                )
            result = self._execute_creation_choice(
                "SKILLS", ",".join(skills), player_input=player_input,
            )
            if not result.get("ok"):
                key_names = ", ".join(
                    CLASS_INFO.get(self.creation.chosen_class, {}).get("key_skills", [])
                )
                err = result.get("error", "Invalid skill picks.")
                if "key abilities" in err.lower() or "key skill" in err.lower():
                    err = (
                        f"{err} For {self.creation.chosen_class.title()}, pick at least one key skill (★): "
                        f"{key_names}."
                    )
                return self._auto_present_skills(player_input, error=err)
            return self._chain_after_creation_choice("")

        if step == "SPELL_SCHOOLS":
            if is_equipment_confirm(player_input):
                return self._auto_present_schools(
                    player_input,
                    error="Pick spell schools from the table — yes/ready is not valid here.",
                )
            if not needs_spell_picks(self.creation):
                skip_inapplicable_spell_steps(self.creation)
                return self._chain_after_creation_choice("")
            schools = parse_player_schools(player_input, self.creation.chosen_class)
            if not schools:
                return self._auto_present_schools(
                    player_input,
                    error="Name exactly 2 schools from the table, comma-separated.",
                )
            result = self._execute_creation_choice(
                "SPELL_SCHOOLS", ",".join(schools), player_input=player_input,
            )
            if not result.get("ok"):
                return self._auto_present_schools(player_input, error=result.get("error"))
            return self._chain_after_creation_choice("")

        if step == "SPELLS":
            if is_equipment_confirm(player_input):
                return self._auto_present_spells(
                    player_input,
                    error="Pick tier-1 spells from the table — yes/ready is not valid here.",
                )
            spells = parse_player_spells(
                player_input, self.creation.chosen_class, self.creation.chosen_schools,
            )
            if not spells:
                return self._auto_present_spells(
                    player_input,
                    error="Name exactly 2 tier-1 spells from the table, comma-separated.",
                )
            result = self._execute_creation_choice(
                "SPELLS", ",".join(spells), player_input=player_input,
            )
            if not result.get("ok"):
                return self._auto_present_spells(player_input, error=result.get("error"))
            return self._chain_after_creation_choice("")

        if step == "EQUIPMENT_GOLD":
            if is_equipment_objection(player_input) or not is_equipment_confirm(player_input):
                return self._auto_present_equipment(
                    player_input,
                    error="Say yes or ready when you accept the kit and starting gold.",
                )
            result = self._execute_creation_choice(
                "EQUIPMENT_GOLD", "confirmed", player_input=player_input,
            )
            if not result.get("ok"):
                return self._auto_present_equipment(player_input, error=result.get("error"))
            return self._chain_after_creation_choice("")

        return None

    def _chain_after_creation_choice(self, prior: str) -> str:
        """Run deterministic follow-up after a creation step advances."""
        if self.creation.step == "ROLL_STATS":
            return self._auto_roll_stats("[SYSTEM: Step auto-advanced. Continue.]")
        if self.creation.step == "SKILLS":
            extra = self._auto_present_skills("[SYSTEM: Step auto-advanced. Continue.]")
            return f"{prior}\n\n{extra}".strip() if prior else extra
        if self.creation.step == "SPELL_SCHOOLS":
            extra = self._auto_present_schools("[SYSTEM: Step auto-advanced. Continue.]")
            return f"{prior}\n\n{extra}".strip() if prior else extra
        if self.creation.step == "SPELLS":
            extra = self._auto_present_spells("[SYSTEM: Step auto-advanced. Continue.]")
            return f"{prior}\n\n{extra}".strip() if prior else extra
        if self.creation.step == "EQUIPMENT_GOLD":
            extra = self._auto_present_equipment("[SYSTEM: Step auto-advanced. Continue.]")
            return f"{prior}\n\n{extra}".strip() if prior else extra
        if self.creation.step == "FINALIZE":
            extra = self._auto_finalize("[SYSTEM: Step auto-advanced. Continue.]")
            return f"{prior}\n\n{extra}".strip() if prior else extra
        return prior or "The clerk waits."

    def _auto_present_skills(self, player_input: str, error: str | None = None) -> str:
        """Deterministic skills table — code body, thin LLM flavor."""
        self.creation.skills_table_shown = True
        err = f"**Note:** {error}\n\n" if error else ""
        flavor = self._narrate_flavor(
            self._creation_flavor_messages(
                f"Ask {self.creation.name} which three skills they trained in as a {self.creation.chosen_class}.",
                player_input,
            )
        )
        body = err + format_skills_table(self.creation.chosen_class)
        return self._compose_creation_narration(flavor, body)

    def _auto_present_schools(self, player_input: str, error: str | None = None) -> str:
        """Deterministic spell school table."""
        skip_inapplicable_spell_steps(self.creation)
        if self.creation.step != "SPELL_SCHOOLS":
            return self._chain_after_creation_choice("")
        self.creation.schools_table_shown = True
        err = f"**Note:** {error}\n\n" if error else ""
        flavor = self._narrate_flavor(
            self._creation_flavor_messages(
                "Ask which magical schools the delver studied.",
                player_input,
            )
        )
        body = err + format_schools_table(self.creation.chosen_class)
        return self._compose_creation_narration(flavor, body)

    def _auto_present_spells(self, player_input: str, error: str | None = None) -> str:
        """Deterministic starting spell table."""
        self.creation.spells_table_shown = True
        err = f"**Note:** {error}\n\n" if error else ""
        flavor = self._narrate_flavor(
            self._creation_flavor_messages(
                "Ask which tier-1 spells the delver memorized from their chosen schools.",
                player_input,
            )
        )
        body = err + format_spells_table(self.creation.chosen_class, self.creation.chosen_schools)
        return self._compose_creation_narration(flavor, body)

    def _auto_present_equipment(self, player_input: str, error: str | None = None) -> str:
        """Present kit and gold from ensure_equipment_gold; require explicit confirm."""
        ensure_equipment_gold(self.creation)
        err = f"**Note:** {error}\n\n" if error else ""
        flavor = self._narrate_flavor(
            self._creation_flavor_messages(
                "Hand over the Registry kit and coin pouch; ask for explicit confirmation.",
                player_input,
            )
        )
        body = err + format_equipment_summary(self.creation)
        return self._compose_creation_narration(flavor, body)

    def _auto_roll_stats(self, player_input: str) -> str:
        """ROLL_STATS is deterministic: code rolls, LLM narrates the table."""
        result = self.bridge.roll_attributes(self.creation.race)
        log_tool_call("roll_attributes", {"race": self.creation.race}, result)
        self.creation.roll_result = result
        self.creation.advance()
        self._remember_creation_step("ROLL_STATS")

        attrs = result.get("final_attributes", {})
        eligible = result.get("eligible_classes", ["peasant"])
        sta = attrs.get("STA", 10)
        hp = 10 + (sta * 5)

        context = (
            f"You are the GM for Tomb Dust. Character creation — present attribute results.\n"
            f"Current state: {json.dumps(self.creation.to_dict())}\n\n"
            f"RESULTS TO NARRATE (present as a table with SHORT headers: Attr | Base | Genetic | Life Evt | Racial | Final):\n"
            f"{json.dumps(result, indent=2)}\n\n"
            f"HP = 10 + (STA {sta} x 5) = {hp}\n"
            f"Eligible classes: {eligible}\n\n"
            f"Write 1-2 sentences of narration, then the stat table, then state HP.\n"
            f"Then present the eligible classes and ask the player to choose.\n"
            f"Do NOT call any tools. Just narrate."
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": context},
        ]
        if self.history:
            messages.extend(self.history[-4:])
        messages.append({"role": "user", "content": player_input})
        return self._narrate_only(messages)

    def _creation_spell_defaults(self) -> tuple[list[str], list[str]]:
        """Fallback schools/spells when player picks were skipped."""
        if self.creation.chosen_schools and self.creation.chosen_spells:
            return list(self.creation.chosen_schools), list(self.creation.chosen_spells)
        cls = self.creation.chosen_class
        skills = set(self.creation.chosen_skills)
        if "spellcasting" not in skills:
            return [], []
        if cls == "novice":
            return ["divine", "ward"], ["mend-light", "consecrate-ground"]
        if cls == "apprentice":
            return ["pyromancy", "ether"], ["ember-touch", "static-lash"]
        return [], []

    def _auto_finalize(self, player_input: str) -> str:
        """FINALIZE is deterministic: code commits character, LLM narrates world intro."""
        attrs = self.creation.roll_result.get("final_attributes", {})
        ensure_equipment_gold(self.creation)
        from tomb_gm.domain.creation import starting_kit

        kit = starting_kit(self.bridge.ctx.config.content_root, self.creation.chosen_class)
        remaining_gp = max(0, self.creation.starting_gold - int(kit.get("costGp", 0)))
        creation_audit = {
            "race": self.creation.race,
            "class": self.creation.chosen_class,
            "skills": list(self.creation.chosen_skills),
            "startingGold": self.creation.starting_gold,
            "kitCostGp": int(kit.get("costGp", 0)),
            "remainingGp": remaining_gp,
            "goldRoll": self.creation.gold_roll,
            "rollResult": self.creation.roll_result,
        }
        spell_schools, known_spells = self._creation_spell_defaults()
        result = self.bridge.character_create(
            name=self.creation.name,
            background=self.creation.chosen_class,
            str_score=attrs.get("STR", 10),
            agi_score=attrs.get("AGI", 10),
            end_score=attrs.get("STA", 10),
            int_score=attrs.get("INT", 10),
            wil_score=attrs.get("SPI", 10),
            luc_score=attrs.get("LUC", 10),
            skill_ids=list(self.creation.chosen_skills),
            race_id=self.creation.race,
            gold_gp=remaining_gp,
            creation_audit=creation_audit,
            known_spell_ids=known_spells or None,
            spell_school_ids=spell_schools or None,
        )
        log_tool_call("character_create", {"name": self.creation.name}, result)
        self._log_creation_finalize_status(result)
        if not result.get("ok"):
            self.creation.active = True
            self.creation.step = "EQUIPMENT_GOLD"
            return self._auto_present_equipment(
                player_input,
                error=f"Registration failed: {result.get('error', 'unknown error')}",
            )

        try:
            status = self.bridge.status()
        except Exception as exc:
            status = {"_error": str(exc)}
        roster = status.get("roster") or []
        if not roster:
            self.creation.active = True
            self.creation.step = "FINALIZE"
            return (
                "The clerk stamps the form but the roster ledger stays blank. "
                f"Registration did not produce a living character ({result.get('error', 'empty roster')}). "
                "Try confirming equipment again or start a new game."
            )

        self._remember_creation_step("FINALIZE")
        self.creation.active = False
        self.creation.step = "WORLD_INTRO"

        sta = attrs.get("STA", 10)
        hp = 10 + (sta * 5)
        cls_info = CLASS_INFO.get(self.creation.chosen_class, {})
        base_mp = cls_info.get("base_mp", 5)
        int_score = attrs.get("INT", 10)
        mp = base_mp + (int_score * 3)
        luc = max(1, 1 + (attrs.get("LUC", 10) - 10) // 2)

        flavor = self._narrate_flavor(
            self._creation_flavor_messages(
                f"Character {self.creation.name} is registered. Describe them stepping into Breley Keep "
                "(outer bailey, garrison, King's Road, smithies, postern gate). End by asking what they do first.",
                player_input,
            )
        )
        body = (
            f"**{self.creation.name}** is registered — {self.creation.race.replace('-', ' ').title()} "
            f"{self.creation.chosen_class.title()}.\n\n"
            f"HP {hp}/{hp} · MP {mp} · Fortune {luc}/{luc} · GP {remaining_gp}\n\n"
            f"Skills: {', '.join(self.creation.chosen_skills)}\n"
            f"Kit: {cls_info.get('kit', 'basic gear')}"
        )
        footer = f"[Location: 32-C | Phase: preparation | HP: {hp}/{hp} | Fortune: {luc}/{luc} | GP: {remaining_gp}]\nAwaiting: RECEPTION_CHOICE"
        return self._compose_creation_narration(flavor, body, footer=footer)

    def _narrate_only(self, messages: list[dict[str, Any]]) -> str:
        """Call LLM with NO tools — pure narration."""
        log_llm_request(len(messages), self.model, 0)
        try:
            response = chat_completion(
                self.client,
                model=self.model,
                messages=messages,
                tools=None,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
        except Exception as exc:
            log_error("narrate_only", str(exc))
            return "The clerk regards you with a weary sigh."

        log_llm_response(response.get("content", ""), [], response.get("finish_reason", ""))
        return response.get("content", "") or "The clerk shuffles papers."

    def _creation_llm_loop(
        self,
        messages: list[dict[str, Any]],
        tools: list,
        tool_choice: dict | str,
        player_input: str = "",
    ) -> str:
        """LLM loop for interactive creation steps. Gated tools + forced tool_choice."""
        for depth in range(4):
            log_llm_request(len(messages), self.model, depth)

            try:
                response = chat_completion(
                    self.client,
                    model=self.model,
                    messages=messages,
                    tools=tools if depth < 2 else None,
                    tool_choice=tool_choice if depth < 2 else "none",
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
            except Exception as exc:
                log_error("creation_llm_loop", str(exc))
                return "The clerk mutters something unintelligible."

            tool_calls = response.get("tool_calls", [])
            content = response.get("content", "")
            log_llm_response(content, tool_calls, response.get("finish_reason", ""))

            if not tool_calls:
                if self.creation.step in ("SKILLS", "SPELL_SCHOOLS", "SPELLS", "EQUIPMENT_GOLD"):
                    fallback = self._handle_creation_response(player_input)
                    if fallback:
                        return fallback
                    return "The clerk waits for a valid choice from the table."
                return content or "The clerk waits patiently."

            messages.append({
                "role": "assistant",
                "content": content or None,
                "tool_calls": tool_calls,
            })

            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                try:
                    args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    args = {}

                if fn_name != "set_creation_choice":
                    result = {"ok": False, "error": f"Only set_creation_choice is available. Got: {fn_name}"}
                else:
                    result = self._execute_creation_choice(
                        args.get("step", ""),
                        args.get("value", ""),
                        player_input=player_input,
                    )

                log_tool_call(fn_name, args, result)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result, default=str),
                })

                if result.get("ok"):
                    if self.creation.step in ("ROLL_STATS", "FINALIZE", "WORLD_INTRO"):
                        chain_narration = content or ""
                        auto_result = self._chain_after_creation_choice(chain_narration)
                        return auto_result.strip()

                    if self.creation.step == "SKILLS":
                        chain_narration = content or ""
                        auto_result = self._auto_present_skills("[SYSTEM: Step auto-advanced. Continue.]")
                        return f"{chain_narration}\n\n{auto_result}".strip()

                    if self.creation.step == "SPELL_SCHOOLS":
                        chain_narration = content or ""
                        auto_result = self._auto_present_schools("[SYSTEM: Step auto-advanced. Continue.]")
                        return f"{chain_narration}\n\n{auto_result}".strip()

                    if self.creation.step == "SPELLS":
                        chain_narration = content or ""
                        auto_result = self._auto_present_spells("[SYSTEM: Step auto-advanced. Continue.]")
                        return f"{chain_narration}\n\n{auto_result}".strip()

                    if self.creation.step == "EQUIPMENT_GOLD":
                        chain_narration = content or ""
                        auto_result = self._auto_present_equipment("[SYSTEM: Step auto-advanced. Continue.]")
                        return f"{chain_narration}\n\n{auto_result}".strip()

                    messages.append({
                        "role": "user",
                        "content": f"[Step advanced to {self.creation.step}. Narrate the transition briefly. Do NOT call tools again.]",
                    })
                    tools = None
                    tool_choice = "none"

        return content or "The clerk waits."

    def _execute_creation_choice(
        self,
        step: str,
        value: str,
        *,
        player_input: str = "",
    ) -> dict:
        """Validate and execute a creation choice. Strict enforcement."""
        if step != self.creation.step:
            return {"ok": False, "error": f"Expected step {self.creation.step}, got {step}. Use step='{self.creation.step}'."}

        source_text = player_input or value

        if step == "NAME":
            name = value.strip()
            if len(name) < 2:
                return {"ok": False, "error": "Name must be at least 2 characters."}
            self.creation.name = name.title()

        elif step == "RACE":
            race = value.strip().lower().replace(" ", "-")
            if race not in RACES:
                parsed = parse_player_race(source_text)
                if parsed:
                    race = parsed
                else:
                    return {"ok": False, "error": f"Invalid race '{race}'. Valid: {list(RACES.keys())}"}
            self.creation.race = race

        elif step == "CLASS":
            chosen = value.strip().lower()
            eligible = self.creation.roll_result.get("eligible_classes", ["peasant"])
            if chosen not in eligible:
                parsed = parse_player_class(source_text, eligible)
                if parsed:
                    chosen = parsed
                else:
                    return {"ok": False, "error": f"Class '{chosen}' not eligible. Eligible: {eligible}."}
            self.creation.chosen_class = chosen

        elif step == "SKILLS":
            if not self.creation.skills_table_shown:
                return {"ok": False, "error": "Skills table must be shown before recording picks."}
            parsed = parse_player_skills(source_text, self.creation.chosen_class)
            if not parsed:
                return {"ok": False, "error": "Could not parse 3 skills from player input. Re-show the table."}
            tool_slugs = []
            for part in value.split(","):
                slug = normalize_skill_slug(part)
                if slug:
                    tool_slugs.append(slug)
            if tool_slugs and set(tool_slugs) != set(parsed):
                return {
                    "ok": False,
                    "error": "Recorded skills must match what the player chose.",
                    "expected": parsed,
                    "got": tool_slugs,
                }
            err = validate_skill_picks(self.creation.chosen_class, parsed)
            if err:
                return {"ok": False, "error": err}
            self.creation.chosen_skills = parsed

        elif step == "SPELL_SCHOOLS":
            if not self.creation.schools_table_shown:
                return {"ok": False, "error": "Schools table must be shown before recording picks."}
            parsed = parse_player_schools(source_text, self.creation.chosen_class)
            if not parsed:
                return {"ok": False, "error": "Could not parse school picks. Re-show the table."}
            err = validate_school_picks(self.creation.chosen_class, parsed)
            if err:
                return {"ok": False, "error": err}
            self.creation.chosen_schools = parsed

        elif step == "SPELLS":
            if not self.creation.spells_table_shown:
                return {"ok": False, "error": "Spells table must be shown before recording picks."}
            parsed = parse_player_spells(
                source_text, self.creation.chosen_class, self.creation.chosen_schools,
            )
            if not parsed:
                return {"ok": False, "error": "Could not parse spell picks. Re-show the table."}
            err = validate_spell_picks(
                self.creation.chosen_class, self.creation.chosen_schools, parsed,
            )
            if err:
                return {"ok": False, "error": err}
            self.creation.chosen_spells = parsed

        elif step == "EQUIPMENT_GOLD":
            if is_equipment_objection(source_text):
                return {"ok": False, "error": "Player has not confirmed equipment yet."}
            if not is_equipment_confirm(source_text):
                return {"ok": False, "error": "Player must explicitly confirm (yes/ready/confirm)."}
            ensure_equipment_gold(self.creation)

        self.creation.advance()
        self._remember_creation_step(step)
        log_creation_advanced({
            "completed_step": step,
            "advanced_to": self.creation.step,
        })
        return {"ok": True, "advanced_to": self.creation.step, "state": self.creation.to_dict()}

    # ─── Combat State Machine ─────────────────────────────────────────────

    def _narrate_text(self, prompt: str) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        return self._narrate_only(messages)

    def _combat_auto_chain(self) -> list[dict[str, Any]]:
        """Run monster turns in code until a PC turn or combat ends."""
        if not self._combat_active_in_db():
            return []
        status = self.bridge.status()
        if not is_pc_turn(status) and status.get("combat", {}).get("turn_kind") == "monster":
            result = self.bridge.run_combat_monster_turns()
            mechanical = result.get("mechanical") or []
            self.combat.last_mechanical = mechanical
            self._sync_combat_from_status()
            if not self._combat_active_in_db():
                self.combat.active = False
                self.combat.step = "COMBAT_AFTERMATH"
            return mechanical
        return []

    def _combat_mechanical_brief(self, mechanical: list[dict]) -> str:
        lines = ["[COMBAT MECHANICS — narrate ONLY these results]"]
        for item in mechanical:
            action = item.get("action") or item.get("kind") or "step"
            if action == "initiative_round":
                lines.append(format_initiative_table(item.get("initiative") or []))
            elif action in ("combat_attack", "monster_attack"):
                hit = item.get("hit")
                dmg = item.get("damage")
                lines.append(
                    f"{action}: {item.get('attacker')} vs {item.get('target')} — "
                    f"hit={hit} damage={dmg} defeated={item.get('target_defeated', False)}"
                )
            elif action == "combat_end_check":
                if item.get("ended"):
                    lines.append(f"Combat ended: {item.get('outcome', 'unknown')} ({item.get('reason', '')})")
            elif item.get("ok") is False:
                lines.append(f"FAILED: {item.get('error', item)}")
            else:
                lines.append(json.dumps(item, default=str)[:200])
        return "\n".join(lines)

    def _combat_turn(self, player_input: str) -> str:
        """State-machine-driven combat turn."""
        self._sync_combat_from_status()

        if self.combat.pending_start:
            specs = self.combat.pending_monsters or ["grave-ghoul:1"]
            start = self.bridge.start_combat_from_trigger(specs)
            self.combat.pending_start = False
            self.combat.pending_monsters = []
            if not start.get("ok"):
                self.combat.active = False
                return f"[Mechanics failed — combat start: {start.get('error')}]\n\nCombat could not begin."
            self.combat.active = True
            self.combat.order_narrated = False
            mechanical = [start]
            auto = self._combat_auto_chain()
            mechanical.extend(auto)
            self.combat.last_mechanical = mechanical
            status = self.bridge.status()
            if not self._combat_active_in_db():
                narration = self._narrate_text(
                    self._combat_mechanical_brief(mechanical)
                    + "\n\nNarrate combat ending."
                )
                self.combat.active = False
                return narration
            if is_pc_turn(status):
                self.combat.step = "COMBAT_PC_ACTION"
            else:
                auto = self._combat_auto_chain()
                mechanical.extend(auto)
                status = self.bridge.status()

        mechanical = self._combat_auto_chain()

        if not self._combat_active_in_db():
            brief = self._combat_mechanical_brief(self.combat.last_mechanical + mechanical)
            narration = self._narrate_text(brief + "\n\nNarrate how combat ended.")
            self.combat.active = False
            self.combat.step = "COMBAT_IDLE"
            self._emit_narration(narration)
            self.history.append({"role": "user", "content": player_input})
            self.history.append({"role": "assistant", "content": narration})
            return narration

        status = self.bridge.status()
        if not self.combat.order_narrated and status.get("combat"):
            init_table = format_initiative_table(status["combat"].get("initiative") or [])
            self.combat.order_narrated = True
            if not is_pc_turn(status):
                mechanical = self._combat_auto_chain()
                status = self.bridge.status()

        if is_pc_turn(status):
            self.combat.step = "COMBAT_PC_ACTION"
            narration = self._combat_llm_loop(player_input, status)
        else:
            mechanical = self._combat_auto_chain()
            death_narration = self._handle_player_death(mechanical)
            if death_narration:
                self._emit_narration(death_narration)
                self.history.append({"role": "user", "content": player_input})
                self.history.append({"role": "assistant", "content": death_narration})
                return death_narration
            status = self.bridge.status()
            if is_pc_turn(status):
                narration = self._combat_llm_loop(player_input, status)
            else:
                brief = self._combat_mechanical_brief(mechanical)
                narration = self._narrate_text(brief + "\n\nMonsters act. Narrate their attacks.")

        self._emit_narration(narration)
        self.history.append({"role": "user", "content": player_input})
        self.history.append({"role": "assistant", "content": narration})
        if len(self.history) > 40:
            self.history = self.history[-30:]
        return narration

    def _combat_llm_loop(self, player_input: str, status: dict) -> str:
        check = self.bridge.check()
        suggest = self.bridge.suggest()
        recap = self.bridge.build_recap()
        step_prompt = get_combat_step_prompt(self.combat, status)
        state_context = build_state_context(status, recap, check, suggest, None)
        if step_prompt:
            state_context += "\n\n## Combat Step\n" + step_prompt
        if self.combat.last_mechanical:
            state_context += "\n\n" + self._combat_mechanical_brief(self.combat.last_mechanical)
            self.combat.last_mechanical = []

        messages = build_messages(SYSTEM_PROMPT, state_context, self.history, player_input)
        return self._combat_llm_loop_inner(messages, depth=0)

    def _combat_llm_loop_inner(self, messages: list[dict], depth: int = 0) -> str:
        if depth > 3:
            return self._last_content or "Combat stalls — try your action again."

        log_llm_request(len(messages), self.model, depth)
        try:
            response = chat_completion(
                self.client,
                model=self.model,
                messages=messages,
                tools=[COMBAT_ACTION_TOOL],
                tool_choice="auto",
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
        except Exception as exc:
            return f"[Mechanics failed — API error: {exc}]"

        tool_calls = response.get("tool_calls", [])
        content = response.get("content", "")
        log_llm_response(content, tool_calls, response.get("finish_reason", ""))

        if not tool_calls:
            if content:
                return content
            return "It's your turn — declare an attack, cast a spell, or end your turn."

        messages.append({"role": "assistant", "content": content or None, "tool_calls": tool_calls})
        all_failed = True
        mechanical: list[dict] = []

        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                args = {}
            if fn_name != "combat_action":
                result = {"ok": False, "error": f"During combat only combat_action is available. Got: {fn_name}"}
            else:
                result = self._execute_combat_action(**args)
            log_tool_call(fn_name, args, result)
            self._last_tool_results[fn_name] = result
            if result.get("ok"):
                all_failed = False
                mechanical.extend(result.get("mechanical") or [])
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(result, default=str)})

        if all_failed:
            failures = "; ".join(
                f"{n}: {r.get('error', r)}"
                for n, r in self._last_tool_results.items()
                if not r.get("ok")
            )
            return f"[Mechanics failed — {failures}]\n\n{content or 'Your action did not resolve.'}"

        self.combat.last_mechanical = mechanical
        auto = self._combat_auto_chain()
        mechanical.extend(auto)
        death_narration = self._handle_player_death(mechanical)
        if death_narration:
            self._emit_narration(death_narration)
            self.history.append({"role": "assistant", "content": death_narration})
            return death_narration
        self._sync_combat_from_status()

        brief = self._combat_mechanical_brief(mechanical)
        narrate_messages = messages + [
            {"role": "user", "content": brief + "\n\nNarrate the combat results honestly. Do not call more tools."},
        ]
        try:
            final = chat_completion(
                self.client,
                model=self.model,
                messages=narrate_messages,
                tools=None,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            return final.get("content") or brief
        except Exception:
            return brief

    def _execute_combat_action(
        self,
        action: str,
        actor_id: str,
        target_id: str | None = None,
        weapon_id: str | None = None,
        spell_id: str | None = None,
    ) -> dict:
        status = self.bridge.status()
        if not status.get("combat"):
            return {"ok": False, "error": "no active combat"}
        turn_id = status["combat"].get("turn_id")
        if actor_id != turn_id:
            return {"ok": False, "error": f"not your turn: expected {turn_id}, got {actor_id}"}
        return self.bridge.combat_action(
            action=action,
            actor_id=actor_id,
            target_id=target_id,
            weapon_id=weapon_id,
            spell_id=spell_id,
        )

    def _handle_combat_trigger(self, beat_result: dict) -> None:
        for item in beat_result.get("mechanical_summary") or []:
            if item.get("action") == "combat_trigger":
                specs = item.get("monster_specs") or ["grave-ghoul:1"]
                if self._combat_active_in_db():
                    continue
                start = self.bridge.start_combat_from_trigger(specs)
                if start.get("ok"):
                    self.combat.active = True
                    self.combat.step = "COMBAT_PC_ACTION"
                    self.combat.order_narrated = False
                    self.bridge.run_combat_monster_turns()

    def _llm_loop(self, messages: list[dict[str, Any]], depth: int = 0, allow_tools: bool = True) -> str:
        """Call LLM, execute tool calls, loop until we get narration text."""
        if self.creation.active:
            log_error("llm_loop", "blocked exploration loop during active creation")
            return self._creation_turn("[SYSTEM: Finish character creation first.]")

        if depth == 0:
            self._last_tool_results = {}
        if depth > 4:
            log_error("llm_loop", f"depth limit reached ({depth}), last_content={bool(self._last_content)}")
            last_content = self._last_content
            if last_content:
                return last_content
            return "The dust settles. You stand at the crossroads, uncertain. What do you do?"

        log_llm_request(len(messages), self.model, depth)

        try:
            response = chat_completion(
                self.client,
                model=self.model,
                messages=messages,
                tools=TOOLS if (allow_tools and depth < 3) else None,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
        except Exception as exc:
            log_error("chat_completion", str(exc))
            if self._last_content:
                return self._last_content
            return f"The GM falters. (API error: {exc})"

        tool_calls = response.get("tool_calls", [])
        content = response.get("content", "")
        finish_reason = response.get("finish_reason", "")

        log_llm_response(content, tool_calls, finish_reason)

        self._last_content = content or self._last_content

        if not tool_calls:
            return content or self._last_content or "The GM regards you silently. Try again."

        messages.append({
            "role": "assistant",
            "content": content or None,
            "tool_calls": tool_calls,
        })

        all_failed = True
        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                args = {}

            result = self._execute_tool(fn_name, args)
            log_tool_call(fn_name, args, result)
            self._last_tool_results[fn_name] = result
            if result.get("ok", False):
                all_failed = False
                if not self.creation.active:
                    fact = tool_impact_fact(fn_name, args, result)
                    if fact:
                        self._remember_player_choice(fact, importance=3)
            else:
                messages.append({
                    "role": "system",
                    "content": (
                        f"TOOL FAILED ({fn_name}): {json.dumps(result, default=str)}. "
                        "You MUST narrate this failure honestly. Do NOT describe success."
                    ),
                })
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, default=str),
            })

        if all_failed and content:
            log_error("llm_loop", f"all tools failed at depth {depth}, returning content")
            failures = "; ".join(
                f"{name}: {res.get('error', res)}"
                for name, res in self._last_tool_results.items()
                if not res.get("ok")
            )
            return f"[Mechanics failed — {failures}]\n\n{content}"

        if all_failed and depth >= 2:
            log_error("llm_loop", f"all tools failed at depth {depth}, injecting no-tools directive")
            messages.append({
                "role": "user",
                "content": "[System: Tools are returning errors. Respond with narration text only — do not call more tools.]",
            })

        return self._llm_loop(messages, depth + 1, allow_tools=allow_tools)

    def _execute_tool(self, name: str, args: dict) -> dict:
        """Route a tool call to the appropriate bridge method."""
        try:
            if self.combat.active or self._combat_active_in_db():
                if name == "combat_action":
                    return self._execute_combat_action(**args)
                return {
                    "ok": False,
                    "error": f"During combat only combat_action is available. Got: {name}",
                }

            # During creation, ONLY set_creation_choice is allowed (interactive steps only)
            if self.creation.active:
                if name == "set_creation_choice":
                    return self._execute_creation_choice(
                        args.get("step", ""),
                        args.get("value", ""),
                        player_input=args.get("_player_input", ""),
                    )
                return {"ok": False, "error": f"During character creation, only set_creation_choice is available. Got: {name}"}

            if name == "roll_d20":
                return self.bridge.roll_d20(**args)
            elif name == "process_beat":
                result = self.bridge.process_beat(**args)
                self._handle_combat_trigger(result)
                return result
            elif name == "world_travel":
                return self.bridge.world_travel(**args)
            elif name == "world_where":
                return self.bridge.world_where()
            elif name == "world_exits":
                return self.bridge.world_exits()
            elif name == "site_enter":
                return self.bridge.site_enter(**args)
            elif name == "site_move":
                return self.bridge.site_move(**args)
            elif name == "start_combat":
                return self.bridge.start_combat(**args)
            elif name == "combat_attack":
                return self.bridge.combat_attack(**args)
            elif name == "combat_end":
                return self.bridge.combat_end()
            elif name == "get_status":
                return self.bridge.status()
            elif name == "memory_recall":
                return self.bridge.memory_recall(**args)
            elif name == "remember_fact":
                return self.bridge.remember_fact(**args)
            elif name == "cast_spell":
                return self.bridge.cast_spell(**args)
            elif name == "list_known_spells":
                return self.bridge.list_known_spells(**args)
            elif name == "fortune_spend":
                return self.bridge.fortune_spend(**args)
            elif name == "short_rest":
                return self.bridge.short_rest()
            elif name == "set_phase":
                return self.bridge.set_phase(**args)
            elif name == "clock_tick":
                return self.bridge.clock_tick(**args)
            elif name == "search_site":
                return self.bridge.search_site(**args)
            elif name == "wilderness_encounter":
                return self.bridge.wilderness_encounter()
            elif name == "advance_scene":
                return self.bridge.advance_scene(**args)
            elif name == "compass_exits":
                return self.bridge.compass_exits()
            elif name == "enter_dungeon":
                args = dict(args)
                if "site_id" in args and "site_address" not in args:
                    args["site_address"] = args.pop("site_id")
                return self.bridge.enter_dungeon(**args)
            elif name == "move_room":
                return self.bridge.move_room(**args)
            elif name == "exit_dungeon":
                return self.bridge.exit_dungeon()
            elif name == "interact_feature":
                return self.bridge.interact_feature(**args)
            elif name == "list_inventory":
                return self.bridge.list_inventory(**args)
            elif name == "equip_item":
                return self.bridge.equip_item(**args)
            elif name == "unequip_item":
                return self.bridge.unequip_item(**args)
            elif name == "grant_loot":
                return self.bridge.grant_loot(**args)
            elif name == "buy_item":
                return self.bridge.buy_item(**args)
            elif name == "sell_item":
                return self.bridge.sell_item(**args)
            elif name == "list_stash":
                return self.bridge.list_stash(**args)
            elif name == "list_vendor":
                return self.bridge.list_vendor(**args)
            else:
                return {"ok": False, "error": f"Unknown tool: {name}"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
