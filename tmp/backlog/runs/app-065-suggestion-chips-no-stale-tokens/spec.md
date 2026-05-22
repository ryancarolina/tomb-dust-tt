# Spec: app-065-suggestion-chips-no-stale-tokens

**Status:** draft (r2 — QA spec round 1 fixes)
**backlog_ticket:** APP-065
**ticket_path:** tmp/backlog/app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md
**domain_spec:** tmp/app-pygame-ui-spec.md
**registry_gap:** false
**Domain specs touched:** tmp/app-pygame-ui-spec.md

## Problem

Suggestion chips are built by regex-scraping GM narration for `[…Awaiting: …]` and only updating when the parse is non-empty. That causes two failures:

1. **Stale chips** — When post-finalize narration omits a bracketed `Awaiting:` line, `_extract_suggestions` returns `[]` but the UI never calls `set_suggestions([])`, so prior chips (e.g. `EQUIPMENT_CONFIRMATION`) remain clickable.
2. **Internal tokens as chips** — Any parsed `Awaiting:` value becomes both label and submit text, including FSM labels (`EQUIPMENT_CONFIRMATION`, `PLAYER_ACTIONS`, `SKILLS_INPUT`) unsuitable as player input.

Batch mate **APP-073** cleans creation narration footers but does not fix chip source-of-truth. APP-065 must not depend on narration cleanliness.

## Goals

- Every turn after `process_turn`, refresh chips from a **code-owned player map** (or empty list).
- Chips are **player-facing phrases only** — never raw `Awaiting:` / `CREATION_STATUS_LABELS` / engine enum strings.
- Equipment confirm step offers actionable chips: confirm phrase matches `is_equipment_confirm`; objection phrase triggers re-present via **non-confirm** (see R3).
- Startup `load game` / `new game` behavior preserved.
- Long-form behavior documented in `tmp/app-pygame-ui-spec.md` (Input panel).

## Non-goals

- Parsing `play/tomb_gm/suggest.py` `prompts` (GM/operator hints, not player chips).
- Chips for every creation step (race/class/skills remain free-text unless explicitly mapped).
- Combat action chips (`ATTACK`, `CAST`) — default empty during `COMBAT_TURN` / `PLAYER_ACTIONS`.
- Changing narration footer format (APP-007 / APP-073).
- `input_box.py` label/submit split unless a step needs display ≠ submit (v1: same string).

## Requirements

### R1: Always clear stale chips

After each `_process_turn` completes (success **or** exception), queue suggestion refresh **unconditionally** in the same code path as status/map updates (or in a `finally` block before early return):

```python
suggestions = self._orchestrator.get_player_suggestions()
self._ui_queue.put(("suggestions", suggestions))
```

- Empty list `[]` must reach `InputBox.set_suggestions` so prior chips disappear.
- Remove the `if suggestions:` guard and stop using `_extract_suggestions(narration)` as the turn-loop source.
- On turn exception (`app/ui/app.py` except path ~319–322), still queue refresh (typically `[]` or current engine map) so equipment/startup chips do not persist beside the error line.
- Startup init path (`_init_orchestrator`) may still seed chips once; first turn refresh overwrites via R2.

**Acceptance criteria**

- [ ] Mock or integration test: narration with no `Awaiting:` after equipment confirm → `input_box.suggestions == []` (or mapped post-world-intro chips if step maps them).
- [ ] Manual Bumpy repro: confirm with “ready” → stale `EQUIPMENT_*` chip gone.
- [ ] Unit or integration test: when `process_turn` raises, UI queue still receives `("suggestions", …)` (not left at prior step’s chips).

### R2: Code-owned source of truth (not narration)

Introduce a single builder used by the UI turn loop:

| Layer | Responsibility |
|-------|----------------|
| `app/ui/suggestions.py` (recommended) or `app/gm/ui_suggestions.py` | `PLAYER_SUGGESTIONS_BY_CREATION_STEP`, `PLAYER_SUGGESTIONS_BY_AWAITING`, `is_blocked_chip_token()`, `build_player_suggestions(creation_step, engine_awaiting, has_save)` |
| `app/gm/orchestrator.py` | `get_player_suggestions() -> list[str]` — reads `self.creation.step` **only when** `creation.active`; otherwise `bridge.status()["awaiting"]` only (never stale `creation.step` after finalize). Includes `bridge.has_save()` for startup. |
| `app/ui/app.py` | Call orchestrator every turn; delete or hard-deprecate `_extract_suggestions` |

