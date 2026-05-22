# Implementation Plan: APP-065-suggestion-chips-no-stale-tokens

**Status:** draft  
**backlog_ticket:** APP-065  
**ticket_path:** tmp/backlog/app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md  
**domain_spec:** tmp/app-pygame-ui-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Replace narration regex scraping with a **code-owned player chip builder** and **unconditional turn-loop refresh**. Two root causes from research:

1. **Stale chips** — `app/ui/app.py:_process_turn` L315–317 only queues when `_extract_suggestions(narration)` is non-empty.
2. **Internal tokens** — parsed `Awaiting:` values (e.g. `EQUIPMENT_CONFIRMATION`) become chip labels and submit text.

Fix in three layers (spec R1–R6):

1. **New `app/ui/suggestions.py`** — curated maps keyed by `creation.step` / engine `awaiting`, plus `is_blocked_chip_token()` defense-in-depth filter.
2. **`Orchestrator.get_player_suggestions()`** — reads `self.creation` (only when `creation.active`) + `bridge.status()["awaiting"]` + `bridge.has_save()`; never reads narration.
3. **`app/ui/app.py` turn loop** — call orchestrator every turn (success **and** exception); delete `_extract_suggestions` from turn path.

**v1 constraints:** `input_box.py` unchanged (label == submit). Startup `_init_orchestrator` may keep hardcoded seed; first turn refresh overwrites via builder. **No** parsing `play/tomb_gm/suggest.py`. Domain spec already drafted by PM (r2); append changelog date on ticket close only.

**Batch note:** Prefer APP-073 impl first; APP-065 chips must work regardless of footer/narration shape.

---

## Code-path traces (current → planned)

### Flow A — Turn loop (stale clear + new source)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `app.py:_submit` | L263–268: spawn `_process_turn` thread | unchanged |
| 2 | `app.py:_process_turn` | L289: `orchestrator.process_turn(text)` | unchanged |
| 3 | same | L315–317: `suggestions = self._extract_suggestions(narration)`; `if suggestions: put(...)` | **R1/R2:** `suggestions = self._orchestrator.get_player_suggestions()`; **always** `put(("suggestions", suggestions))` |
| 4 | same | L319–322: `except` → error line → `return` (no chip refresh) | **R1:** `_queue_turn_suggestions` in `finally`; **retain** `return` in `except` (no TTS on error) |
| 5 | `app.py:_process_ui_queue` | L190–191: `set_suggestions(data)` | unchanged — receives `[]` and clears widget |
| 6 | `input_box.py:set_suggestions` | L32–33: `self.suggestions = suggestions[:4]` | unchanged |

**Planned `_process_turn` suggestion refresh (pseudocode):**

```python
def _queue_turn_suggestions(self, turn_id: int) -> None:
    """Testable helper — unconditional refresh; may queue []."""
    if turn_id != self._current_turn_id or not self._orchestrator:
        return
    self._ui_queue.put(
        ("suggestions", self._orchestrator.get_player_suggestions())
    )

def _process_turn(self, text, turn_id):
    narration = None
    try:
        ...
        narration = self._orchestrator.process_turn(text)
        ...  # status, map_update (unchanged; remove L315–317 scrape)
    except Exception as exc:
        if turn_id == self._current_turn_id:
            self._ui_queue.put(("error", str(exc)))
        return  # preserve current behavior: no TTS / turn_idle on error (finally still runs)
    finally:
        self._queue_turn_suggestions(turn_id)
        if self._orchestrator and narration is not None and turn_id == self._current_turn_id:
            self._save_session()

    if turn_id != self._current_turn_id:
        return
    ...  # TTS / turn_idle (unchanged — unreachable after except return)
```

- **`return` in `except` is mandatory** — current code L322 returns before TTS/`turn_idle`; Python runs `finally` first, so `_queue_turn_suggestions` still clears stale chips on error without starting narration audio.
- Stale `turn_id` early returns **inside** `try` (before `process_turn`) should **not** refresh — helper guards on `turn_id == self._current_turn_id`.
- Orchestrator-not-init path: helper no-ops (no orchestrator).

### Flow B — Narration scrape (remove)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `app.py:_extract_suggestions` | L339–348: regex `\[.*?Awaiting:\s*(.+?)\]` | **Delete** method (or leave unused with deprecation comment — prefer delete) |
| 2 | Turn path | calls `_extract_suggestions(narration)` | **Remove** — zero regex on narration in turn path |

**Why scrape fails (ticket repro):**

