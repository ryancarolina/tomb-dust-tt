# Spec: APP-066-sync-engine-awaiting-with-creation-step

**Status:** draft  
**backlog_ticket:** APP-066  
**ticket_path:** tmp/backlog/app-066-sync-engine-awaiting-with-creation-step.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**registry_gap:** false  
**Domain specs touched:** `tmp/app-character-creation-spec.md`, `tmp/app-logging-qa-spec.md`

## Problem

During character creation, `bridge.status()["awaiting"]` stays `CHARACTER_CREATION` while narration footers use granular labels (`SKILLS_INPUT`, `SPELL_SCHOOLS_INPUT`, etc.). APP-002’s `_check_creation_drift()` compares narrated `Awaiting:` to engine `awaiting`, so **every healthy creation turn** logs `creation_drift` with `awaiting_mismatch` — noise that hides real regressions (LLM wrong phase, premature PRE_DELVE, footer vs FSM step).

## Goals

- Align drift detection with the **intentional** two-layer awaiting model (coarse engine vs granular app).
- Stop `creation_drift` on golden-path creation turns when footers match `creation.step`.
- Document engine vs narration awaiting in the character-creation domain spec; document drift semantics in the logging spec.

## Non-goals

- Per-step `awaiting` in `play/tomb_gm` / SQLite (duplicates app FSM; breaks CLI `suggest`).
- Changing `format_creation_status()` labels or engine `CHARACTER_CREATION` coarse enum.
- Fixing `WORLD_INTRO` / `RECEPTION_CHOICE` vs `PLAYER_ACTIONS` post-finalize mismatch (out of scope unless drift scope already excludes it).
- UI badge work (APP-036) — spec notes engine awaiting is not granular.

## Requirements

### R1: Two-layer awaiting contract (documented)

**Behavior (no code change required for docs-only PM pass; implementation in Dev):**

| Layer | Owner | Source | Values during desk creation |
|-------|--------|--------|----------------------------|
| **Engine** | `play/tomb_gm` via `GameBridge.status()` | `handle_status` when roster empty, no characters | `CHARACTER_CREATION` for entire creation until `character_create` + `roster_set` |
| **App narration / drift expected** | `app/gm/creation.py` | `CREATION_STATUS_LABELS[creation.step]` via `format_creation_status()` | `NAME_INPUT`, `SKILLS_INPUT`, … per FSM step |

**Truth for player-facing step:** `CreationState.step` (+ `session_state.json` `creation_state` on resume). UI chips and drift **expected** label must use this map, not engine `awaiting`.

Full label map: see [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) § Awaiting contract (engine vs app).

### R2: Drift check compares narrated awaiting to expected label

**Acceptance criteria**

- [ ] When `creation.active` and narration includes `Awaiting:`, `_check_creation_drift` compares `narrated_awaiting` to `CREATION_STATUS_LABELS[self.creation.step]` (uppercase), **not** to `status["awaiting"]`.
- [ ] Mismatch vs expected label still emits `awaiting_mismatch` (real drift: wrong footer, LLM tag leak, step/label desync).
- [ ] When `creation.active` and `narrated_awaiting` matches expected label, **do not** add `awaiting_mismatch` solely because engine is `CHARACTER_CREATION`.

**Fallback:** If `creation.active` but step unknown, use `f"{step}_INPUT"` same as `format_creation_status()`.

### R3: Phase drift during creation

**Acceptance criteria**

- [ ] While `creation.active`, do **not** emit `phase_mismatch` when narrated phase is absent and engine `party.phase` is `preparation` (code footers omit `Phase:` except post-finalize `WORLD_INTRO`).
- [ ] Keep `premature_exploration_phase` when `creation.active` and narrated phase is in `_PREMATURE_EXPLORE_PHASES` (existing guard).
- [ ] Optional (recommended): only compare `narrated_phase` to `engine_phase` when narrated phase is present **and** not a benign desk-creation omission — or when narrated phase is in premature-explore set.

### R4: Drift scope without `creation.active`

**Acceptance criteria**

- [ ] `_creation_drift_scope()` unchanged: `creation.active` OR engine `CHARACTER_CREATION` with empty roster.
- [ ] When scope true but `creation.active` false (resume edge: engine still `CHARACTER_CREATION`, no restored `creation_state`): skip awaiting compare until `import_creation_state` restores step, or compare only if `creation.step` is trustworthy.

### R5: Logging payload clarity (optional)

**Acceptance criteria**

- [ ] `creation_drift` JSONL may include `expected_awaiting` (and keep `awaiting` as engine value) for QA grep — not required for AC if reasons are sufficient.

### R6: Tests

**Acceptance criteria**

- [ ] `python -m pytest app/tests/test_creation_flow.py -q` stays green.
- [ ] Optional (ticket): assert no `creation_drift` events on golden-path mock run, or unit test `_check_creation_drift` with fixed narration + `creation.step`.

## Test plan

```bash
python -m pytest app/tests/test_creation_flow.py -q
python -m pytest play/tomb_gm/tests/test_campaign_session.py -q
```

After implementation: replay `new game` → full creation; grep `app/logs/session-*.jsonl` — no `creation_drift` with `awaiting_mismatch` on turns where footer matches step.

## Human playtest hints (for Stage 7)

- New game through equipment confirm: watch JSONL — `creation_step` each turn, **no** `creation_drift` every line.
- Force wrong step (if debug): footer `Awaiting: CLASS_INPUT` while on `SKILLS` — should log `creation_drift` with `awaiting_mismatch`.
- After finalize: `RECEPTION_CHOICE` footer with engine `PLAYER_ACTIONS` — confirm scope/reasons do not spam false positives (existing WORLD_INTRO behavior).

## Affected paths

Must match ticket **Expected files**:

- `app/gm/orchestrator.py` — `_check_creation_drift`, import `CREATION_STATUS_LABELS`
- `tmp/app-character-creation-spec.md` — § Awaiting contract
- `tmp/app-logging-qa-spec.md` — `creation_drift` semantics
- _(optional)_ `app/tests/test_creation_flow.py` — drift silence assert

**Not in scope:** `app/gm/bridge.py`, `play/tomb_gm/` engine awaiting logic (remain coarse).

## Pointers (source of truth)

| Topic | Location |
|-------|----------|
| Awaiting contract & label map | [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) § Awaiting contract (engine vs app) |
| `creation_drift` event semantics | [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) § `creation_drift` |
| Research traces & minimal fix | [`research-brief.md`](research-brief.md) |
| Engine `CHARACTER_CREATION` | `play/tomb_gm/cli/cmd_core.py` `handle_status` (~178–184) |
| Footer formatter | `app/gm/creation.py` `CREATION_STATUS_LABELS`, `format_creation_status()` |
| Drift detector | `app/gm/orchestrator.py` `_creation_drift_scope`, `_check_creation_drift` |

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial PM draft (APP-066) |