**Lookup order**

1. If `creation.active` and `creation.step` has a map entry → use that list (may be `[]`).
2. Else if coarse `status["awaiting"]` has a map entry → use that list.
3. Else → `[]` (never fall back to narration scrape).

**Post-finalize / inactive creation:** When `creation.active` is false, **ignore** `creation.step` entirely — even if engine `awaiting` is still `CHARACTER_CREATION` (resume desync) or `creation.step` is stale (e.g. `WORLD_INTRO` after finalize sets `active=False` at `orchestrator.py` ~1196–1197). Chips come from engine `awaiting` only (typically `PLAYER_ACTIONS` → `[]`), never from a stale step map.

**Acceptance criteria**

- [ ] No regex on narration for chip text in `app/ui/app.py` turn path.
- [ ] `get_player_suggestions()` does not read `narration` or `parse_narration_status_line`.
- [ ] After finalize (`creation.active == false`), equipment chips never reappear from stale `creation.step == EQUIPMENT_GOLD`.

### R3: Player-facing map (keys = `creation.step`, not `Awaiting` labels)

Maps use **`CreationState.step`** values (`NAME`, `RACE`, …) from `CREATION_STEPS`, **not** `CREATION_STATUS_LABELS` values (`EQUIPMENT_GOLD_CONFIRMATION`, etc.).

| `creation.step` | Chips (max 4) | Notes |
|-----------------|---------------|-------|
| `NAME` | `[]` | Free-text name |
| `RACE` | `[]` | Type race name |
| `ROLL_STATS` | `[]` | Code tables drive choices |
| `CLASS` | `[]` | Type class name |
| `SKILLS` | `[]` | Type skill list |
| `SPELL_SCHOOLS` | `[]` | Type schools |
| `SPELLS` | `[]` | Type spells |
| `EQUIPMENT_GOLD` | `Yes, confirm`, `I need different gear` | Confirm: must match `is_equipment_confirm` (`EQUIPMENT_CONFIRM_RE`). Objection: must **not** match confirm — handler re-presents kit via `not is_equipment_confirm` (`orchestrator.py` ~1004–1008); **does not** require `EQUIPMENT_OBJECTION_RE` match |
| `FINALIZE` | `[]` | Auto-advance |
| `WORLD_INTRO` | `[]` | v1: no chips; map travel is click-driven (APP-063) |

**Coarse engine `awaiting` map** (non-creation or fallback)

| `awaiting` | Chips |
|------------|-------|
| `SETUP` | `new game`; plus `load game` when `has_save` |
| `SESSION_ENDED` | `new game` |
| `CHARACTER_CREATION` | When `creation.active`: same as step 1 (creation.step map). When not active: `[]` — never delegate to stale `creation.step` |
| `ROSTER_SETUP`, `PLAYER_ACTIONS`, `COMBAT_TURN`, `DYING`, `DOWNED`, `BLOCKED`, `HUMAN_GATE` | `[]` |

**Acceptance criteria**

- [ ] `EQUIPMENT_GOLD` never exposes `EQUIPMENT_GOLD_CONFIRMATION`, `EQUIPMENT_CONFIRMATION`, or other `UPPER_SNAKE_CASE` tokens as chips.
- [ ] Clicking `Yes, confirm` submits that literal string (matches `EQUIPMENT_CONFIRM_RE` / `is_equipment_confirm`).
- [ ] Clicking `I need different gear` submits that literal string; orchestrator re-presents equipment because `not is_equipment_confirm(text)` — **do not** assert `is_equipment_objection("I need different gear")` or extend `EQUIPMENT_OBJECTION_RE` for this ticket.

### R4: Blocklist (defense in depth)

Even if a future path passes strings into `set_suggestions`, filter through `is_blocked_chip_token(text)`:

**Always block**

- Any string matching `^[A-Z][A-Z0-9_]*$` with length ≥ 3 (internal `UPPER_SNAKE_CASE` labels).
- Suffix patterns: `*_INPUT`, `*_CONFIRMATION`.
- Known engine / footer enums: `SETUP`, `SESSION_ENDED`, `CHARACTER_CREATION`, `ROSTER_SETUP`, `PLAYER_ACTIONS`, `COMBAT_TURN`, `DYING`, `DOWNED`, `BLOCKED`, `HUMAN_GATE`, `RECEPTION_CHOICE`, and every value in `CREATION_STATUS_LABELS.values()`.
- Raw `Awaiting:` scrape results (if any legacy call remains).

