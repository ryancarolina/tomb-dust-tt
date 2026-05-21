# Implementation Plan: APP-019-surface-new-game-errors

**Status:** draft (Dev plan phase)  
**backlog_ticket:** APP-019  
**ticket_path:** tmp/backlog/app-019-surface-new-game-failure-errors.md  
**domain_spec:** tmp/app-session-persistence-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Summary

Replace silent or terse `setup_new_game` failures across **three contexts** (explicit **`new game`**, combat death restart, resume **`run_ended`**) with **mapped cause + retry copy**, dual JSONL (`error` + `gm_narration` via existing **`_emit_recovery_narration`**), and **`[Awaiting: new game]`** footers. Context **B** requires a new **`already_emitted`** return contract so combat callers do not double-emit via `_emit_narration`. Add `app/tests/test_setup_new_game_failure.py` (T-019a–f). R6 UI status bar is **optional** — close on orchestrator + tests if manual smoke is clear.

---

## Root cause (current)

### Context A — command (`process_turn` ~535–539)

```535:539:app/gm/orchestrator.py
        if lower in ("new game", "start", "new"):
            result = self.setup_new_game()
            if not result.get("ok"):
                log_error("setup_new_game", result.get("error", "unknown"))
                return f"Could not start game: {result.get('error', 'unknown')}"
```

| Gap | Effect |
|-----|--------|
| No `_emit_*` on failure | JSONL `error` only — no matching `gm_narration` (APP-071 gap) |
| Raw engine error in return | `Could not start game: campaign not found: …` — not player-facing |
| No `[Awaiting: new game]` footer | Chips may omit **`new game`** retry |

### Context B — death (`_handle_player_death` ~404–433)

```424:432:app/gm/orchestrator.py
        self.setup_new_game(campaign_slug)
        ...
        return (
            f"**{name}** is dead. ..."
            "This run is over. A **new game** has started. Welcome to the Registry, delver. What is your name?"
        )
```

| Gap | Effect |
|-----|--------|
| `setup_new_game` return **ignored** | Success NAME prompt even when L4/L5 failed |
| Caller always `_emit_narration` (~1586, ~1680) | Naive in-handler recovery emit would **double-log** `gm_narration` |

### Context C — `run_ended` (`process_turn` ~549–565)

```558:564:app/gm/orchestrator.py
                self.setup_new_game(campaign_slug)
                death_msg = (
                    f"Your previous delver did not survive ..."
                    "This run is over. A **new game** has started. What is your delver's name?"
                )
                self._emit_narration(death_msg)
```

| Gap | Effect |
|-----|--------|
| No `ok` check after `setup_new_game` | Success run_ended copy + `_emit_narration` (drift path) on failure |

### Existing helper (reuse — no change to contract)

```309:311:app/gm/orchestrator.py
    def _emit_recovery_narration(self, message: str) -> None:
        """Log recovery copy without creation drift checks (resume failure paths)."""
        log_gm_narration(message)
```

**Do not** call `_emit_narration` on any setup-failure path — `[Awaiting: new game]` would trigger `awaiting_mismatch` when `_creation_drift_scope()` is true.

---

## Code-path traces (planned)

### Context A — explicit `new game` command failure

| Step | Location | Action |
|------|----------|--------|
| A1 | `process_turn` | `lower in ("new game", "start", "new")` |
| A2 | `setup_new_game()` | Returns `{"ok": False, "error": …}` |
| A3 | `log_error("setup_new_game", verbatim error)` | Unchanged context string (QA grep) |
| A4 | `_setup_new_game_failure_message(result, context="command")` | R2 copy + R5 `{cause_line}` + `[Awaiting: new game]` |
| A5 | `_emit_recovery_narration(message)` | **Once** — inline in `process_turn` (R1a) |
| A6 | `return message` | UI `narration_text`; chips from footer |
| A7 | **Forbidden** | `_creation_turn`, success NAME desk |

**Success (unchanged):** `ok` → `_creation_turn("[SYSTEM: New game started…]")` (R7 / T-019f).

### Context B — combat death restart failure (R1b / SPEC-001)