| Footer shape | Example | Current parse | After fix |
|--------------|---------|---------------|-----------|
| LLM bracket line | `[Location: … \| Awaiting: EQUIPMENT_CONFIRMATION]` | Bad chip | Map → `Yes, confirm` / `I need different gear` at `EQUIPMENT_GOLD` |
| Code two-line finalize | `[Location: 32-C \| …]\nAwaiting: RECEPTION_CHOICE` | `[]` → stale chip | `get_player_suggestions()` → `[]` (inactive creation, `PLAYER_ACTIONS` unmapped) |
| Bare code footer | `Awaiting: SKILLS_INPUT` | `[]` | Step map → `[]` |

### Flow C — Builder lookup (new)

| Step | File:symbol | Action |
|------|-------------|--------|
| 1 | `suggestions.py:build_player_suggestions` | Accept `creation_step`, `creation_active`, `engine_awaiting`, `has_save` |
| 2 | same | **If** `creation_active` **and** `creation_step in PLAYER_SUGGESTIONS_BY_CREATION_STEP` → return filtered map value (may be `[]`) |
| 3 | same | **Elif** `engine_awaiting == "SETUP"` → `["load game", "new game"]` if `has_save` else `["new game"]` |
| 4 | same | **Elif** `engine_awaiting == "SESSION_ENDED"` → `["new game"]` |
| 5 | same | **Elif** `engine_awaiting == "CHARACTER_CREATION"` and not `creation_active` → `[]` (resume desync guard) |
| 6 | same | **Elif** `engine_awaiting in PLAYER_SUGGESTIONS_BY_AWAITING` → filtered list |
| 7 | same | **Else** → `[]` |
| 8 | same | Run each candidate through `is_blocked_chip_token`; cap at 4 |
| 9 | `orchestrator.py:get_player_suggestions` | Gather `creation.active`, `creation.step`, `bridge.status()["awaiting"]`, `bridge.has_save()`; delegate to builder |
| 10 | `app.py:_process_turn` | Call `get_player_suggestions()` in `finally` |

**Post-finalize guard (`orchestrator.py:_auto_finalize` L1196–1197):**

- Sets `creation.active = False`, `creation.step = "WORLD_INTRO"`.
- Builder must **ignore** `creation.step` when `creation_active` is false → equipment chips never return from stale `EQUIPMENT_GOLD` step.

### Flow D — Equipment confirm chips (handler alignment)

| Step | File:symbol | Current | Planned chip submit |
|------|-------------|---------|---------------------|
| 1 | `creation.py:EQUIPMENT_CONFIRM_RE` | L93–97 | `"Yes, confirm"` matches (word `confirm`) |
| 2 | `orchestrator.py:_handle_creation_input` | L1004–1008: `if is_equipment_objection(...) or not is_equipment_confirm(...):` re-present | `"I need different gear"` → `not is_equipment_confirm` → re-present kit (no `EQUIPMENT_OBJECTION_RE` required) |
| 3 | Chip map | — | `EQUIPMENT_GOLD` → `["Yes, confirm", "I need different gear"]` |

### Flow E — Startup (preserve)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `app.py:_init_orchestrator` | L137–146: hardcoded `load game` / `new game` | **Keep** (spec allows seed once) |
| 2 | First `_process_turn` | overwrites via scrape today | overwrites via `get_player_suggestions()` — should match SETUP map when engine awaiting is SETUP |

Optional DRY (non-blocking): replace L141/L146 hardcode with `get_player_suggestions()` after orchestrator init if `awaiting == SETUP` — only if init status is reliable; otherwise keep hardcode.

---

## Task breakdown

### 1. Create `app/ui/suggestions.py`

#### 1.1 Constants

```python
PLAYER_SUGGESTIONS_BY_CREATION_STEP: dict[str, list[str]] = {
    "NAME": [],
    "RACE": [],
    "ROLL_STATS": [],
    "CLASS": [],
    "SKILLS": [],
    "SPELL_SCHOOLS": [],
    "SPELLS": [],
    "EQUIPMENT_GOLD": ["Yes, confirm", "I need different gear"],
    "FINALIZE": [],
    "WORLD_INTRO": [],
}

PLAYER_SUGGESTIONS_BY_AWAITING: dict[str, list[str]] = {
    "SETUP": ["new game"],  # prepend "load game" when has_save in builder
    "SESSION_ENDED": ["new game"],
    "CHARACTER_CREATION": [],  # only used when inactive (guard in builder)
    "ROSTER_SETUP": [],
    "PLAYER_ACTIONS": [],
    "COMBAT_TURN": [],
    "DYING": [],
    "DOWNED": [],
    "BLOCKED": [],
    "HUMAN_GATE": [],
}
```

Import `CREATION_STATUS_LABELS` from `gm.creation` for blocklist enum set.

#### 1.2 `is_blocked_chip_token(text: str) -> bool`

Block if any:

- Matches `^[A-Z][A-Z0-9_]{2,}$` (UPPER_SNAKE_CASE, len ≥ 3).
- Ends with `_INPUT` or `_CONFIRMATION`.
- In frozen set: engine enums + all `CREATION_STATUS_LABELS.values()` + `RECEPTION_CHOICE`.

Allow curated lowercase phrases (`load game`, `new game`, `Yes, confirm`, `I need different gear`).

#### 1.3 `build_player_suggestions(...) -> list[str]`

Implement lookup order from spec R2/R3. SETUP row: when `has_save`, return `["load game", "new game"]` (preserve existing startup order per domain spec).

Apply blocklist filter to final list; return `[:4]`.

#### 1.4 `filter_player_suggestions(candidates: list[str]) -> list[str]`

Optional small helper used by builder — drop blocked tokens, preserve order, cap 4.

---

### 2. Add `Orchestrator.get_player_suggestions()` — `app/gm/orchestrator.py`

Place near `get_status()` (after L102):

```python
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
```

**Import path:** `ui.suggestions` matches `app/` on `sys.path` when running `main.py` and pytest (`conftest.py` adds `APP` to path). Use same style as other `ui.*` imports if any exist; otherwise `from ui.suggestions import ...` from orchestrator (verify with existing imports in orchestrator — may use relative or absolute under `gm`).

**Verify import:** Check how `app/gm/orchestrator.py` imports app modules today; adjust to `from ui.suggestions import build_player_suggestions` (APP root on path) or `from app.ui.suggestions` — match repo convention.

---

### 3. Rewire turn loop — `app/ui/app.py`

#### 3.1 Replace L315–317 and extract helper

Remove `_extract_suggestions` call and `if suggestions:` guard. Add `_queue_turn_suggestions(turn_id)` per Flow A; call from `finally` only (not success path inline).

#### 3.2 Restructure exception + refresh — L319–325

Extract `_queue_turn_suggestions(turn_id)` (see Flow A) and call from `finally`. Ensure:

- **`except` keeps `return` after error enqueue** (L322 today) — do not fall through to TTS/`turn_idle` on failed turns; `finally` runs before the return.
- Exception after partial `process_turn` still refreshes from current orchestrator state via `_queue_turn_suggestions`.
- `_save_session()` remains in `finally` only when `narration is not None`.

#### 3.3 Delete `_extract_suggestions` — L339–348

Remove dead code; grep confirms no other callers.

---

### 4. Tests — `app/tests/test_ui_suggestions.py` (new)

Use `orchestrator` fixture from `conftest.py`. No pygame / full `App` required for primary coverage.

| Test | Assert |
|------|--------|
| `test_blocked_internal_tokens` | `is_blocked_chip_token("EQUIPMENT_CONFIRMATION")` True; `"Yes, confirm"` False; `SKILLS_INPUT`, `PLAYER_ACTIONS` blocked |
| `test_equipment_gold_active_chips` | `build_player_suggestions(..., creation_step="EQUIPMENT_GOLD", creation_active=True)` → confirm + gear strings; no UPPER_SNAKE |
| `test_equipment_confirm_regex_alignment` | `is_equipment_confirm("Yes, confirm")`; `not is_equipment_confirm("I need different gear")` |
| `test_inactive_creation_ignores_step` | `creation_step="EQUIPMENT_GOLD", creation_active=False, engine_awaiting="CHARACTER_CREATION"` → `[]` |
| `test_post_finalize_orchestrator` | Drive orchestrator to `WORLD_INTRO` with `creation.active is False`; `get_player_suggestions() == []` |
| `test_setup_has_save` | `engine_awaiting="SETUP", has_save=True` → `["load game", "new game"]` |
| `test_setup_no_save` | → `["new game"]` |
| `test_name_step_no_chips` | `creation_step="NAME", creation_active=True` → `[]` |
| `test_builder_never_returns_blocked` | Parametrize known bad tokens through filter |
| `test_queue_turn_suggestions_empty_list_always_put` | **R1 / spec test plan:** stub `App` with queue spy + mock orchestrator where `get_player_suggestions()` returns `[]`; call `_queue_turn_suggestions(turn_id)`; assert queue receives exactly `("suggestions", [])` (no `if suggestions:` gate) |
| `test_process_turn_exception_refreshes_suggestions` | **R1 AC:** minimal `App` stub (no pygame loop): mock `_orchestrator.process_turn` to raise; set `_current_turn_id`; run `_process_turn("x", turn_id)`; assert queue contains `("error", …)` **and** `("suggestions", …)` (typically `[]`) — stale chips would not refresh without `finally` helper |

**Post-finalize integration:** After golden-path `"yes"` at equipment in `test_creation_flow.py` inputs, optionally add assertion in new test file (not modifying creation_flow unless minimal):

