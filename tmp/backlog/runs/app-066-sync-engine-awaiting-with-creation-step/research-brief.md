# Research Brief: APP-066-sync-engine-awaiting-with-creation-step

**Date:** 2026-05-20
**Question:** Where should `awaiting` be set during character creation — bridge/orchestrator vs `tomb_gm` engine? What is the minimal fix to stop `creation_drift` on every healthy creation turn?

**backlog_ticket:** APP-066
**ticket_path:** tmp/backlog/app-066-sync-engine-awaiting-with-creation-step.md
**domain_spec:** tmp/app-character-creation-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket **Domain spec** is [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md), which owns `app/gm/creation.py`, creation paths in `app/gm/orchestrator.py`, and documents code-owned status labels. [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Character creation** maps to that spec. Secondary drift semantics live in [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) (`creation_drift` event). No new domain spec is required.

## Summary

`bridge.status()["awaiting"]` is **engine-owned** and intentionally coarse: `play/tomb_gm/cli/cmd_core.py` `handle_status` sets `CHARACTER_CREATION` whenever the active session has an empty roster and no character rows — for the **entire** creation period, regardless of app FSM step. Granular player-facing labels (`NAME_INPUT`, `SKILLS_INPUT`, …) are **app-owned** in `CREATION_STATUS_LABELS` / `format_creation_status()` driven by `CreationState.step` in `app/gm/creation.py`.

APP-002’s `_check_creation_drift()` compares narration `Awaiting:` (granular) to engine `status["awaiting"]` (`CHARACTER_CREATION`). That comparison is **structurally wrong** for healthy creation turns, so `awaiting_mismatch` fires on every `_emit_narration` during creation — not a gameplay bug.

**Minimal fix (recommended):** Do **not** push granular steps into `tomb_gm`. Adjust `_check_creation_drift` in `app/gm/orchestrator.py` so that when `creation.active`, expected awaiting is `CREATION_STATUS_LABELS[self.creation.step]` (same source as `format_creation_status`). Keep engine `CHARACTER_CREATION` for CLI `suggest`, save/resume gates, and post-finalize `PLAYER_ACTIONS`. Document the two-layer contract in the character-creation spec; note drift semantic change in the logging spec.

`phase_mismatch` during creation is secondary: code footers omit `Phase:` except `WORLD_INTRO` finalize; mismatches usually mean LLM-invented phase in flavor (real drift) or full bracket footer vs engine `preparation`.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Drift detector | `app/gm/orchestrator.py` | `_creation_drift_scope`, `_check_creation_drift`, `_emit_narration` |
| Status footer | `app/gm/creation.py` | `CREATION_STATUS_LABELS`, `format_creation_status()` |
| Drift parse | `app/gm/logger.py` | `parse_narration_status_line()` |
| Engine status | `app/gm/bridge.py` → `play/tomb_gm/cli/cmd_core.py` | `status()` → `handle_status`; awaiting derived from roster/characters |
| App FSM state | `app/gm/orchestrator.py` | `CreationState`, `export_creation_state` / `import_creation_state` |
| Session persist | `app/session_state.json` (via `app/ui/app.py`) | `creation_state` — step truth on resume, not in SQLite |
| Engine session | `play/tomb_gm/domain/session.py` | `DEFAULT_PHASE = "preparation"`, hub `32-C` at start |
| CLI suggest | `play/tomb_gm/suggest.py` | `CHARACTER_CREATION` → character-create commands |
| LLM context | `app/gm/context.py` | Injects engine `Awaiting:` into exploration prompts |
| Tests | `app/tests/test_creation_flow.py` | Asserts final `PLAYER_ACTIONS` + `RECEPTION_CHOICE`; no drift silence yet |
| Prior research | `tmp/backlog/runs/app-002-log-creation-drift-events/research-brief.md` | Log-only; assumed compare to engine awaiting |

## Code-path traces

### Engine `awaiting` (coarse, roster-based)

1. Entry: `GameBridge.status()` → `handle_status` (`bridge.py:36–37`, `cmd_core.py:84+`).
2. Active session, not ended, `roster` empty, `characters` empty → `payload["awaiting"] = "CHARACTER_CREATION"` (`cmd_core.py:178–180`).
3. After `character_create` + `roster_set`, roster non-empty → `PLAYER_ACTIONS` (`cmd_core.py:183–184`).
4. No SQLite column or API for per-step creation awaiting; `suggest.py` and tomb_gm tests only know coarse enums.

### App creation footer (granular, step-based)

1. Entry: `_creation_turn_body` → `_compose_creation_narration` (`orchestrator.py:566–647, 507–524`).
2. Footer: `format_creation_status(self.creation)` → `Awaiting: {CREATION_STATUS_LABELS[step]}` (`creation.py:538–541`).
3. LLM flavor stripped of status tags via `strip_llm_status_tags` before compose (`creation.py:532–535`).
4. `WORLD_INTRO` after finalize uses custom footer with `Phase: preparation` + `Awaiting: RECEPTION_CHOICE` (`orchestrator.py:1057–1058`).

### Drift check (current — causes noise)

1. Entry: `_emit_narration` → `_check_creation_drift` (`orchestrator.py:247–249`).
2. Scope: `creation.active` **or** (`awaiting == CHARACTER_CREATION` and empty roster) (`orchestrator.py:172–181`).
3. Parse narration `Phase:` / `Awaiting:` (`logger.py:65–77`).
4. Compare `narrated_awaiting` to `status["awaiting"]` → **always mismatch** when footer is `SKILLS_INPUT` and engine is `CHARACTER_CREATION` (`orchestrator.py:197–203`).
5. Compare `narrated_phase` to `party.phase` when both present (`orchestrator.py:204–205`).
6. Log `creation_drift` via `log_creation_drift` (`orchestrator.py:212–221`).

### Resume / sync

1. `import_creation_state` restores `CreationState` from `session_state.json` (`orchestrator.py:168–170`, `ui/app.py`).
2. `_sync_creation_from_status` re-activates creation when engine still `CHARACTER_CREATION` and no characters (`orchestrator.py:153–161`).
3. Drift scope can run with restored `creation.step` — fix must use `creation.step` when `creation.active`.

## Existing specs & docs

- **Ticket domain spec:** `tmp/app-character-creation-spec.md` — § Status line labels; does not yet document engine vs narration awaiting split.
- **Secondary:** `tmp/app-logging-qa-spec.md` — `creation_drift` when narration disagrees with engine during creation (wording predates granular footers).
- **APP-002:** Logging only; identified compare targets but not the contract bug.
- **APP-007:** Code-owned granular `Awaiting:` footers (intentional).
- **APP-036:** UI badge from engine — should use `creation.step` / `creation_state`, not granular engine awaiting (engine has none).
- **APP-065:** Chips parse `Awaiting:` footer — separate from drift; granular labels are player-facing hazard there, not drift.

## Tests & commands

```bash
# Creation integration (no drift assert today)
python -m pytest app/tests/test_creation_flow.py -q

# Engine status contract
python -m pytest play/tomb_gm/tests/test_campaign_session.py -q

# After fix: grep session JSONL — creation_drift should be absent on golden path
# (manual) cd app && python main.py → new game → complete creation
```

## Risks & unknowns

- **Resume without `creation.active`:** If `creation_state` missing but engine `CHARACTER_CREATION`, drift scope runs but `creation.step` may be stale — drift check should fall back to engine-only or skip awaiting compare until state restored.
- **WORLD_INTRO / post-finalize:** `creation.active` false, `awaiting` `PLAYER_ACTIONS`, footer `RECEPTION_CHOICE` — current compare would drift unless scope excludes post-finalize or expects `RECEPTION_CHOICE` vs `PLAYER_ACTIONS` (separate ticket semantics; test already allows this at end of flow).
- **Engine change anti-pattern:** Adding per-step awaiting to `tomb_gm` would duplicate app FSM, break CLI `suggest` assumptions, and require DB/schema + bridge plumbing — high cost, no engine consumer for `SKILLS_INPUT`.
- **Real drift still needed:** LLM `Phase: delve` / `Awaiting: PLAYER_ACTIONS` while `creation.active` — keep `premature_exploration_phase` and compare narrated awaiting to **expected** label, not engine coarse enum.
- **Session log evidence:** `app/logs/session-2026-05-20.jsonl` cited in ticket not present in workspace snapshot; conclusion follows from code contract, aligned with APP-002 research and ticket examples.

## Raw notes

### `CREATION_STATUS_LABELS` (full map)

| `creation.step` | Narration / expected awaiting |
|-----------------|------------------------------|
| NAME | NAME_INPUT |
| RACE | RACE_INPUT |
| ROLL_STATS | STATS_REVIEW |
| CLASS | CLASS_INPUT |
| SKILLS | SKILLS_INPUT |
| SPELL_SCHOOLS | SPELL_SCHOOLS_INPUT |
| SPELLS | SPELLS_INPUT |
| EQUIPMENT_GOLD | EQUIPMENT_GOLD_CONFIRMATION |
| FINALIZE | FINALIZE |
| WORLD_INTRO | RECEPTION_CHOICE |

### Minimal implementation sketch (orchestrator only)

```python
# When creation.active and narrated_awaiting present:
expected = CREATION_STATUS_LABELS.get(self.creation.step, f"{self.creation.step}_INPUT")
if narrated_awaiting != expected.upper(): reasons.append("awaiting_mismatch")
# Do not compare to status["awaiting"] == "CHARACTER_CREATION" in this branch
```

Optional: when `creation.active`, suppress `phase_mismatch` unless `narrated_phase` in `_PREMATURE_EXPLORE_PHASES` (engine `preparation` is correct during desk creation).

### Acceptance mapping

| Ticket AC | Research recommendation |
|-----------|-------------------------|
| Engine awaiting reflects step **or** drift compares labels | **Prefer label compare** — minimal, no `play/tomb_gm` change |
| No drift every healthy turn | Fix drift comparator, not footer or engine |
| Spec documents contract | `app-character-creation-spec.md` + logging spec changelog |
| APP-057 optional assert | Add `creation_drift` absence or mock log hook in golden-path loop |