**Always allow** (lowercase player phrases)

- `load game`, `new game`, `Yes, confirm`, `I need different gear`, and other curated map entries.

**Acceptance criteria**

- [ ] Unit test: `is_blocked_chip_token("EQUIPMENT_CONFIRMATION")` → true; `is_blocked_chip_token("Yes, confirm")` → false.
- [ ] Unit test: `build_player_suggestions("EQUIPMENT_GOLD", …)` never returns blocked tokens.

### R5: Click submits player text, not tokens

`input_box.py` behavior unchanged for v1: displayed label == submitted string. Chips must already be player phrases from R3.

**Acceptance criteria**

- [ ] Clicking equipment chip does not send `EQUIPMENT_GOLD_CONFIRMATION` or similar.

### R6: Domain spec sync

Update `tmp/app-pygame-ui-spec.md` Input section with source-of-truth, maps, blocklist, always-clear rule (see domain spec — PM delivers in same change set).

**Acceptance criteria**

- [ ] Ticket AC “Domain spec documents chip source-of-truth and blocklist rules” satisfied in domain spec, not only this run `spec.md`.

## Batch coordination (APP-073)

| Topic | Rule |
|-------|------|
| Impl order | Prefer **APP-073 before APP-065** at Stage 4 (batch board wave 1 parallel, impl preference documented). |
| Independence | APP-065 chips **must not** parse narration; APP-073 may leave footers with bare `Awaiting: RECEPTION_CHOICE` — chips still correct via map. |
| Vocabulary | Chip map keys off `creation.step`; APP-073 canon footers use `CREATION_STATUS_LABELS` — different layers, no duplication of label strings in chips. |

## Test plan

```bash
# New module tests (add app/tests/test_ui_suggestions.py — allowed under app/tests per logging-qa / ticket test AC)
python -m pytest app/tests/test_ui_suggestions.py -q

# Regression — narration Awaiting asserts unchanged
python -m pytest app/tests/test_creation_flow.py app/tests/test_session_resume_failure.py -q
```

**Suggested unit cases**

- `build_player_suggestions(creation_step="EQUIPMENT_GOLD", creation_active=True, …)` → `["Yes, confirm", "I need different gear"]`.
- `build_player_suggestions(creation_step="EQUIPMENT_GOLD", creation_active=False, engine_awaiting="CHARACTER_CREATION", …)` → `[]` (inactive creation ignores step map).
- `is_equipment_confirm("Yes, confirm")` → true; `is_equipment_confirm("I need different gear")` → false (objection chip path).
- `build_player_suggestions(creation_step="NAME", …)` → `[]`.
- `build_player_suggestions(engine_awaiting="SETUP", has_save=True)` → `["load game", "new game"]` (order per existing startup UX).
- Blocklist rejects `SKILLS_INPUT`, `PLAYER_ACTIONS`, `COMBAT_TURN`.
- App turn path: patch `get_player_suggestions` returning `[]` → verify queue delivers empty list (no `if suggestions` skip).

## Human playtest hints (for Stage 7)

- New game → reach equipment summary → chips show **Yes, confirm** / **I need different gear**, not `EQUIPMENT_*` token.
- Confirm with typed “ready” → post-finalize narration → **no** stale equipment chip.
- Startup with save → **load game** / **new game**; without save → **new game** only.
- Click stale-token repro from ticket → should be impossible after fix.

## Affected paths

_Must match ticket **Expected files**._

- `app/ui/app.py` — turn-loop suggestion refresh; remove narration scrape
- `app/ui/panels/input_box.py` — only if label ≠ submit required (unlikely v1)
- `app/gm/orchestrator.py` — `get_player_suggestions()`
- `app/ui/suggestions.py` — player chip maps, blocklist, builder (under `app/ui/**`, domain-owned)
- `app/tests/test_ui_suggestions.py` — unit tests for builder, blocklist, inactive-creation guard
- `tmp/app-pygame-ui-spec.md` — Input panel chip contract

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial PM draft from research-brief; batch APP-073 noted |
| 2026-05-20 | R2: QA spec round 1 — Expected files, equipment non-confirm path, inactive creation lookup, error-path refresh |
