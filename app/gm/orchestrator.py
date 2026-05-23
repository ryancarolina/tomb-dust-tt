"""GM Orchestrator: turn loop connecting player input → LLM → tools → narration."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from gm.bridge import GameBridge
from gm.tool_args import normalize_tool_args, validate_tool_args
from gm.combat_fsm import (
    CombatState,
    format_initiative_table,
    get_combat_step_prompt,
    is_pc_turn,
)
from gm.creation import (
    CreationState,
    CREATION_STEPS,
    CREATION_STATUS_LABELS,
    format_creation_step_display,
    RACES,
    CLASS_INFO,
    format_skills_table,
    format_schools_table,
    format_spells_table,
    format_races_table,
    format_roll_stats_table,
    format_classes_table,
    format_equipment_summary,
    format_creation_status,
    format_exploration_status,
    _primary_roster_entry,
    strip_llm_status_tags,
    strip_llm_meta_narration,
    strip_flavor_race_table,
    strip_flavor_stats_table,
    strip_flavor_equipment_claims,
    race_display_title,
    sanitize_premature_completion_flavor,
    SKILL_DISPLAY,
    ensure_equipment_gold,
    is_equipment_confirm,
    is_equipment_objection,
    parse_player_race,
    parse_player_class,
    parse_player_skills,
    format_skill_parse_error,
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
from openai import APIStatusError, BadRequestError

from gm.openrouter import create_client, chat_completion
from gm.system_prompt import SYSTEM_PROMPT
from gm.tools import TOOLS, SET_CREATION_CHOICE_TOOL, COMBAT_PC_TOOLS
from gm.context import build_state_context, build_messages
from gm.logger import (
    log_player_input,
    log_gm_narration,
    log_creation_advanced,
    log_creation_drift,
    log_exploration_drift,
    log_creation_finalize,
    log_creation_step,
    parse_narration_status_line,
    log_tool_call,
    log_llm_request,
    log_llm_response,
    log_error,
    log_narration_verify_fail,
    log_narration_verify_pass,
    log_narration_verify_exhausted,
    log_llm_truncation_recovery,
    log_api_error,
    log_transcript_400_retry,
    summarize_messages_for_log,
    extract_tool_chain,
)
from gm.narration_verify import (
    TurnTruth,
    build_creation_turn_truth,
    build_encounter_turn_truth,
    build_exploration_turn_truth,
    format_turn_truth_for_prompt,
    verify_narration,
)

_PREMATURE_EXPLORE_PHASES = frozenset({"delve", "ingress", "extract", "aftermath"})
_PRE_DELVE_PHASES = frozenset({"pre_delve", "pre-delve"})
_PREMATURE_COMPLETION_COPY_RE = re.compile(
    r"registered\s+delver|you\s+are\s+now\s+a\s+registered",
    re.IGNORECASE,
)
_DEATH_MESSAGE_RE = re.compile(r"\*\*.+\*\* is dead\.", re.IGNORECASE)
_CREATION_FLAVOR_MAX_TOKENS = 500
NARRATION_LLM_MAX_ATTEMPTS = 6
NARRATION_VERIFY_MAX_RETRIES = 5
LENGTH_MAX_RECOVERY_RETRIES = 1
_NAME_LENGTH_STATIC_FALLBACK = "The clerk glances up from the ledger."

# APP-028: exploration _llm_loop all_failed strips pre-tool content for these tools.
_COMBAT_TOOL_NAMES = frozenset({
    "start_combat",
    "combat_attack",
    "combat_end",
    "cast_spell",
    "fortune_spend",
    "combat_action",
})

# APP-089 encounter FSM
_HOSTILE_INTENT_RE = re.compile(
    r"\b(attack|charge|strike|fight|engage|draw (?:my )?(?:weapon|sword|blade)|"
    r"swing at|stab|shoot at|lunge at)\b",
    re.I,
)
_CONTEST_KEYWORD_MAP: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(perception|listen|spot|notice|detect|search for|look for)\b", re.I), "pc_perceive"),
    (re.compile(r"\b(stealth|sneak|hide|slip past|avoid detection|move quietly)\b", re.I), "pc_sneak"),
    (re.compile(r"\b(ambush|surprise|wait in hiding|lurk)\b", re.I), "monster_ambush"),
]
_ENCOUNTER_ENTRY_HINT = (
    "Combat not started — threat present. Offer detect / sneak / fight. "
    "Do not call start_combat until engaged or ambush."
)
_ENCOUNTER_NOT_ENGAGED_HINT = (
    "Threat present — detect, sneak past, or declare hostile action before start_combat."
)
_ENCOUNTER_VERIFY_FALLBACK = (
    "Something stirs in the shadows — a threat you have not yet resolved. "
    "You could listen for movement, try to slip past, withdraw, or engage."
)
_EXPLORATION_ECONOMY_VERIFY_FALLBACK = (
    "The exchange stays unsettled — the Registry ledger shows no matching payment or outcome yet."
)

_SITE_ENTRY_REFUSAL_LINE = (
    "The entrance holds you at the threshold — the Registry ledger still shows you on the surface. "
    "Crossing requires a successful **enter_dungeon** or **site_enter** call; the delving clock does not start until then."
)


def _delve_entry_tool_hint(*, below_addresses: list[str] | None = None) -> str:
    core = (
        "Do not use set_phase to enter a site. Call compass_exits to list below addresses, "
        "then enter_dungeon(site_address). enter_dungeon advances preparation→ingress→delve automatically."
    )
    if below_addresses:
        addrs = ", ".join(below_addresses)
        return f"{core} Below from current cell: {addrs}."
    return core


def _should_delve_entry_hint(fn_name: str, args: dict, result: dict) -> bool:
    return (
        fn_name == "set_phase"
        and str(args.get("phase", "")).strip().lower() == "delve"
        and not result.get("ok")
    )


_SITE_ENTRY_LINE_MARKER_RES = (
    re.compile(r"step\s+(?:into|inside|through)", re.IGNORECASE),
    re.compile(r"cross(?:es|ed)?\s+the\s+threshold", re.IGNORECASE),
    re.compile(r"beyond\s+the\s+(?:arch|door|gate)", re.IGNORECASE),
    re.compile(
        r"you\s+(?:are|enter|stand)\s+(?:now\s+)?(?:in|inside)\s+(?:the\s+)?(?:crypt|dungeon|site|undercrypt|vault)",
        re.IGNORECASE,
    ),
    re.compile(r"\[Phase:\s*delve", re.IGNORECASE),
    re.compile(r"Phase:\s*delve", re.IGNORECASE),
    re.compile(r"mode:\s*dungeon", re.IGNORECASE),
    re.compile(r"\[Location:[^\]]*(?:UG-|undercrypt|crypt|dungeon)", re.IGNORECASE),
)

_SITE_ENTRY_PARAGRAPH_MARKER_RES = (
    re.compile(r"torchlit", re.IGNORECASE),
    re.compile(r"corridor", re.IGNORECASE),
    re.compile(r"vault\s+interior", re.IGNORECASE),
    re.compile(r"catacomb", re.IGNORECASE),
    re.compile(r"dungeon\s+(?:floor|hall)", re.IGNORECASE),
)


def sanitize_premature_site_entry_flavor(text: str, *, gate_active: bool) -> str:
    """Strip site-entry / interior fiction when surface gate is active (APP-024)."""
    if not gate_active or not (text or "").strip():
        return text or ""

    def _line_matches(chunk: str) -> bool:
        return any(pattern.search(chunk) for pattern in _SITE_ENTRY_LINE_MARKER_RES)

    def _paragraph_matches(chunk: str) -> bool:
        return any(pattern.search(chunk) for pattern in _SITE_ENTRY_PARAGRAPH_MARKER_RES)

    kept = [line for line in (text or "").splitlines() if not _line_matches(line)]
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()
    if result and _paragraph_matches(result):
        return ""
    return result


SPELL_QUERY_RE = re.compile(
    r"\b(what spells|spells do i know|my spells|known spells|spell list|do i know any spells)\b",
    re.I,
)


@dataclass(frozen=True)
class PlayerDeathResult:
    message: str
    already_emitted: bool = False


@dataclass(frozen=True)
class LengthRecoveryResult:
    action: Literal["discard", "retry", "fallback", "none"]
    next_prose: str
    attempt_budget_used: int = 0


def handle_finish_reason_length(
    finish_reason: str,
    prose: str,
    *,
    body_pending: bool,
    flavor_only: bool,
    length_retries_left: int,
) -> LengthRecoveryResult:
    """APP-079: discard truncated flavor when code body follows; retry NAME-only turns."""
    if finish_reason != "length":
        return LengthRecoveryResult(action="none", next_prose=prose)
    if body_pending:
        return LengthRecoveryResult(action="discard", next_prose="")
    if flavor_only and length_retries_left > 0:
        return LengthRecoveryResult(action="retry", next_prose=prose, attempt_budget_used=1)
    if flavor_only:
        return LengthRecoveryResult(
            action="fallback",
            next_prose=_NAME_LENGTH_STATIC_FALLBACK,
        )
    return LengthRecoveryResult(action="none", next_prose=prose)


def _is_valid_tool_call(tc: Any) -> bool:
    """Structural tool_call validity (APP-031); not APP-080 arg semantics."""
    if not isinstance(tc, dict):
        return False
    tc_id = tc.get("id")
    if not isinstance(tc_id, str) or not tc_id.strip():
        return False
    fn = tc.get("function")
    if not isinstance(fn, dict):
        return False
    name = fn.get("name")
    if not isinstance(name, str) or not name.strip():
        return False
    if "arguments" not in fn:
        return False
    if not isinstance(fn.get("arguments"), str):
        return False
    return True


def _normalize_assistant_message(msg: dict[str, Any]) -> dict[str, Any] | None:
    """Pass 1: strip invalid tool_calls; drop empty assistant shells."""
    copy = {**msg}
    raw_calls = copy.get("tool_calls")
    if raw_calls is not None:
        if not isinstance(raw_calls, list):
            raw_calls = []
        valid = [tc for tc in raw_calls if _is_valid_tool_call(tc)]
        if valid:
            copy["tool_calls"] = [{**tc} for tc in valid]
            return copy
        copy.pop("tool_calls", None)
    if copy.get("content") is None:
        return None
    return copy


def _safe_prefix_fallback(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """When sanitize would return empty, keep leading system + last user (APP-031)."""
    if not messages:
        return []
    prefix: list[dict[str, Any]] = []
    for msg in messages:
        if msg.get("role") != "system":
            break
        prefix.append({**msg})
    last_user: dict[str, Any] | None = None
    for msg in messages:
        if msg.get("role") == "user":
            last_user = msg
    if last_user is not None:
        prefix.append({**last_user})
    return prefix


def sanitize_transcript_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Repair in-turn tool transcript before chat_completion (APP-031)."""
    if not messages:
        return []

    normalized: list[dict[str, Any]] = []
    for msg in messages:
        role = msg.get("role")
        if role == "assistant":
            norm = _normalize_assistant_message({**msg})
            if norm is not None:
                normalized.append(norm)
        else:
            normalized.append({**msg})

    output: list[dict[str, Any]] = []
    i = 0
    n = len(normalized)
    while i < n:
        msg = normalized[i]
        role = msg.get("role")

        if role == "tool":
            i += 1
            continue

        if role == "assistant":
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                expected_ids = {tc["id"] for tc in tool_calls}
                seg_start = i + 1
                seg_end = seg_start
                while seg_end < n:
                    next_msg = normalized[seg_end]
                    if next_msg.get("role") == "assistant":
                        next_calls = next_msg.get("tool_calls")
                        if next_calls:
                            break
                    seg_end += 1

                tools: list[dict[str, Any]] = []
                deferred: list[dict[str, Any]] = []
                for seg_msg in normalized[seg_start:seg_end]:
                    if seg_msg.get("role") == "tool":
                        tool_id = seg_msg.get("tool_call_id")
                        if tool_id in expected_ids:
                            tools.append({**seg_msg})
                    else:
                        deferred.append({**seg_msg})

                output.append({**msg})
                output.extend(tools)
                output.extend(deferred)
                i = seg_end
                continue

            output.append({**msg})
            i += 1
            continue

        output.append({**msg})
        i += 1

    if not output and messages:
        return _safe_prefix_fallback(messages)
    return output