| Step | Location | Action |
|------|----------|--------|
| B1 | Combat resolves PC death | `_handle_player_death(mechanical)` |
| B2 | Early exits | `None` if no death / no char / corpse processing failed — **unchanged** |
| B3 | `setup_new_game(campaign_slug)` | Capture `result` |
| B4a | **`not result.get("ok")`** | `log_error` → R3 message (preserve corpse `{name}` / `{where}`) → `_emit_recovery_narration` **inside handler** → return `PlayerDeathResult(message, already_emitted=True)` |
| B4b | **`ok`** | Build existing success copy → return `PlayerDeathResult(message, already_emitted=False)` |
| B5 | Combat caller ~1586 or ~1680 | If result non-`None`: append history; **`if not already_emitted: _emit_narration(message)`**; `return message` |
| B6 | **Forbidden** | Recovery emit in handler **and** caller `_emit_narration` on same failure; `_emit_narration` on failure copy |

**Success death path (unchanged):** `already_emitted=False` → caller `_emit_narration` once → NAME desk via `_check_creation_drift` on success copy only.

### Context C — `load game` + `run_ended` + setup failure

| Step | Location | Action |
|------|----------|--------|
| C1 | `process_turn("load game")` | `session_resume()` → `ok`, `run_ended=True` |
| C2 | Build `{where}` from `corpses[0]` | Existing logic (~551–557) — unchanged |
| C3 | `result = setup_new_game(campaign_slug)` | Capture return |
| C4a | **`not result.get("ok")`** | `log_error` → R4 message → `_emit_recovery_narration` → `return message` (R1a inline) |
| C4b | **`ok`** | Existing `death_msg` + `_emit_narration(death_msg)` + return (R7 regression) |
| C5 | **Forbidden** | Success “new game has started” / NAME prompt on failure |

### Out of scope (document only)

| Item | Note |
|------|------|
| UI `clear_narration` before `new game` | Runs before outcome known — spec accepts; do not skip unless manual QA blocks |
| `main.py` | Thin bootstrap — no session logic |
| APP-014 L1–L7 / APP-015 C1–C2 | Lifecycle ordering unchanged |
| APP-071 load failure | Already closed — pattern mirror only |

---

## Helpers (new, colocated in `orchestrator.py`)

Place after `_emit_recovery_narration` (~309) so emit contract stays visible.

### `_map_setup_new_game_cause(self, error: str) -> str`

Substring map per spec R5 / domain § Engine error → cause line:

| Pattern | `{cause_line}` |
|---------|----------------|
| `campaign not found` | The save campaign could not be found in the workspace database. |
| `slug must be` | The campaign name failed validation — this is an internal setup error. |
| `campaign already exists` | A leftover campaign record blocked startup (unexpected after wipe). |
| `active session already exists` / `campaign already has an open session` | A stale open session blocked startup (regression — report if seen after APP-014). |
| `permission denied`, `database is locked`, `disk I/O` | The workspace database could not be written (permissions or file lock). |
| default | Something went wrong while resetting the workspace for a new run. |

First matching row wins; case-insensitive substring on `str(error)`.

### `_setup_new_game_failure_message(self, result: dict, *, context: Literal["command", "death", "run_ended"], name: str | None = None, where: str | None = None) -> str`

- `cause_line = self._map_setup_new_game_cause(result.get("error") or "")`
- **command (R2):**
  ```
  Could not start a fresh session.

  {cause_line}

  Type **new game** to try again. If this keeps happening, quit and relaunch the app.

  [Awaiting: new game]
  ```
- **death (R3):** Lead with preserved corpse line (`**{name}** is dead… **{where}**`); tail:
  ```
  This run is over, but the registry could not open a fresh desk session.

  {cause_line}

  Type **new game** to try again.

  [Awaiting: new game]
  ```
- **run_ended (R4):** Lead with existing prior-delver line + `{where}`; same failure tail as death (without duplicating corpse name line from B).

All variants: **never** expose verbatim engine error as primary copy; **never** include “new game has started” or “What is your name?”.

### `PlayerDeathResult` (dataclass — dev choice for R1b)

```python
@dataclass(frozen=True)
class PlayerDeathResult:
    message: str
    already_emitted: bool = False
```

- `_handle_player_death` return type: `PlayerDeathResult | None`
- `None` = no death processed (preserve combat caller `if death_result is not None` guard)
- Tuple `(message, already_emitted)` acceptable if dataclass feels heavy — **must** distinguish `None` vs emitted failure vs success