```python
def test_get_player_suggestions_empty_after_finalize(orchestrator, monkeypatch):
    # reuse FIXED_ROLL + INPUTS pattern from test_creation_flow
    ...
    assert orchestrator.creation.active is False
    assert orchestrator.get_player_suggestions() == []
```

**App turn-path testing approach (no full pygame):**

- Extract `_queue_turn_suggestions(turn_id)` on `App` — unit-testable without display init.
- `test_queue_turn_suggestions_empty_list_always_put` covers spec “patch `get_player_suggestions` returning `[]` → verify queue” (PLAN-003).
- `test_process_turn_exception_refreshes_suggestions` covers spec R1 exception-path AC (PLAN-001); uses `queue.Queue` spy and mocked orchestrator only.

---

### 5. Domain spec sync — `tmp/app-pygame-ui-spec.md`

PM r2 already contains § Suggestion chips (source-of-truth, maps, blocklist, always refresh). On ticket close:

- Mark APP-065 checklist item `[x]`.
- Append changelog row: `2026-05-20 | APP-065: code-owned chips, blocklist, always-clear (impl)`.

No behavioral doc rewrite unless impl diverges from PM draft.

---

### 6. Out of scope (do not touch)

- `app/ui/panels/input_box.py` — v1 label == submit
- `play/tomb_gm/suggest.py` — GM hints only
- `app/gm/creation.py` footer / `CREATION_STATUS_LABELS` — APP-007/073
- Narration footer format in `_auto_finalize` L1221

---

## Files (must ⊆ ticket Expected files)

| File | Change |
|------|--------|
| `app/ui/suggestions.py` | **New** — maps, blocklist, `build_player_suggestions` |
| `app/gm/orchestrator.py` | **Add** `get_player_suggestions()` |
| `app/ui/app.py` | Turn-loop refresh; remove `_extract_suggestions` |
| `app/tests/test_ui_suggestions.py` | **New** — unit + orchestrator integration tests |
| `tmp/app-pygame-ui-spec.md` | Changelog + checklist on close |
| `app/ui/panels/input_box.py` | **No change** (v1) |

---

## Tests

| Step | Command | Expected |
|------|---------|----------|
| 1 | `python -m pytest app/tests/test_ui_suggestions.py -q` | All new tests green |
| 2 | `python -m pytest app/tests/test_creation_flow.py app/tests/test_session_resume_failure.py -q` | Regression green (narration `Awaiting:` asserts unchanged) |
| 3 | `python -m pytest app/tests/test_ui_suggestions.py::test_queue_turn_suggestions_empty_list_always_put app/tests/test_ui_suggestions.py::test_process_turn_exception_refreshes_suggestions -q` | R1 exception + empty-list queue automation green |
| 4 | Manual Bumpy repro | Equipment chips player-facing; post-finalize no stale token; click objection re-presents kit |

---

## Rollback / flags

- Revert `app/ui/suggestions.py` + orchestrator method + app.py turn change.
- No feature flags. Behavior change is immediate on deploy.

---

## Open questions

| # | Question | Default if unresolved |
|---|----------|----------------------|
| 1 | Unify startup hardcode with `get_player_suggestions()`? | Keep hardcode (spec allows) |
| 2 | `orchestrator` import path for `ui.suggestions` | Match pytest + `main.py` path setup; verify in impl |
| 3 | Pygame-less test for `_process_turn` finally block | **Resolved:** extract `_queue_turn_suggestions`; add `test_queue_turn_suggestions_empty_list_always_put` + `test_process_turn_exception_refreshes_suggestions` (§4) |

---

## Acceptance criteria mapping

| Ticket AC | Plan task |
|-----------|-----------|
| Empty extract → clear chips | §3 `_queue_turn_suggestions` + `finally`; `test_queue_turn_suggestions_empty_list_always_put`; post-finalize test |
| Never show internal tokens | §1 blocklist + remove scrape |
| Player-facing actions only | §1 maps + §2 orchestrator |
| Equipment confirm examples | §1 `EQUIPMENT_GOLD` map; §4 regex alignment test |
| Startup load/new game | §1 SETUP map; preserve §E startup seed |
| Click submits label not token | §1 player phrases; no `input_box` change |
| Exception path clears stale chips | §3.2 `return` in `except` + `finally` refresh; `test_process_turn_exception_refreshes_suggestions` |
| Domain spec documents rules | §5 PM draft already done; checklist on close |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial Dev plan from spec r2 + qa-spec-pass |
| 2026-05-20 | r2: PLAN-001 — `_queue_turn_suggestions` + exception-path test; PLAN-002 — explicit `return` in `except`; PLAN-003 — empty-list queue test; open Q3 resolved |