_MALFORMED_TRANSCRIPT_MARKERS = (
    "tool-call assistant message produced no valid function calls",
    "no valid function calls but is followed by tool",
)


def is_malformed_transcript_400(exc: BaseException) -> bool:
    """Narrow 400 classifier for transcript tool-order rejections (APP-032)."""
    try:
        if not isinstance(exc, (BadRequestError, APIStatusError)):
            return False
        if getattr(exc, "status_code", None) != 400:
            return False
        msg = str(exc).casefold()
        if any(m in msg for m in _MALFORMED_TRANSCRIPT_MARKERS):
            return True
        if "tool result messages" in msg and (
            "tool_call" in msg or "tool_calls" in msg
        ):
            return True
        return False
    except Exception:
        return False


def _resolve_combatant_id_for_gate(combatants: list[dict], ref: str) -> str | None:
    ref_lower = ref.lower().strip()
    for c in combatants:
        cid = str(c.get("id", ""))
        if cid == ref or cid.lower() == ref_lower:
            return cid
        display = str(c.get("displayName", "")).lower()
        if display == ref_lower or ref_lower in display:
            return cid
    return None


class Orchestrator:
    """Manages the GM turn loop."""

    def __init__(self, config: dict):
        self.config = config
        llm_cfg = config.get("llm", {})
        self.model = llm_cfg.get("model", "anthropic/claude-sonnet-4")
        self.max_tokens = llm_cfg.get("max_tokens", 1024)
        self.temperature = llm_cfg.get("temperature", 0.8)
        self._creation_flavor_max_tokens = int(
            llm_cfg.get("creation_flavor_max_tokens", _CREATION_FLAVOR_MAX_TOKENS)
        )

        self.client = create_client()
        self.bridge = GameBridge()
        self.history: list[dict[str, str]] = []
        self._last_content = ""
        self._last_finish_reason = ""
        self._last_tool_results: dict = {}
        narr_cfg = config.get("narration", {})
        self._narration_llm_max_attempts = int(
            narr_cfg.get("llm_max_attempts", NARRATION_LLM_MAX_ATTEMPTS)
        )
        self._narration_verify_max_retries = int(
            narr_cfg.get("verify_max_retries", NARRATION_VERIFY_MAX_RETRIES)
        )
        self._length_max_recovery_retries = int(
            narr_cfg.get("length_max_recovery_retries", LENGTH_MAX_RECOVERY_RETRIES)
        )
        self._beat_combat_start_failure: str | None = None
        self._entry_committed_this_turn = False
        self._delve_entry_hint_this_turn: str | None = None
        self._exploration_pre_turn_mode = "surface"
        self.creation = CreationState()
        self.combat = CombatState()
        self._creation_disk_restore_done = False
        # APP-089 encounter FSM
        self._encounter_by_room: dict[str, dict[str, Any]] = {}
        self._tools_ok_this_turn: list[str] = []
        self._current_encounter_key: str | None = None
        self._pending_contest_type: str | None = None
        self._current_player_input: str = ""

    def get_status(self) -> dict:
        return self.bridge.status()

    def is_map_travel_blocked(self) -> bool:
        status = self.bridge.status()
        roster = status.get("roster") or []
        if self.creation.active:
            return True
        if status.get("awaiting") == "CHARACTER_CREATION" and not roster:
            return True
        return False

    def get_creation_step_badge(self) -> dict[str, str] | None:
        if not self.creation.active:
            return None
        step = self.creation.step
        return {"step": step, "display_label": format_creation_step_display(step)}

    def get_player_suggestions(self) -> list[str]:
        from ui.suggestions import build_player_suggestions

        has_save = self.bridge.has_save()
        try:
            awaiting = self.bridge.status().get("awaiting") or ""
        except Exception:
            awaiting = ""

        return build_player_suggestions(
            creation_step=self.creation.step,
            creation_active=self.creation.active,
            engine_awaiting=awaiting,
            has_save=has_save,
        )

    def _restore_history(self):
        """Load orchestrator history and combat state from session_state.json."""
        save_path = self._session_state_path()
        if not save_path.exists():
            return
        try:
            data = json.loads(save_path.read_text(encoding="utf-8"))
            if not self.history:
                saved = data.get("orchestrator_history", [])
                if saved:
                    self.history = saved[-20:]
            combat_data = data.get("combat_state")
            if combat_data and combat_data.get("active"):
                self.combat = CombatState.from_dict(combat_data)
            encounter_data = data.get("encounter_state")
            if encounter_data:
                self.import_encounter_state(encounter_data)
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
            try:
                st = self.bridge.status()
                key = self._encounter_room_key(st)
                if key and self._encounter_by_room.get(key, {}).get("phase") == "in_combat":
                    self._encounter_by_room.pop(key, None)
            except Exception:
                pass

    def export_combat_state(self) -> dict | None:
        if not self.combat.active:
            return None
        return self.combat.to_dict()

    def import_combat_state(self, data: dict | None) -> None:
        if data and data.get("active"):
            self.combat = CombatState.from_dict(data)

    def export_encounter_state(self) -> dict[str, dict[str, Any]]:
        return dict(self._encounter_by_room)

    def import_encounter_state(self, data: dict[str, dict[str, Any]] | None) -> None:
        self._encounter_by_room = dict(data) if data else {}

    def _encounter_room_key(self, status: dict) -> str | None:
        party = status.get("party") or {}
        if party.get("mode") != "dungeon":
            return None
        site_id = party.get("site_id")
        room_id = party.get("dungeon_room_id")
        if not site_id or not room_id:
            return None
        return f"{site_id}:{room_id}"

    def _enemy_threats_from_features(self, features: list) -> list[dict[str, Any]]:
        threats: list[dict[str, Any]] = []
        for feature in features:
            if not isinstance(feature, dict):
                continue
            if str(feature.get("feature_type") or "").lower() != "enemy":
                continue
            raw = feature.get("data_json")
            data: dict[str, Any] = raw if isinstance(raw, dict) else {}
            if isinstance(raw, str) and raw.strip():
                try:
                    parsed = json.loads(raw)
                    data = parsed if isinstance(parsed, dict) else {}
                except json.JSONDecodeError:
                    data = {}
            monster_id = str(data.get("monsterId") or data.get("monster_id") or "").strip()
            if not monster_id:
                continue
            threats.append({
                "monster_id": monster_id,
                "count": int(data.get("count") or 1),
                "feature_id": feature.get("id"),
            })
        return threats

    def _room_features_from_status(self, status: dict) -> list:
        dungeon = status.get("dungeon") or {}
        return list(dungeon.get("features") or status.get("features") or [])

    def _get_encounter_state(self, status: dict) -> dict[str, Any]:
        key = self._encounter_room_key(status)
        if not key:
            return {}
        if key not in self._encounter_by_room:
            self._encounter_by_room[key] = {"phase": "", "threats": []}
        self._current_encounter_key = key
        return self._encounter_by_room[key]

    def _current_encounter_phase(self, status: dict) -> str:
        return str(self._get_encounter_state(status).get("phase") or "")

    def _set_encounter_phase(self, status: dict, phase: str) -> None:
        key = self._encounter_room_key(status)
        if not key:
            return
        blob = self._get_encounter_state(status)
        blob["phase"] = phase
        self._encounter_by_room[key] = blob

    def _init_encounter_state_detected(self, status: dict, features: list) -> None:
        key = self._encounter_room_key(status)
        if not key:
            return
        threats = self._enemy_threats_from_features(features)
        if not threats:
            return
        self._encounter_by_room[key] = {"phase": "detected", "threats": threats}
        self._current_encounter_key = key

    def _pc_character_ids(self, status: dict) -> list[str]:
        ids: list[str] = []
        for entry in status.get("roster") or status.get("characters") or []:
            cid = entry.get("character_id") or entry.get("id")
            if cid:
                ids.append(str(cid))
        return ids

    def _surprised_combatant_ids_if_ambush(self, status: dict) -> list[str] | None:
        blob = self._get_encounter_state(status)
        if blob.get("phase") != "ambush":
            return None
        if "surprised_combatant_ids" in blob:
            return list(blob["surprised_combatant_ids"])
        pc_ids = self._pc_character_ids(status)
        return pc_ids or None

    def _disambiguate_contest_type(
        self,
        contest_type: str,
        phase: str,
        features: list,
    ) -> str:
        has_enemy = bool(self._enemy_threats_from_features(features))
        if contest_type == "pc_sneak":
            if phase == "unnoticed" and not has_enemy:
                return "monster_ambush"
        if contest_type == "pc_perceive" and phase == "unnoticed":
            return "pc_perceive"
        return contest_type

    def _infer_contest_type(
        self,
        reason: str,
        player_input: str,
        phase: str,
        features: list,
    ) -> str | None:
        if self._pending_contest_type:
            return self._disambiguate_contest_type(self._pending_contest_type, phase, features)

        matched: str | None = None
        for pattern, contest_type in _CONTEST_KEYWORD_MAP:
            if pattern.search(reason or ""):
                matched = contest_type
                break
        if matched is None:
            for pattern, contest_type in _CONTEST_KEYWORD_MAP:
                if pattern.search(player_input or ""):
                    matched = contest_type
                    break
        if matched is None:
            return None
        return self._disambiguate_contest_type(matched, phase, features)

    def _resolve_encounter_contest(self, roll_result: dict, contest_type: str) -> None:
        status = self.bridge.status()
        key = self._encounter_room_key(status)
        if not key:
            return
        blob = self._get_encounter_state(status)
        phase = str(blob.get("phase") or "")
        success = bool(
            roll_result.get("ok")
            and roll_result.get(
                "success",
                roll_result.get("total", 0) >= roll_result.get("dc", 99),
            )
        )

        if contest_type == "pc_perceive":
            if success and phase == "unnoticed":
                blob["phase"] = "detected"
        elif contest_type == "pc_sneak":
            if not success:
                blob["phase"] = "engaged"
        elif contest_type == "monster_ambush":
            if not success:
                blob["phase"] = "ambush"
                blob["surprised_combatant_ids"] = self._pc_character_ids(status)

        blob["last_contest"] = {
            "contest_type": contest_type,
            "success": success,
            "roll_ref": {
                k: roll_result.get(k)
                for k in ("total", "dc", "skill", "reason", "natural")
            },
        }
        blob["last_roll"] = blob["last_contest"]["roll_ref"]
        self._encounter_by_room[key] = blob

    def _advance_encounter_phase(self, player_input: str) -> None:
        try:
            status = self.bridge.status()
        except Exception:
            return
        if status.get("combat") or self.combat.active:
            return
        key = self._encounter_room_key(status)
        if not key:
            return
        blob = self._get_encounter_state(status)
        phase = str(blob.get("phase") or "")

        if phase in ("detected", "unnoticed") and _HOSTILE_INTENT_RE.search(player_input):
            blob["phase"] = "engaged"
            self._encounter_by_room[key] = blob
            return

        for pattern, contest_type in _CONTEST_KEYWORD_MAP:
            if pattern.search(player_input):
                self._pending_contest_type = contest_type
                break

    def _handle_beat_encounter_rows(self, beat_result: dict) -> dict:
        summary = list(beat_result.get("mechanical_summary") or [])
        if not summary:
            return beat_result

        status = self.bridge.status()
        phase = self._current_encounter_phase(status)
        new_summary: list[dict[str, Any]] = []

        for item in summary:
            if item.get("action") == "hostile" and item.get("ok"):
                if phase in ("detected", "unnoticed"):
                    self._set_encounter_phase(status, "engaged")
                    phase = "engaged"
                    continue
                if phase in ("engaged", "ambush"):
                    new_summary.append({
                        "ok": True,
                        "action": "combat_trigger",
                        "monster_specs": item.get("monster_specs") or ["grave-ghoul:1"],
                        "include_party": True,
                        "slot": item.get("slot"),
                    })
                    continue
            new_summary.append(item)

        return {**beat_result, "mechanical_summary": new_summary}

    def _scan_beat_roll_contests(self, beat_result: dict) -> None:
        status = self.bridge.status()
        if not self._encounter_room_key(status):
            return
        for item in beat_result.get("mechanical_summary") or []:
            if not item.get("ok"):
                continue
            action = item.get("action") or ""
            if action not in ("roll_d20", "roll"):
                continue
            contest_type = item.get("contest_type")
            if not contest_type:
                features = self._room_features_from_status(status)
                phase = self._current_encounter_phase(status)
                reason = str(item.get("reason") or item.get("skill") or "")
                contest_type = self._infer_contest_type(
                    reason,
                    self._current_player_input,
                    phase,
                    features,
                )
            if contest_type:
                self._resolve_encounter_contest(item, contest_type)

    def _combat_active_in_db(self) -> bool:
        try:
            return bool(self.bridge.status().get("combat"))
        except Exception:
            return False

    def _gate_pc_attack(self, attacker_id: str) -> dict | None:
        """Return error dict if PC attack context invalid; None if caller may dispatch."""
        status = self.bridge.status()
        combat = status.get("combat")
        if not combat:
            return {"ok": False, "error": "no active combat for session"}

        combatants = combat.get("combatants") or []
        initiative = combat.get("initiative") or []
        resolved = _resolve_combatant_id_for_gate(combatants, attacker_id) or attacker_id

        initiative_ids = {str(row.get("id", "")) for row in initiative}
        if resolved not in initiative_ids:
            return {"ok": False, "error": f"attacker not in combat: {attacker_id}"}

        return None

    def _sync_creation_from_status(self) -> None:
        """Ensure we do not stay in creation mode when a roster already exists."""
        restore = getattr(self, "_restore_creation_from_session_state", None)
        if callable(restore):
            restore()
        self._force_creation_active_if_reconcile_needed()
        try:
            status = self.bridge.status()
        except Exception:
            return
        if status.get("roster"):
            self.creation.active = False
            self.creation.step = "WORLD_INTRO"
        elif (
            self._effective_awaiting_for_reconcile(status) == "CHARACTER_CREATION"
            and not status.get("roster")
        ):
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

    def _expected_creation_awaiting_label(self) -> str:
        """Granular awaiting label for creation.step (matches format_creation_status)."""
        step = self.creation.step
        label = CREATION_STATUS_LABELS.get(step, f"{step}_INPUT")
        return str(label).strip().upper()

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
        try:
            status = self.bridge.status()
        except Exception:
            status = {}
        roster = status.get("roster") or []
        roster_len = len(roster)
        party = status.get("party") or {}
        engine_phase = str(party.get("phase") or "").strip().lower()
        narrated_phase = str(narrated.get("phase") or "").strip().lower()
        narrated_awaiting = str(narrated.get("awaiting") or "").strip().upper()

        reasons: list[str] = []
        expected_awaiting: str | None = None
        if roster_len == 0 and _PREMATURE_COMPLETION_COPY_RE.search(narration):
            reasons.append("premature_completion_copy")

        if not narrated.get("phase") and not narrated.get("awaiting"):
            if not reasons:
                return
        else:
            if self.creation.active and narrated_awaiting:
                expected_awaiting = self._expected_creation_awaiting_label()
                if narrated_awaiting != expected_awaiting:
                    reasons.append("awaiting_mismatch")
            if narrated_phase and engine_phase and narrated_phase != engine_phase:
                reasons.append("phase_mismatch")
            if self.creation.active and narrated_phase in _PREMATURE_EXPLORE_PHASES:
                reasons.append("premature_exploration_phase")
            if roster_len == 0:
                if narrated_phase in _PRE_DELVE_PHASES:
                    reasons.append("premature_exploration_phase")
                if self.creation.active and narrated_awaiting == "RECEPTION_CHOICE":
                    reasons.append("premature_exploration_phase")
                if (
                    self.creation.active
                    and narrated_phase == "preparation"
                    and self.creation.step != "WORLD_INTRO"
                ):
                    reasons.append("premature_exploration_phase")

        if not reasons:
            return

        payload: dict[str, Any] = {
            "step": self.creation.step,
            "roster_len": len(roster),
            "awaiting": status.get("awaiting"),
            "creation.active": self.creation.active,
            "narrated_phase": narrated.get("phase"),
            "narrated_awaiting": narrated.get("awaiting"),
            "engine_phase": party.get("phase"),
            "reasons": reasons,
        }
        if expected_awaiting is not None:
            payload["expected_awaiting"] = expected_awaiting
        log_creation_drift(payload)

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

    def _exploration_gate_active(self, pre_turn_mode: str) -> bool:
        if self._entry_committed_this_turn:
            return False
        if pre_turn_mode in ("dungeon", "site"):
            return False
        return pre_turn_mode == "surface"

    def _encounter_verify_active(self, status: dict) -> bool:
        """True when encounter TurnTruth verify should run on exploration publish (APP-089 D2)."""
        if status.get("combat"):
            return False
        if self._current_encounter_phase(status):
            return True
        features = self._room_features_from_status(status)
        return any(str(f.get("feature_type") or "").lower() == "enemy" for f in features)

    def _exploration_economy_verify_active(self, status: dict) -> bool:
        """True when economy/social TurnTruth verify should run (APP-107; not with encounter verify)."""
        if status.get("combat"):
            return False
        if self._encounter_verify_active(status):
            return False
        if self._all_tools_failed_this_turn():
            return False
        return True

    def _all_tools_failed_this_turn(self) -> bool:
        results = self._last_tool_results
        if not results:
            return False
        return all(not r.get("ok") for r in results.values())

    def _social_state_for_truth(self) -> dict[str, Any]:
        try:
            result = self.bridge.social_encounter_status()
            return result if isinstance(result, dict) else {}
        except Exception:
            return {}

    def _compose_exploration_narration(self, prose: str, *, gate_active: bool) -> str:
        """Exploration post-process: APP-024 site-entry strip, then APP-077 footer/tags."""
        text = sanitize_premature_site_entry_flavor(prose or "", gate_active=gate_active)
        if gate_active and not text.strip():
            text = _SITE_ENTRY_REFUSAL_LINE
        self._log_exploration_drift_if_needed(text)
        text = strip_llm_status_tags(text)
        text = strip_llm_meta_narration(text)
        footer = format_exploration_status(self.bridge.status())
        parts: list[str] = []
        if text.strip():
            parts.append(text.strip())
        parts.append(footer)
        return "\n\n".join(parts)

    def _log_exploration_drift_if_needed(self, prose: str) -> None:
        """Telemetry when LLM prose bracket fields disagree with engine (never blocks emit)."""
        if not (prose or "").strip():
            return
        narrated = parse_narration_status_line(prose)
        gp_m = re.search(r"GP:\s*([^|\]]+)", prose, re.I)
        narrated_gp = gp_m.group(1).strip() if gp_m else None
        try:
            status = self.bridge.status()
        except Exception:
            return
        party = status.get("party") or {}
        engine_phase = str(party.get("phase") or "").strip().lower()
        engine_awaiting = str(status.get("awaiting") or "").strip().upper()
        primary = _primary_roster_entry(status)
        engine_gold = primary.get("gold", 0) if primary else 0
        transit = int(party.get("gold_in_transit") or 0)
        engine_gp = str(engine_gold)
        if transit > 0:
            engine_gp = f"{engine_gold} (+{transit} transit)"
        reasons: list[str] = []
        narrated_phase = str(narrated.get("phase") or "").strip().lower()
        narrated_awaiting = str(narrated.get("awaiting") or "").strip().upper()
        if narrated_phase and engine_phase and narrated_phase != engine_phase:
            reasons.append("phase_mismatch")
        if narrated_awaiting and engine_awaiting and narrated_awaiting != engine_awaiting:
            reasons.append("awaiting_mismatch")
        if narrated_gp and narrated_gp != engine_gp:
            reasons.append("gp_mismatch")
        if not reasons:
            return
        log_exploration_drift({
            "narrated_phase": narrated.get("phase"),
            "narrated_awaiting": narrated.get("awaiting"),
            "narrated_gp": narrated_gp,
            "engine_phase": party.get("phase"),
            "engine_awaiting": status.get("awaiting"),
            "engine_gp": engine_gp,
            "reasons": reasons,
        })

    def _is_code_only_combat_narration(self, text: str) -> bool:
        if not (text or "").strip():
            return False
        if _DEATH_MESSAGE_RE.search(text):
            return True
        stripped = text.strip()
        if stripped.startswith("[Mechanics failed —"):
            parts = stripped.split("\n\n", 1)
            if len(parts) == 1:
                return True
            return not parts[1].strip()
        return False

    def _emit_exploration_narration(self, narration: str, *, gate_active: bool = False) -> None:
        if not self._is_code_only_combat_narration(narration):
            narration = self._compose_exploration_narration(narration, gate_active=gate_active)
        self._emit_narration(narration)

    def _build_delve_entry_hint(self) -> str:
        below: list[str] = []
        try:
            compass = self.bridge.compass_exits()
            if compass.get("ok"):
                for item in (compass.get("exits") or {}).get("below") or []:
                    addr = (item.get("address") or "").strip()
                    if addr:
                        below.append(addr)
        except Exception:
            pass
        return _delve_entry_tool_hint(below_addresses=below or None)

    def _emit_recovery_narration(self, message: str) -> None:
        """Log recovery copy without creation drift checks (resume failure paths)."""
        log_gm_narration(message)

    def _map_setup_new_game_cause(self, error: str) -> str:
        err = str(error).lower()
        if "campaign not found" in err:
            return "The save campaign could not be found in the workspace database."
        if "slug must be" in err:
            return "The campaign name failed validation — this is an internal setup error."
        if "campaign already exists" in err:
            return "A leftover campaign record blocked startup (unexpected after wipe)."
        if "active session already exists" in err or "campaign already has an open session" in err:
            return (
                "A stale open session blocked startup (regression — report if seen after APP-014)."
            )
        if any(
            token in err
            for token in ("permission denied", "database is locked", "disk i/o")
        ):
            return "The workspace database could not be written (permissions or file lock)."
        return "Something went wrong while resetting the workspace for a new run."

    def _setup_new_game_failure_message(
        self,
        result: dict,
        *,
        context: Literal["command", "death", "run_ended"],
        name: str | None = None,
        where: str | None = None,
    ) -> str:
        cause_line = self._map_setup_new_game_cause(result.get("error") or "")
        failure_tail = (
            "This run is over, but the registry could not open a fresh desk session.\n\n"
            f"{cause_line}\n\n"
            "Type **new game** to try again.\n\n"
            "[Awaiting: new game]"
        )
        if context == "command":
            return (
                "Could not start a fresh session.\n\n"
                f"{cause_line}\n\n"
                "Type **new game** to try again. If this keeps happening, quit and relaunch the app.\n\n"
                "[Awaiting: new game]"
            )
        if context == "death":
            display_name = name or "The delver"
            location = where or "the site"
            lead = (
                f"**{display_name}** is dead. The body remains in **{location}** — gear still on the "
                "corpse for anyone who finds it."
            )
            return f"{lead}\n\n{failure_tail}"
        location = where or "the delve"
        lead = (
            f"Your previous delver did not survive (0 HP after the last fight). "
            f"The body remains in **{location}** with all carried gear."
        )
        return f"{lead}\n\n{failure_tail}"

    def _session_state_path(self) -> Path:
        return Path(__file__).resolve().parents[1] / "session_state.json"

    def _read_saved_engine_status(self) -> dict | None:
        save_path = self._session_state_path()
        if not save_path.exists():
            return None
        try:
            data = json.loads(save_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        engine_status = data.get("engine_status")
        if isinstance(engine_status, dict):
            return engine_status
        return None

    def _effective_awaiting_for_reconcile(self, live_status: dict) -> str:
        live_awaiting = live_status.get("awaiting") or ""
        if live_awaiting and live_awaiting != "SETUP":
            return live_awaiting
        saved = self._read_saved_engine_status()
        if saved:
            return saved.get("awaiting") or live_awaiting
        return live_awaiting

    def _force_creation_active_if_reconcile_needed(self) -> None:
        if self.creation.active:
            return
        try:
            live = self.bridge.status()
        except Exception:
            return
        roster = live.get("roster") or []
        if roster:
            return
        live_awaiting = live.get("awaiting") or ""
        if live_awaiting == "ROSTER_SETUP":
            return
        effective = self._effective_awaiting_for_reconcile(live)
        if effective != "CHARACTER_CREATION":
            return
        self.creation.active = True

    def _creation_restore_gate(self, data: dict, live_status: dict) -> bool:
        """G1: restore creation from disk only when snapshot + live rules pass."""
        if live_status.get("roster"):
            return False

        if "engine_status" in data:
            engine = data.get("engine_status") or {}
            saved_awaiting = engine.get("awaiting")
            if saved_awaiting is not None:
                if saved_awaiting != "CHARACTER_CREATION":
                    return False
            elif live_status.get("awaiting") != "CHARACTER_CREATION":
                return False
            if "roster" in engine and engine.get("roster") != []:
                return False
        elif live_status.get("awaiting") != "CHARACTER_CREATION":
            return False

        creation_state = data.get("creation_state") or {}
        if not creation_state.get("active"):
            return False
        step = creation_state.get("step")
        if not step or step not in CREATION_STEPS:
            return False
        return True

    def _restore_creation_from_session_state(self) -> bool:
        """Import creation FSM from session_state.json once per relaunch (G1 + once-only guard)."""
        if self._creation_disk_restore_done:
            return False
        save_path = self._session_state_path()
        if not save_path.exists():
            return False
        try:
            data = json.loads(save_path.read_text(encoding="utf-8"))
        except Exception:
            return False
        try:
            live = self.bridge.status()
        except Exception:
            live = {}
        if not self._creation_restore_gate(data, live):
            return False
        self.import_creation_state(data.get("creation_state"))
        if not self.creation.active:
            return False
        self._creation_disk_restore_done = True
        return True

    def _reset_creation_for_new_game(self) -> None:
        self._creation_disk_restore_done = False
        self.creation = CreationState(active=True, step="NAME")

    def _clear_creation_block_on_disk(self) -> None:
        save_path = self._session_state_path()
        if not save_path.exists():
            return
        try:
            data = json.loads(save_path.read_text(encoding="utf-8"))
            data["creation_state"] = self.export_creation_state()
            data.pop("engine_status", None)
            save_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _is_mid_creation_resume_failure(self) -> bool:
        if self.creation.active:
            return True
        try:
            status = self.bridge.status()
            if (
                status.get("awaiting") == "CHARACTER_CREATION"
                and not (status.get("roster") or [])
            ):
                return True
        except Exception:
            pass

        save_path = self._session_state_path()
        if not save_path.exists():
            return False
        try:
            data = json.loads(save_path.read_text(encoding="utf-8"))
            creation_data = data.get("creation_state") or {}
            if creation_data.get("active"):
                return True
            step = creation_data.get("step")
            if step and step != "NAME":
                return True
        except Exception:
            pass
        return False

    def _resume_failure_message(self, result: dict) -> str:
        error = str(result.get("error") or "unknown").strip()
        if error not in ("no save session found", "unknown"):
            error = "no save session found"

        if self._is_mid_creation_resume_failure():
            step = self.creation.step or "NAME"
            step_phrase = step.lower().replace("_", " ")
            lines = [
                "There is no **finished save** to load yet — the registry needs a living "
                "slotted delver before **load game** can restore a run.",
                f"You still have an unsaved character in progress at the **{step_phrase}** step. "
                "Keep answering the clerk's prompts to continue this desk, or type **new game** "
                "to wipe this in-progress creation and start over (that clears your current progress).",
            ]
            footer = format_creation_status(self.creation)
            return "\n\n".join(lines) + f"\n\n[{footer}]"

        lines = [
            "No saved game was found on this workspace. Type **new game** to start fresh.",
            "The app's autosave does not replace an engine roster save — you need a living "
            "delver in the registry save before **load game** can restore a run.",
        ]
        return "\n\n".join(lines) + "\n\n[Awaiting: new game]"

    def setup_new_game(self, campaign_slug: str = "salt-road") -> dict:
        """End prior session before wipe; start completely fresh. World corpses persist."""
        self._reset_creation_for_new_game()
        self._clear_creation_block_on_disk()
        end_result = self.bridge.end_session()
        if not end_result.get("ok"):
            self.bridge.force_close_all_sessions()
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

    def _handle_player_death(self, mechanical: list[dict]) -> PlayerDeathResult | None:
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
        corpse = corpse_result.get("corpse") or {}
        name = corpse.get("display_name", "The delver")
        site = corpse.get("site_address") or corpse.get("cell_address") or "the site"
        room = corpse.get("room_id")
        where = f"{site} / {room}" if room else str(site)
        setup_result = self.setup_new_game(campaign_slug)
        if not setup_result.get("ok"):
            log_error("setup_new_game", setup_result.get("error", "unknown"))
            message = self._setup_new_game_failure_message(
                setup_result, context="death", name=name, where=where
            )
            self._emit_recovery_narration(message)
            return PlayerDeathResult(message, already_emitted=True)
        success_message = (
            f"**{name}** is dead. The body remains in **{where}** — gear still on the corpse for anyone who finds it.\n\n"
            "This run is over. A **new game** has started. Welcome to the Registry, delver. What is your name?"
        )
        return PlayerDeathResult(success_message, already_emitted=False)

    def _delete_save_file(self):
        """Remove the UI session state file."""
        save_path = self._session_state_path()
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
                status_stub = {
                    "party": {
                        "mode": ps["mode"],
                        "site_id": ps["site_id"],
                        "dungeon_room_id": ps["dungeon_room_id"],
                    }
                }
                phase = self._current_encounter_phase(status_stub)
                features = (room_info or {}).get("features") or []
                has_enemy = any(
                    str(f.get("feature_type") or "").lower() == "enemy" for f in features
                )
                if phase or has_enemy:
                    phase_label = phase or "unknown"
                    result["encounter_context"] = (
                        f"Encounter: combat NOT active. Phase: {phase_label}. "
                        "Threats present — player may detect, sneak, or engage."
                    )
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
                message = self._setup_new_game_failure_message(result, context="command")
                self._emit_recovery_narration(message)
                return message
            return self._creation_turn("[SYSTEM: New game started. Begin character creation.]")

        if lower not in ("new game", "start", "new"):
            self._restore_creation_from_session_state()

        if lower in ("continue", "resume", "load", "load game"):
            result = self.bridge.session_resume()
            if not result.get("ok"):
                log_error("session_resume", result.get("error", "unknown"))
                self._restore_creation_from_session_state()
                message = self._resume_failure_message(result)
                self._emit_recovery_narration(message)
                return message
            if result.get("run_ended"):
                campaign_slug = result.get("campaign_slug", "salt-road")
                corpses = result.get("corpses") or []
                where = "the delve"
                if corpses:
                    c0 = corpses[0] or {}
                    site = c0.get("site_address") or c0.get("cell_address") or where
                    room = c0.get("room_id")
                    where = f"{site} / {room}" if room else str(site)
                setup_result = self.setup_new_game(campaign_slug)
                if not setup_result.get("ok"):
                    log_error("setup_new_game", setup_result.get("error", "unknown"))
                    message = self._setup_new_game_failure_message(
                        setup_result, context="run_ended", where=where
                    )
                    self._emit_recovery_narration(message)
                    return message
                death_msg = (
                    f"Your previous delver did not survive (0 HP after the last fight). "
                    f"The body remains in **{where}** with all carried gear.\n\n"
                    "This run is over. A **new game** has started. What is your delver's name?"
                )
                self._emit_narration(death_msg)
                return death_msg
            self._restore_history()
            self._restore_creation_from_session_state()
            self._sync_creation_from_status()
            self._sync_combat_from_status()
            status = self.bridge.status()
            if result.get("recovered_campaign"):
                log_error("session_resume", f"recovered save campaign: {result.get('campaign_slug')}")
            if status.get("awaiting") == "CHARACTER_CREATION" and not status.get("roster"):
                if not self.creation.active:
                    self._force_creation_active_if_reconcile_needed()
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

        self._current_player_input = player_input
        self._advance_encounter_phase(player_input)

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
        if exploration and exploration.get("encounter_context"):
            state_context += f"\n\n## Encounter\n{exploration['encounter_context']}"

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

        pre_turn_mode = (status.get("party") or {}).get("mode", "surface")
        narration = self._llm_loop(messages)
        gate_active = self._exploration_gate_active(pre_turn_mode)

        if self._encounter_verify_active(status):
            status = self.bridge.status()
            truth = build_encounter_turn_truth(
                status,
                self._get_encounter_state(status),
                self._tools_ok_this_turn,
                gate_flags={"entry_committed": self._entry_committed_this_turn},
            )
            narration = self.narrate_with_verification(
                "",
                player_input,
                truth=truth,
                initial_prose=narration,
                mode="exploration",
                state_context=state_context,
            ) or _ENCOUNTER_VERIFY_FALLBACK
        elif self._exploration_economy_verify_active(status):
            status = self.bridge.status()
            truth = build_exploration_turn_truth(
                status,
                self._last_tool_results,
                social_state=self._social_state_for_truth(),
                player_input=player_input,
            )
            narration = self.narrate_with_verification(
                "",
                player_input,
                truth=truth,
                initial_prose=narration,
                mode="exploration",
                state_context=state_context,
            ) or _EXPLORATION_ECONOMY_VERIFY_FALLBACK

        narration = self._compose_exploration_narration(narration, gate_active=gate_active)
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
        cleaned = strip_flavor_race_table(cleaned)
        cleaned = strip_flavor_stats_table(cleaned)
        cleaned = strip_flavor_equipment_claims(cleaned)
        cleaned = self._sanitize_creation_flavor(cleaned)
        try:
            roster_len = len(self.bridge.status().get("roster") or [])
        except Exception:
            roster_len = 0
        if self.creation.active or roster_len == 0:
            sanitized = sanitize_premature_completion_flavor(
                cleaned,
                active=self.creation.active,
                step=self.creation.step,
                roster_len=roster_len,
            )
            if sanitized != cleaned:
                cleaned = strip_llm_status_tags(sanitized)
            else:
                cleaned = sanitized
        if cleaned:
            parts.append(cleaned)
        if body.strip():
            parts.append(body.strip())
        status_line = footer if footer is not None else format_creation_status(self.creation)
        if status_line:
            parts.append(status_line)
        return "\n\n".join(parts)

    def _committed_state_flavor_block(self) -> str:
        lines: list[str] = []
        if self.creation.name:
            lines.append(f"Character name: {self.creation.name}")
        if self.creation.race:
            lines.append(f"Committed race: {race_display_title(self.creation.race)}")
        if self.creation.chosen_class:
            lines.append(f"Committed class: {self.creation.chosen_class}")
        if self.creation.chosen_skills:
            names = ", ".join(SKILL_DISPLAY.get(s, s) for s in self.creation.chosen_skills)
            lines.append(f"Committed skills: {names}")
        return "\n".join(lines)

    def _sanitize_creation_flavor(self, flavor: str) -> str:
        if not self.creation.active or not self.creation.race:
            return flavor
        for key in RACES:
            if key == self.creation.race:
                continue
            title = race_display_title(key)
            if re.search(rf"\b{re.escape(title)}\b", flavor, re.IGNORECASE):
                return ""
        return flavor

    def _creation_flavor_messages(
        self,
        instruction: str,
        player_input: str,
        *,
        truth_block: str = "",
    ) -> list[dict[str, Any]]:
        committed = self._committed_state_flavor_block()
        committed_block = f"\n\n{committed}\n" if committed else ""
        truth_section = f"\n\n{truth_block}\n" if truth_block else ""
        history_block = [] if self.creation.active else list(self.history[-4:])
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "system",
                "content": (
                    "You are the GM for Tomb Dust at the Registry desk in Breley Keep.\n"
                    f"Character: {self.creation.name or '(unnamed)'}\n"
                    f"Creation step: {self.creation.step}\n"
                    f"{committed_block}"
                    f"{truth_section}\n"
                    f"{instruction}\n\n"
                    "Write 1-2 short sentences of in-character flavor ONLY.\n"
                    "Do NOT include markdown tables, status lines, [Location:...], Phase, Awaiting, "
                    "or mechanical numbers — code appends those."
                ),
            },
            *history_block,
            {"role": "user", "content": player_input},
        ]

    def _exploration_narration_messages(
        self,
        player_input: str,
        truth_block: str,
        state_context: str,
        *,
        truth: TurnTruth | None = None,
    ) -> list[dict[str, Any]]:
        if truth and not truth.encounter_phase and not (truth.step or "").startswith("encounter_"):
            write_hint = (
                "Write 1-3 sentences of scene narration only. "
                "Do not claim GP changes, item transfers, or social pass/fail unless authoritative facts allow."
            )
        else:
            write_hint = (
                "Write 1-3 sentences of encounter narration only. "
                "Offer detect, sneak, withdraw, or hostile engage — do not start combat in prose."
            )
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": state_context},
            {
                "role": "system",
                "content": f"{truth_block}\n\n{write_hint}",
            },
            *self.history[-4:],
            {"role": "user", "content": player_input},
        ]

    def _emit_api_error(
        self,
        *,
        exc: BaseException,
        attempt: int,
        sent_messages: list[dict],
        original_messages: list[dict],
        context: str | None,
        depth: int | None,
        tools: list | None,
        retry_truncated: bool = False,
    ) -> None:
        payload: dict[str, Any] = {
            "context": context or "unknown",
            "exc_type": type(exc).__name__,
            "error": str(exc),
            "model": self.model,
            "tools_present": tools is not None,
            "attempt": attempt,
            "malformed_transcript_400": is_malformed_transcript_400(exc),
            "original_len": len(original_messages),
            "sent_len": len(sent_messages),
            "messages_summary": summarize_messages_for_log(sent_messages),
            "tool_chain": extract_tool_chain(sent_messages),
        }
        if depth is not None:
            payload["depth"] = depth
        if retry_truncated:
            payload["retry_truncated"] = True
        try:
            log_api_error(payload)
        except Exception:
            pass

    def _chat_completion(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list | None = None,
        tool_choice: str | dict | None = "auto",
        max_tokens: int | None = None,
        temperature: float | None = None,
        context: str | None = None,
        depth: int | None = None,
    ) -> dict:
        clean = sanitize_transcript_messages(messages)
        cc_kwargs = dict(
            model=self.model,
            messages=clean,
            tools=tools,
            tool_choice=tool_choice,
            max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
            temperature=temperature if temperature is not None else self.temperature,
        )
        try:
            return chat_completion(self.client, **cc_kwargs)
        except Exception as exc:
            if not is_malformed_transcript_400(exc):
                self._emit_api_error(
                    exc=exc,
                    attempt=1,
                    sent_messages=clean,
                    original_messages=messages,
                    context=context,
                    depth=depth,
                    tools=tools,
                )
                raise
            truncated = _safe_prefix_fallback(messages)
            log_transcript_400_retry({
                "context": context or "unknown",
                "attempt": 1,
                "original_len": len(messages),
                "clean_len": len(clean),
                "prefix_len": len(truncated),
                "will_retry": True,
            })
            retry_clean = sanitize_transcript_messages(truncated)
            try:
                return chat_completion(
                    self.client,
                    **{**cc_kwargs, "messages": retry_clean},
                )
            except Exception as exc2:
                self._emit_api_error(
                    exc=exc2,
                    attempt=2,
                    sent_messages=retry_clean,
                    original_messages=messages,
                    context=context,
                    depth=depth,
                    tools=tools,
                    retry_truncated=True,
                )
                raise

    def _call_narration_llm(self, messages: list[dict[str, Any]]) -> str:
        """Short LLM flavor call (configurable creation flavor cap, default 500; no tools)."""
        log_llm_request(len(messages), self.model, 0)
        try:
            response = self._chat_completion(
                messages=messages,
                tools=None,
                max_tokens=self._creation_flavor_max_tokens,
                context="narrate_flavor",
            )
        except Exception as exc:
            self._last_finish_reason = ""
            return _NAME_LENGTH_STATIC_FALLBACK
        content = response.get("content", "") or _NAME_LENGTH_STATIC_FALLBACK
        self._last_finish_reason = response.get("finish_reason", "") or ""
        log_llm_response(content, [], self._last_finish_reason)
        return content

    def _narrate_flavor(self, messages: list[dict[str, Any]]) -> str:
        """Short LLM flavor during creation (configurable creation flavor cap, default 500; no tools)."""
        return self._call_narration_llm(messages)

    def narrate_with_verification(
        self,
        instruction: str,
        player_input: str,
        *,
        truth: TurnTruth | None = None,
        initial_prose: str | None = None,
        mode: str = "creation",
        state_context: str = "",
        body_pending: bool = False,
        flavor_only: bool = False,
        presenting_step: str | None = None,
        skip_llm: bool = False,
    ) -> str:
        """Inject turn truth, verify prose, retry until pass or exhaust (APP-083)."""
        if skip_llm:
            return ""

        if truth is not None and initial_prose is not None and mode == "exploration":
            return self._narrate_exploration_with_verification(
                player_input,
                truth,
                initial_prose,
                state_context=state_context,
            )

        truth = build_creation_turn_truth(self.creation)
        truth_block = format_turn_truth_for_prompt(truth, creation=self.creation)
        messages = self._creation_flavor_messages(
            instruction, player_input, truth_block=truth_block
        )
        length_retries = self._length_max_recovery_retries
        verify_retries = self._narration_verify_max_retries
        step = self.creation.step

        for attempt in range(self._narration_llm_max_attempts):
            prose = self._call_narration_llm(messages)
            recovery = handle_finish_reason_length(
                self._last_finish_reason,
                prose,
                body_pending=body_pending,
                flavor_only=flavor_only,
                length_retries_left=length_retries,
            )
            if recovery.action == "discard":
                prose = ""
                log_llm_truncation_recovery(
                    {"step": step, "action": "discard_flavor", "finish_reason": "length"}
                )
            elif recovery.action == "retry":
                length_retries -= recovery.attempt_budget_used
                log_llm_truncation_recovery(
                    {"step": step, "action": "retry", "finish_reason": "length"}
                )
                messages = [
                    *messages,
                    {"role": "assistant", "content": prose},
                    {
                        "role": "user",
                        "content": "Continue briefly in 1-2 short sentences only.",
                    },
                ]
                continue
            elif recovery.action == "fallback":
                log_llm_truncation_recovery(
                    {"step": step, "action": "fallback", "finish_reason": "length"}
                )
                return recovery.next_prose

            if presenting_step:
                prose = self._sanitize_creation_flavor(prose)

            check = verify_narration(prose, truth)
            if check.passed:
                if prose.strip():
                    log_narration_verify_pass({"step": step, "attempt": attempt + 1})
                return prose

            log_narration_verify_fail(
                {
                    "step": step,
                    "attempt": attempt + 1,
                    "violations": list(check.violations),
                }
            )
            verify_retries -= 1
            if verify_retries <= 0:
                log_narration_verify_exhausted({"step": step, "attempt": attempt + 1})
                if flavor_only:
                    return _NAME_LENGTH_STATIC_FALLBACK
                return ""

            messages = [
                *messages,
                {"role": "assistant", "content": prose},
                {
                    "role": "user",
                    "content": (
                        "Rewrite 1-2 sentences only. "
                        f"Violations: {', '.join(check.violations)}. "
                        "Do not contradict authoritative facts."
                    ),
                },
            ]

        log_narration_verify_exhausted({"step": step, "attempt": self._narration_llm_max_attempts})
        if flavor_only:
            return _NAME_LENGTH_STATIC_FALLBACK
        return ""

    def _narrate_exploration_with_verification(
        self,
        player_input: str,
        truth: TurnTruth,
        initial_prose: str,
        *,
        state_context: str = "",
    ) -> str:
        """Verify settled _llm_loop prose; retry via tool-free _call_narration_llm only (APP-089 D9)."""
        truth_block = format_turn_truth_for_prompt(truth, creation=None)
        verify_step = truth.step or (
            f"encounter_{truth.encounter_phase}" if truth.encounter_phase else "encounter"
        )
        messages = self._exploration_narration_messages(
            player_input, truth_block, state_context, truth=truth
        )
        verify_retries = self._narration_verify_max_retries
        prose = initial_prose

        for attempt in range(verify_retries + 1):
            check = verify_narration(prose, truth)
            if check.passed:
                if prose.strip():
                    log_narration_verify_pass(
                        {
                            "mode": "exploration",
                            "step": verify_step,
                            "attempt": attempt + 1,
                        }
                    )
                return prose

            log_narration_verify_fail(
                {
                    "mode": "exploration",
                    "step": verify_step,
                    "attempt": attempt + 1,
                    "violations": list(check.violations),
                }
            )
            if attempt >= verify_retries:
                log_narration_verify_exhausted(
                    {
                        "mode": "exploration",
                        "step": verify_step,
                        "attempt": attempt + 1,
                    }
                )
                return ""

            messages = [
                *messages,
                {"role": "assistant", "content": prose},
                {
                    "role": "user",
                    "content": (
                        "Rewrite 1-3 sentences only. "
                        f"Violations: {', '.join(check.violations)}. "
                        f"{truth_block}\n"
                        "Do not contradict authoritative facts."
                    ),
                },
            ]
            prose = self._call_narration_llm(messages)

        log_narration_verify_exhausted(
            {"mode": "exploration", "step": verify_step, "attempt": verify_retries + 1}
        )
        return ""

    def _narrate_creation_flavor(
        self, instruction: str, player_input: str, *, presenting_step: str | None = None
    ) -> str:
        return self.narrate_with_verification(
            instruction,
            player_input,
            body_pending=True,
            presenting_step=presenting_step,
        )

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
        elif self.creation.step == "RACE" and (is_system_trigger or not self.creation.races_table_shown):
            narration = self._auto_present_race(player_input)
        elif self.creation.step == "RACE":
            narration = self._handle_creation_response(player_input) or self._auto_present_race(
                player_input,
                error="Pick one race from the table.",
            )
        elif self.creation.step == "CLASS" and (is_system_trigger or not self.creation.classes_table_shown):
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
        flavor = self.narrate_with_verification(
            "A Registry clerk asks a new delver for their legal name.",
            player_input,
            body_pending=False,
            flavor_only=True,
        )
        body = f"{err}What name shall I put on the Registry ledger?"
        return self._compose_creation_narration(flavor, body)

    def _auto_present_race(self, player_input: str, error: str | None = None) -> str:
        self.creation.races_table_shown = True
        err = f"**Note:** {error}\n\n" if error else ""
        flavor = self.narrate_with_verification(
            f"The clerk writes down '{self.creation.name}' and asks about lineage. "
            "Brief clerk banter only — do not list races or use markdown tables; "
            "the Registry ledger appends the race table.",
            player_input,
            body_pending=True,
            skip_llm=bool(error),
        )
        body = err + format_races_table()
        return self._compose_creation_narration(flavor, body)

    def _auto_present_class(self, player_input: str, error: str | None = None) -> str:
        self.creation.classes_table_shown = True
        err = f"**Note:** {error}\n\n" if error else ""
        eligible = self.creation.roll_result.get("eligible_classes", ["peasant"])
        attrs = self.creation.roll_result.get("final_attributes", {})
        flavor = self.narrate_with_verification(
            "Present the stat results briefly, then ask which tier-1 class path the delver chooses.",
            player_input,
            body_pending=True,
            skip_llm=bool(error),
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
            return self._auto_present_race("[SYSTEM: Step auto-advanced from name. Continue.]")

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
                    error=format_skill_parse_error(
                        player_input, self.creation.chosen_class
                    ),
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
        if self.creation.step == "RACE":
            extra = self._auto_present_race("[SYSTEM: Step auto-advanced. Continue.]")
            return f"{prior}\n\n{extra}".strip() if prior else extra
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
        if self.creation.step == "RACE" and not self.creation.race:
            extra = self._auto_present_race("[SYSTEM: Step auto-advanced. Continue.]")
            return f"{prior}\n\n{extra}".strip() if prior else extra
        return prior or "The clerk waits."

    def _creation_table_flavor(
        self, instruction: str, player_input: str, *, error: str | None
    ) -> str:
        return self.narrate_with_verification(
            instruction,
            player_input,
            body_pending=True,
            skip_llm=bool(error),
        )

    def _auto_present_skills(self, player_input: str, error: str | None = None) -> str:
        """Deterministic skills table — code body, thin LLM flavor."""
        self.creation.skills_table_shown = True
        err = f"**Note:** {error}\n\n" if error else ""
        flavor = self._creation_table_flavor(
            f"Ask {self.creation.name} which three skills they trained in as a {self.creation.chosen_class}.",
            player_input,
            error=error,
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
        flavor = self._creation_table_flavor(
            "Ask which magical schools the delver studied.",
            player_input,
            error=error,
        )
        body = err + format_schools_table(self.creation.chosen_class)
        return self._compose_creation_narration(flavor, body)

    def _auto_present_spells(self, player_input: str, error: str | None = None) -> str:
        """Deterministic starting spell table."""
        self.creation.spells_table_shown = True
        err = f"**Note:** {error}\n\n" if error else ""
        flavor = self._creation_table_flavor(
            "Ask which tier-1 spells the delver memorized from their chosen schools.",
            player_input,
            error=error,
        )
        body = err + format_spells_table(self.creation.chosen_class, self.creation.chosen_schools)
        return self._compose_creation_narration(flavor, body)

    def _auto_present_equipment(self, player_input: str, error: str | None = None) -> str:
        """Present kit and gold from ensure_equipment_gold; require explicit confirm."""
        ensure_equipment_gold(self.creation)
        err = f"**Note:** {error}\n\n" if error else ""
        flavor = self.narrate_with_verification(
            "Brief Registry clerk banter only — mood, paperwork, confirmation ask. "
            "Do not mention kit contents, gold amounts, GP, coin pouches, or item lists; "
            "code appends the authoritative Registry kit summary.",
            player_input,
            body_pending=True,
            skip_llm=bool(error),
        )
        body = err + format_equipment_summary(self.creation)
        return self._compose_creation_narration(flavor, body)

    def _auto_roll_stats(self, player_input: str) -> str:
        """ROLL_STATS: code rolls and formats tables; LLM flavor only."""
        result = self.bridge.roll_attributes(self.creation.race)
        log_tool_call("roll_attributes", {"race": self.creation.race}, result)
        self.creation.roll_result = result
        self.creation.advance()
        self._remember_creation_step("ROLL_STATS")

        eligible = result.get("eligible_classes", ["peasant"])
        race_title = race_display_title(self.creation.race)
        flavor = self._narrate_creation_flavor(
            f"The clerk reacts briefly to the dice roll for a delver whose lineage is **{race_title}**. "
            "Write 1–2 sentences of Registry banter only — mood, ledger ink, superstition. "
            "Do not name or imply any other race. "
            "Do not present attribute numbers, HP, or markdown tables; code appends the full roll readout. "
            "Do not include status lines or Awaiting labels.",
            player_input,
            presenting_step="ROLL_STATS",
        )
        body = format_roll_stats_table(result) + "\n\n" + format_classes_table(eligible)
        self.creation.classes_table_shown = True
        return self._compose_creation_narration(flavor, body)

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

        flavor = self.narrate_with_verification(
            f"Character {self.creation.name} is registered. Describe them stepping into Breley Keep "
            "(outer bailey, garrison, King's Road, smithies, postern gate). End by asking what they do first.",
            player_input,
            body_pending=True,
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
            response = self._chat_completion(messages=messages, tools=None, context="narrate_only")
        except Exception as exc:
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
                response = self._chat_completion(
                    messages=messages,
                    tools=tools if depth < 2 else None,
                    tool_choice=tool_choice if depth < 2 else "none",
                    context="creation_llm_loop",
                    depth=depth,
                )
            except Exception as exc:
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
                args = normalize_tool_args(fn_name, args)

                if fn_name != "set_creation_choice":
                    result = {"ok": False, "error": f"Only set_creation_choice is available. Got: {fn_name}"}
                elif err := validate_tool_args(fn_name, args):
                    result = {"ok": False, "error": err}
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
            if not self.creation.races_table_shown:
                return {"ok": False, "error": "Race table must be shown before recording picks."}
            race = value.strip().lower().replace(" ", "-")
            if race not in RACES:
                parsed = parse_player_race(source_text)
                if parsed:
                    race = parsed
                else:
                    return {"ok": False, "error": f"Invalid race '{race}'. Valid: {list(RACES.keys())}"}
            self.creation.race = race

        elif step == "CLASS":
            if not self.creation.classes_table_shown:
                return {"ok": False, "error": "Class table must be shown before recording picks."}
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
            elif action == "fortune_spend":
                f = item.get("fortune") or {}
                lines.append(
                    f"fortune_spend: {item.get('character_id')} spent={item.get('spent', 1)} "
                    f"pool={f.get('current')}/{f.get('max')} "
                    f"pending_advantage={item.get('pending_advantage', False)}"
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
            self._emit_exploration_narration(narration)
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
            death_result = self._handle_player_death(mechanical)
            if death_result is not None:
                if not death_result.already_emitted:
                    self._emit_narration(death_result.message)
                self.history.append({"role": "user", "content": player_input})
                self.history.append({"role": "assistant", "content": death_result.message})
                return death_result.message
            status = self.bridge.status()
            if is_pc_turn(status):
                narration = self._combat_llm_loop(player_input, status)
            else:
                brief = self._combat_mechanical_brief(mechanical)
                narration = self._narrate_text(brief + "\n\nMonsters act. Narrate their attacks.")

        self._emit_exploration_narration(narration)
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
        if is_pc_turn(status):
            step_prompt += (
                "\n\nFortune: if the player spends Fortune on this attack, call "
                "`fortune_spend(character_id=<turn_id>)` THEN `combat_action` (ATTACK or CAST) "
                "in one batch — **fortune_spend first**. Do not narrate Fortune spent without "
                "a successful fortune_spend tool result."
            )
        state_context = build_state_context(status, recap, check, suggest, None)
        if step_prompt:
            state_context += "\n\n## Combat Step\n" + step_prompt
        if self.combat.last_mechanical:
            state_context += "\n\n" + self._combat_mechanical_brief(self.combat.last_mechanical)
            self.combat.last_mechanical = []

        messages = build_messages(SYSTEM_PROMPT, state_context, self.history, player_input)
        return self._combat_llm_loop_inner(messages, depth=0)

    def _reorder_combat_pc_tool_calls(self, tool_calls: list[dict]) -> list[dict]:
        """If batch has fortune_spend + combat_action for same actor, run spend first (F11)."""
        if len(tool_calls) < 2:
            return tool_calls

        parsed: list[tuple[dict, str, dict]] = []
        for tc in tool_calls:
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                args = {}
            parsed.append((tc, name, normalize_tool_args(name, args)))

        if not any(p[1] == "fortune_spend" for p in parsed):
            return tool_calls
        if not any(p[1] == "combat_action" for p in parsed):
            return tool_calls

        status = self.bridge.status()
        turn_id = (status.get("combat") or {}).get("turn_id")
        fortune_ids = {p[2].get("character_id") for p in parsed if p[1] == "fortune_spend"}
        combat_ids = {p[2].get("actor_id") for p in parsed if p[1] == "combat_action"}
        same_actor = bool(fortune_ids & combat_ids)
        if not same_actor and turn_id:
            same_actor = turn_id in fortune_ids and turn_id in combat_ids
        if not same_actor:
            return tool_calls

        order = {"fortune_spend": 0, "combat_action": 1}

        def sort_key(item: tuple[dict, str, dict]) -> tuple[int, int]:
            _, name, _ = item
            return (order.get(name, 2), tool_calls.index(item[0]))

        return [p[0] for p in sorted(parsed, key=sort_key)]

    def _combat_llm_loop_inner(self, messages: list[dict], depth: int = 0) -> str:
        if depth > 3:
            return self._last_content or "Combat stalls — try your action again."

        log_llm_request(len(messages), self.model, depth)
        try:
            response = self._chat_completion(
                messages=messages,
                tools=COMBAT_PC_TOOLS,
                tool_choice="auto",
                context="combat_tools",
                depth=depth,
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

        for tc in self._reorder_combat_pc_tool_calls(tool_calls):
            fn_name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                args = {}
            args = normalize_tool_args(fn_name, args)
            if fn_name == "combat_action":
                if err := validate_tool_args(fn_name, args):
                    result = {"ok": False, "error": err}
                else:
                    result = self._execute_combat_action(**args)
            elif fn_name == "fortune_spend":
                if err := validate_tool_args(fn_name, args):
                    result = {"ok": False, "error": err}
                else:
                    result = self._execute_combat_fortune_spend(**args)
            else:
                result = {
                    "ok": False,
                    "error": (
                        f"During combat only combat_action and fortune_spend are available. "
                        f"Got: {fn_name}"
                    ),
                }
            log_tool_call(fn_name, args, result)
            self._last_tool_results[fn_name] = result
            if result.get("ok"):
                all_failed = False
                mechanical.extend(result.get("mechanical") or [])
            else:
                messages.append({
                    "role": "system",
                    "content": (
                        f"TOOL FAILED ({fn_name}): {json.dumps(result, default=str)}. "
                        "You MUST narrate this failure honestly. Do NOT describe success."
                    ),
                })
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(result, default=str)})

        if all_failed:
            failures = "; ".join(
                f"{n}: {r.get('error', r)}"
                for n, r in self._last_tool_results.items()
                if not r.get("ok")
            )
            prefix = (
                f"[Mechanics failed — {failures}]"
                if failures
                else "[Mechanics failed — combat_action: unknown failure]"
            )
            log_error("combat_llm_loop", f"all tools failed at depth {depth}, stripping assistant content")
            if not failures:
                return f"{prefix}\n\nYour action did not resolve."
            return prefix

        self.combat.last_mechanical = mechanical
        auto = self._combat_auto_chain()
        mechanical.extend(auto)
        death_result = self._handle_player_death(mechanical)
        if death_result is not None:
            if not death_result.already_emitted:
                self._emit_narration(death_result.message)
            self.history.append({"role": "assistant", "content": death_result.message})
            return death_result.message
        self._sync_combat_from_status()

        brief = self._combat_mechanical_brief(mechanical)
        narrate_messages = messages + [
            {"role": "user", "content": brief + "\n\nNarrate the combat results honestly. Do not call more tools."},
        ]
        try:
            final = self._chat_completion(
                messages=narrate_messages,
                tools=None,
                context="combat_narrate",
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
        if action.upper().strip() == "ATTACK":
            if err := self._gate_pc_attack(actor_id):
                return err

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

    def _execute_combat_fortune_spend(self, character_id: str) -> dict:
        status = self.bridge.status()
        if not status.get("combat"):
            return {"ok": False, "error": "no active combat"}
        turn_id = status["combat"].get("turn_id")
        if character_id != turn_id:
            return {"ok": False, "error": f"not your turn: expected {turn_id}, got {character_id}"}
        from tomb_gm.domain.combat_player import spend_fortune

        session_id = self.bridge._active_session_id()
        campaign_slug = self.bridge._campaign_slug()
        try:
            result = spend_fortune(
                self.bridge.ctx.conn,
                campaign_slug=campaign_slug,
                character_id=character_id,
                session_id=session_id,
            )
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        if not result.get("ok"):
            return {"ok": False, "error": result.get("error", "fortune spend failed")}
        mechanical_row = {
            "action": "fortune_spend",
            "character_id": character_id,
            "spent": result.get("spent", 1),
            "fortune": result.get("fortune"),
            "pending_advantage": result.get("pending_advantage", True),
        }
        return {"ok": True, "mechanical": [mechanical_row], **result}

    def _handle_combat_trigger(self, beat_result: dict) -> str | None:
        status = self.bridge.status()
        encounter_key = self._encounter_room_key(status)
        phase = self._current_encounter_phase(status) if encounter_key else ""
        for item in beat_result.get("mechanical_summary") or []:
            if item.get("action") != "combat_trigger":
                continue
            if encounter_key and phase not in ("engaged", "ambush"):
                continue
            specs = item.get("monster_specs") or ["grave-ghoul:1"]
            if self._combat_active_in_db():
                continue
            surprised_ids = self._surprised_combatant_ids_if_ambush(status)
            start = self.bridge.start_combat(
                monster_specs=specs,
                include_party=item.get("include_party", True),
                surprised_combatant_ids=surprised_ids,
            )
            if not start.get("ok"):
                self.combat.active = False
                err = start.get("error", start)
                return (
                    f"[Mechanics failed — combat start: {err}]\n\n"
                    "Combat could not begin."
                )
            self.combat.active = True
            self.combat.step = "COMBAT_PC_ACTION"
            self.combat.order_narrated = False
            self._set_encounter_phase(status, "in_combat")
        return None

    def _llm_loop(self, messages: list[dict[str, Any]], depth: int = 0, allow_tools: bool = True) -> str:
        """Call LLM, execute tool calls, loop until we get narration text."""
        if self.creation.active:
            log_error("llm_loop", "blocked exploration loop during active creation")
            return self._creation_turn("[SYSTEM: Finish character creation first.]")

        if depth == 0:
            self._last_tool_results = {}
            self._tools_ok_this_turn = []
            self._pending_contest_type = None
            self._beat_combat_start_failure = None
            self._entry_committed_this_turn = False
            self._delve_entry_hint_this_turn = None
            try:
                st = self.bridge.status()
                self._exploration_pre_turn_mode = (st.get("party") or {}).get("mode", "surface")
            except Exception:
                self._exploration_pre_turn_mode = "surface"
        if depth > 4:
            log_error("llm_loop", f"depth limit reached ({depth}), last_content={bool(self._last_content)}")
            last_content = self._last_content
            if last_content:
                return last_content
            return "The dust settles. You stand at the crossroads, uncertain. What do you do?"

        log_llm_request(len(messages), self.model, depth)

        try:
            response = self._chat_completion(
                messages=messages,
                tools=TOOLS if (allow_tools and depth < 3) else None,
                context="llm_loop",
                depth=depth,
            )
        except Exception as exc:
            if self._last_content:
                return self._last_content
            return f"The GM falters. (API error: {exc})"

        tool_calls = response.get("tool_calls", [])
        content = response.get("content", "")
        finish_reason = response.get("finish_reason", "")

        log_llm_response(content, tool_calls, finish_reason)

        self._last_content = content or self._last_content

        if not tool_calls:
            if finish_reason == "length":
                log_llm_truncation_recovery(
                    {
                        "mode": "exploration",
                        "action": "fallback_last_content" if self._last_content else "emit_truncated",
                        "finish_reason": "length",
                    }
                )
                if self._last_content and self._last_content != content:
                    return self._last_content
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
            args = normalize_tool_args(fn_name, args)
            if err := validate_tool_args(fn_name, args):
                result = {"ok": False, "error": err}
            else:
                result = self._execute_tool(fn_name, args)
            if _should_delve_entry_hint(fn_name, args, result):
                hint = self._build_delve_entry_hint()
                result = {**result, "hint": hint}
                if self._delve_entry_hint_this_turn is None:
                    self._delve_entry_hint_this_turn = hint
            log_tool_call(fn_name, args, result)
            self._last_tool_results[fn_name] = result
            if result.get("ok"):
                self._tools_ok_this_turn.append(fn_name)
            if fn_name in ("enter_dungeon", "site_enter") and result.get("ok"):
                self._entry_committed_this_turn = True
            if result.get("ok", False):
                all_failed = False
                if not self.creation.active:
                    fact = tool_impact_fact(fn_name, args, result)
                    if fact:
                        self._remember_player_choice(fact, importance=3)
            else:
                sys_content = (
                    f"TOOL FAILED ({fn_name}): {json.dumps(result, default=str)}. "
                    "You MUST narrate this failure honestly. Do NOT describe success."
                )
                if result.get("hint"):
                    sys_content += f" Hint: {result['hint']}"
                messages.append({
                    "role": "system",
                    "content": sys_content,
                })
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, default=str),
            })

        beat_failure = getattr(self, "_beat_combat_start_failure", None)
        if beat_failure:
            self._beat_combat_start_failure = None
            log_error("llm_loop", f"beat combat start failed: {beat_failure[:120]}")
            return beat_failure

        if all_failed and content:
            log_error("llm_loop", f"all tools failed at depth {depth}, returning content")
            failures = "; ".join(
                f"{name}: {res.get('error', res)}"
                for name, res in self._last_tool_results.items()
                if not res.get("ok")
            )
            prefix = f"[Mechanics failed — {failures}]"
            failed_names = {
                name for name, res in self._last_tool_results.items()
                if not res.get("ok")
            }
            if failed_names & _COMBAT_TOOL_NAMES:
                return prefix
            gate_active = self._exploration_gate_active(self._exploration_pre_turn_mode)
            safe = self._compose_exploration_narration(content, gate_active=gate_active)
            hint = self._delve_entry_hint_this_turn
            if depth == 0 and hint:
                return f"{prefix}\n\n{hint}\n\n{safe}"
            return f"{prefix}\n\n{safe}"

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
                if name == "fortune_spend":
                    if err := validate_tool_args(name, args):
                        return {"ok": False, "error": err}
                    return self._execute_combat_fortune_spend(**args)
                return {
                    "ok": False,
                    "error": (
                        f"During combat only combat_action and fortune_spend are available. "
                        f"Got: {name}"
                    ),
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
                status = self.bridge.status()
                features = self._room_features_from_status(status)
                phase = self._current_encounter_phase(status)
                contest_type = self._infer_contest_type(
                    str(args.get("reason") or ""),
                    self._current_player_input,
                    phase,
                    features,
                )
                if contest_type:
                    self._pending_contest_type = contest_type
                result = self.bridge.roll_d20(**args)
                if result.get("ok") and contest_type and self._encounter_room_key(status):
                    self._resolve_encounter_contest(result, contest_type)
                self._pending_contest_type = None
                return result
            elif name == "process_beat":
                result = self.bridge.process_beat(**args)
                self._scan_beat_roll_contests(result)
                result = self._handle_beat_encounter_rows(result)
                failure = self._handle_combat_trigger(result)
                if failure:
                    self._beat_combat_start_failure = failure
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
                status = self.bridge.status()
                encounter_key = self._encounter_room_key(status)
                if encounter_key:
                    phase = self._current_encounter_phase(status)
                    if phase not in ("engaged", "ambush"):
                        return {
                            "ok": False,
                            "error": "ENCOUNTER_NOT_ENGAGED",
                            "hint": _ENCOUNTER_NOT_ENGAGED_HINT,
                            "encounter_phase": phase,
                        }
                surprised_ids = self._surprised_combatant_ids_if_ambush(status)
                result = self.bridge.start_combat(
                    **args,
                    surprised_combatant_ids=surprised_ids,
                )
                if result.get("ok"):
                    self._set_encounter_phase(status, "in_combat")
                return result
            elif name == "combat_attack":
                if err := self._gate_pc_attack(args.get("attacker_id", "")):
                    return err
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
                result = self.bridge.enter_dungeon(**args)
                if result.get("ok"):
                    status = self.bridge.status()
                    features = result.get("features") or []
                    if self._enemy_threats_from_features(features):
                        self._init_encounter_state_detected(status, features)
                        result = {**result, "encounter_hint": _ENCOUNTER_ENTRY_HINT}
                return result
            elif name == "move_room":
                result = self.bridge.move_room(**args)
                if result.get("ok"):
                    status = self.bridge.status()
                    key = self._encounter_room_key(status)
                    features = result.get("features") or self._room_features_from_status(status)
                    if key:
                        threats = self._enemy_threats_from_features(features)
                        if threats:
                            self._encounter_by_room[key] = {"phase": "detected", "threats": threats}
                        else:
                            self._encounter_by_room.pop(key, None)
                return result
            elif name == "exit_dungeon":
                result = self.bridge.exit_dungeon()
                if result.get("ok"):
                    self._encounter_by_room.clear()
                    self._current_encounter_key = None
                return result
            elif name == "interact_feature":
                return self.bridge.interact_feature(**args)
            elif name == "list_inventory":
                return self.bridge.list_inventory(**args)
            elif name == "equip_item":
                return self.bridge.equip_item(**args)
            elif name == "unequip_item":
                return self.bridge.unequip_item(**args)
            elif name == "use_item":
                return self.bridge.use_item(**args)
            elif name == "has_pack_item":
                return self.bridge.has_pack_item(**args)
            elif name == "remove_pack_item":
                return self.bridge.remove_pack_item(**args)
            elif name == "deliver_quest_item":
                return self.bridge.deliver_quest_item(**args)
            elif name == "grant_loot":
                return self.bridge.grant_loot(**args)
            elif name == "buy_item":
                return self.bridge.buy_item(**args)
            elif name == "sell_item":
                return self.bridge.sell_item(**args)
            elif name == "list_stash":
                return self.bridge.list_stash(**args)
            elif name == "list_factions":
                return self.bridge.list_factions(**args)
            elif name == "list_vendor":
                return self.bridge.list_vendor(**args)
            elif name == "skill_check":
                return self.bridge.skill_check(**args)
            elif name == "negotiate_quest_advance":
                return self.bridge.negotiate_quest_advance(**args)
            elif name == "offer_quest":
                return self.bridge.offer_quest(**args)
            elif name == "accept_quest":
                return self.bridge.accept_quest(**args)
            elif name == "grant_quest_advance":
                return self.bridge.grant_quest_advance(**args)
            elif name == "list_quests":
                return self.bridge.list_quests()
            elif name == "social_encounter_status":
                return self.bridge.social_encounter_status()
            else:
                return {"ok": False, "error": f"Unknown tool: {name}"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