---

## Task breakdown

### 1. Add failure helpers — `app/gm/orchestrator.py`

1. Add `_map_setup_new_game_cause`, `_setup_new_game_failure_message` after `_emit_recovery_narration`.
2. Add `PlayerDeathResult` near top of module (with other small types) or immediately above `_handle_player_death`.
3. No bridge/engine changes.

### 2. Context A — wire `process_turn` new-game branch

Replace lines 537–539:

```python
if not result.get("ok"):
    log_error("setup_new_game", result.get("error", "unknown"))
    message = self._setup_new_game_failure_message(result, context="command")
    self._emit_recovery_narration(message)
    return message
```

### 3. Context B — refactor `_handle_player_death`

1. Capture `setup_result = self.setup_new_game(campaign_slug)`.
2. Compute `{name}` / `{where}` from corpse (unchanged).
3. On failure: build R3 via `_setup_new_game_failure_message(..., context="death", name=name, where=where)` → `log_error` → `_emit_recovery_narration` → `return PlayerDeathResult(message, already_emitted=True)`.
4. On success: existing success string → `return PlayerDeathResult(message, already_emitted=False)`.
5. Early exits still `return None`.

### 4. Context C — wire `process_turn` `run_ended` branch

After `{where}` resolution (~557), replace unconditional setup + success narrate:

```python
setup_result = self.setup_new_game(campaign_slug)
if not setup_result.get("ok"):
    log_error("setup_new_game", setup_result.get("error", "unknown"))
    message = self._setup_new_game_failure_message(
        setup_result, context="run_ended", where=where
    )
    self._emit_recovery_narration(message)
    return message
death_msg = ( ... existing success copy ... )
self._emit_narration(death_msg)
return death_msg
```

Adjust R4 builder so run_ended lead line includes prior-delver prose + `{where}` (spec minimum).

### 5. Combat caller changes — `orchestrator.py` ~1586–1591 and ~1680–1684

**Both sites** — replace:

```python
death_narration = self._handle_player_death(mechanical)
if death_narration:
    self._emit_narration(death_narration)
    ...
    return death_narration
```

With:

```python
death_result = self._handle_player_death(mechanical)
if death_result is not None:
    if not death_result.already_emitted:
        self._emit_narration(death_result.message)
    self.history.append(...)  # preserve existing append shape
    return death_result.message
```

- Site 1 (~1586): keep user + assistant history append as today.
- Site 2 (~1680): assistant-only append as today.
- **Never** `_emit_narration` when `already_emitted=True`.

### 6. Optional R6 — `app/ui/app.py`

**Defer until manual smoke.** If command failure copy is hard to notice after `clear_narration`:

- In `_process_turn`, after orchestrator returns, if message starts with `Could not start a fresh session` (or add `orchestrator.last_turn_was_setup_failure` flag — only if prefix is brittle), call `_set_turn_idle("Error — try again")`.
- **Do not** queue `("error", full_message)` — avoids `[Error: …]` duplication.

Ticket closes without this if narration + chips suffice.

### 7. Tests — `app/tests/test_setup_new_game_failure.py` (new)

Follow APP-071 style: `orchestrator` fixture, monkeypatch `gm.orchestrator.log_gm_narration`, `log_error`, `log_creation_drift`.

| ID | Case | Setup | Action | Assert |
|----|------|-------|--------|--------|
| **T-019a** | Command failure — mapped cause | `monkeypatch.setattr(orch, "setup_new_game", lambda *a, **k: {"ok": False, "error": "campaign not found: salt-road"})` | `process_turn("new game")` | R2 lead; mapped cause line; `[Awaiting: new game]`; **one** `log_gm_narration`; `log_error("setup_new_game", …)`; no `Could not start game:` prefix |
| **T-019b** | Command failure — default map | Mock `setup_new_game` → `{"ok": False, "error": "something weird"}` | `process_turn("new game")` | Default `{cause_line}`; verbatim engine error **not** in player copy first line |
| **T-019c** | Death failure + caller contract | Mock `bridge.extract_death_from_mechanical` → death hit; `process_delver_death` → ok + corpse; `setup_new_game` → fail | `death_result = orch._handle_player_death([{...}])` then simulate caller: skip `_emit_narration` if `already_emitted` | R3 copy; no “new game has started”; `already_emitted is True`; **one** `gm_narration`; no `_creation_turn`; assert caller branch would not call `_emit_narration` |
| **T-019d** | run_ended failure | Mock `bridge.session_resume` → `ok, run_ended=True, corpses=[{site_address, room_id}]`; `setup_new_game` → fail | `process_turn("load game")` | R4 copy; no NAME / success prompt; dual JSONL; **one** `gm_narration` |
| **T-019e** | Drift silence | Run T-019a setup + T-019c setup | Inspect `log_creation_drift` mock | No events with `awaiting_mismatch` in `reasons` |
| **T-019f** | Success regression | Isolated workspace, real `setup_new_game` | `process_turn("new game")` | Reaches creation / NAME path (`creation.active`, step `NAME` or creation turn content) — mirrors T-014a |

**T-019c notes:**

- No full combat integration required — direct `_handle_player_death` + explicit caller-branch assertion.
- Optional helper in test file: `_simulate_combat_death_emit(orch, death_result)` that mirrors ~1586 logic.

**T-019d notes:**

- Monkeypatch `bridge.session_resume` on orchestrator’s bridge instance or module path `gm.orchestrator` if bridge method bound at call time.

### 8. Domain spec sync — `tmp/app-session-persistence-spec.md` (on close)

- Check APP-019 task checkbox; confirm § New game failure matches impl.
- Changelog row if copy tweaks during impl.
- `release APP-019 --done` after pytest green.

---

## Files (must ⊆ ticket Expected files)

| File | Change |
|------|--------|
| `app/gm/orchestrator.py` | `_map_setup_new_game_cause`, `_setup_new_game_failure_message`, `PlayerDeathResult`; contexts A/B/C; combat callers |
| `app/tests/test_setup_new_game_failure.py` | **New** — T-019a–f |
| `app/ui/app.py` | **Optional** R6 only |
| `tmp/app-session-persistence-spec.md` | Checklist / changelog on close |

**Out of scope:**

- `app/main.py`
- `play/tomb_gm/**` engine error shapes (consume as-is)
- Toast widget (non-existent)
- Changing APP-014 lifecycle order or APP-015 disk clear

---

## Tests

```bash
# From repo root
python -m pytest app/tests/test_setup_new_game_failure.py -q
python -m pytest app/tests -q -k "setup_new_game_failure or setup_new_game"
```

| Step | Command | Expected |
|------|---------|----------|
| New module | `pytest app/tests/test_setup_new_game_failure.py -q` | T-019a–f pass |
| Filter | `pytest app/tests -q -k "setup_new_game_failure or setup_new_game"` | APP-019 + APP-014 lifecycle green |
| Regression | `pytest app/tests/test_session_resume_failure.py -q` | APP-071 unchanged |
| Regression | `pytest app/tests/test_creation_flow.py -q -k "new_game"` | T-019f / creation path |

**Manual smoke (Stage 7):** `cd app && python main.py` — TC-A–D in spec.md; inject L4/L5 failure; tail JSONL for paired `error` + `gm_narration`.

---

## Rollback / risks

| Risk | Mitigation |
|------|------------|
| Double `gm_narration` on death failure | R1b: `already_emitted` + caller skip |
| `creation_drift` / `awaiting_mismatch` | `_emit_recovery_narration` only on failure; never `_emit_narration` |
| Return-type break at combat sites | Only two call sites; type `PlayerDeathResult \| None`; preserve `None` early exits |
| R6 prefix sentinel brittle | Prefer message prefix match; add flag only if needed |
| APP-015 disk state on failure | C1–C2 already run at `setup_new_game` entry — no change |

**Rollback:** Revert orchestrator failure branches + delete test file.

---

## Acceptance mapping

| Ticket AC | Plan task |
|-----------|-----------|
| Clear error with cause + retry hint | §2–5 failure branches + `_setup_new_game_failure_message` / R5 map |
| JSONL dual-log | `log_error` + `_emit_recovery_narration` per context |
| Death / run_ended never claim success on failure | §3 `_handle_player_death` ok check; §4 run_ended ok check |
| Single JSONL on death failure | §5 combat caller + `already_emitted` |
| Chips offer **`new game`** | `[Awaiting: new game]` footer all contexts |
