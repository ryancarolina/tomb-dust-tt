# Workstreams: APP-019-surface-new-game-errors

**backlog_ticket:** APP-019  
**ticket_path:** tmp/backlog/app-019-surface-new-game-failure-errors.md  
**domain_spec:** tmp/app-session-persistence-spec.md (§ New game failure, T-019a–f)

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | Failure helpers + contexts A/B/C + combat callers | — | `app/gm/orchestrator.py` | `_map_setup_new_game_cause`, `_setup_new_game_failure_message`, `PlayerDeathResult`; contexts A/B/C wired; both combat sites honor `already_emitted`; import smoke green |
| WS2 | Tests T-019a–f | WS1 | `app/tests/test_setup_new_game_failure.py` | `pytest app/tests/test_setup_new_game_failure.py -q` green; regression filters green |

**Stream count:** 2 — WS1 is all orchestrator failure surfacing (~120–180 LOC across helpers + three contexts + two combat call sites); WS2 locks domain tests T-019a–f and APP-014/071/creation regressions.

**Out of workstreams (ticket release):** `tmp/app-session-persistence-spec.md` checklist + changelog; `python tmp/backlog/claim_ticket.py release APP-019 --done`; manual Stage 7 playtest (spec TC-A–D).

**Explicitly not in any stream:** `app/main.py`, `app/gm/bridge.py`, `play/tomb_gm/**`, optional R6 `app/ui/app.py` (defer until manual smoke — escalate human if narration visibility weak).

---

## WS1 — Failure helpers + contexts A/B/C + combat callers

**Scope:** Plan tasks §1–5 — `_map_setup_new_game_cause`, `_setup_new_game_failure_message`, `PlayerDeathResult`; wire context A (command), B (death + `already_emitted`), C (`run_ended`); update both combat death emit sites.

**Requirements covered:** spec R0–R5, R1a/R1b emit ownership, R7 success branches unchanged; ticket AC (cause + retry + no silent success on B/C).

### Implementation order (within stream)

| # | Task | File:area | Plan ref |
|---|------|-----------|----------|
| 1 | Add `PlayerDeathResult` dataclass (`message`, `already_emitted=False`) | `orchestrator.py` — near module types or above `_handle_player_death` | § Helpers |
| 2 | Add `_map_setup_new_game_cause(error: str) -> str` | After `_emit_recovery_narration` (~309) | § `_map_setup_new_game_cause` |
| 3 | Add `_setup_new_game_failure_message(result, *, context, name?, where?)` | Same block as #2 | § `_setup_new_game_failure_message` |
| 4 | **Context A** — replace terse command failure branch | `process_turn` ~535–539 | §2, Trace A |
| 5 | **Context B** — refactor `_handle_player_death` return contract | `_handle_player_death` ~404–433 | §3, Trace B |
| 6 | **Context C** — guard `run_ended` setup failure | `process_turn` ~549–565 | §4, Trace C |
| 7 | **Combat callers** — honor `already_emitted` at both sites | ~1586–1591, ~1680–1684 | §5 |

### Task 4 — Context A (command failure)

Replace current `Could not start game: {error}` branch:

```python
if not result.get("ok"):
    log_error("setup_new_game", result.get("error", "unknown"))
    message = self._setup_new_game_failure_message(result, context="command")
    self._emit_recovery_narration(message)
    return message
```

**Success path unchanged:** `ok` → `_creation_turn("[SYSTEM: New game started…]")` (R7 / T-019f).

### Task 5 — Context B (death restart failure)

1. Capture `setup_result = self.setup_new_game(campaign_slug)`.
2. Preserve early exits → `return None` (no death / no char / corpse processing failed).
3. Compute `{name}` / `{where}` from corpse (unchanged).
4. **On failure:** `log_error` → R3 via `_setup_new_game_failure_message(..., context="death", name=name, where=where)` → `_emit_recovery_narration` → `return PlayerDeathResult(message, already_emitted=True)`.
5. **On success:** existing success string → `return PlayerDeathResult(message, already_emitted=False)`.

**Forbidden:** success copy (“new game has started”, “What is your name?”) when `not ok`; `_emit_narration` inside handler on failure.

### Task 6 — Context C (`run_ended` failure)

After `{where}` resolution (~551–557):

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

R4 builder: lead with prior-delver prose + `{where}`; same failure tail as death (without duplicating B corpse name line).

### Task 7 — Combat callers (both sites)

Replace:

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
    self.history.append(...)  # preserve existing append shape per site
    return death_result.message
```

- Site ~1586: keep user + assistant history append as today.
- Site ~1680: assistant-only append as today.

### `_map_setup_new_game_cause` (R5)

First matching row wins; case-insensitive substring on `str(error)`:

| Pattern | `{cause_line}` |
|---------|----------------|
| `campaign not found` | The save campaign could not be found in the workspace database. |
| `slug must be` | The campaign name failed validation — this is an internal setup error. |
| `campaign already exists` | A leftover campaign record blocked startup (unexpected after wipe). |
| `active session already exists` / `campaign already has an open session` | A stale open session blocked startup (regression — report if seen after APP-014). |
| `permission denied`, `database is locked`, `disk I/O` | The workspace database could not be written (permissions or file lock). |
| default | Something went wrong while resetting the workspace for a new run. |

### Failure message variants (R2–R4)

All include `[Awaiting: new game]` footer; **never** expose verbatim engine error as primary copy; **never** “new game has started” or NAME prompt on failure.

| Context | Lead |
|---------|------|
| **command (R2)** | `Could not start a fresh session.` + cause + retry hint |
| **death (R3)** | `**{name}** is dead… **{where}**` + failure tail |
| **run_ended (R4)** | Prior-delver line + `{where}` + failure tail (no duplicate corpse name from B) |

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Emit contract | Failure paths: `_emit_recovery_narration` **only** — never `_emit_narration` (avoids `awaiting_mismatch` under `_creation_drift_scope()`) |
| Dual JSONL | Always `log_error("setup_new_game", verbatim)` **before** build + emit (spec R1 order) |
| Context B double-log | `already_emitted=True` on failure; combat callers skip `_emit_narration` when true |
| `None` vs result | Early `_handle_player_death` exits stay `None`; combat guard is `if death_result is not None` |
| Success regression | Context B success: `already_emitted=False` → caller `_emit_narration` once; context C success keeps `_emit_narration(death_msg)` |
| APP-014 / APP-015 | Do **not** reorder L1–L7 or C1–C2 in `setup_new_game` — consume `{"ok": False, "error": …}` as-is |
| APP-071 mirror | Same recovery pattern as load failure — `_emit_recovery_narration` reuse, no helper contract change |
| Out of scope | `bridge.py`, `main.py`, UI R6, engine error shapes |

### Test gates (WS1 done when)

WS1 has **no dedicated test file** until WS2; smoke after WS1:

```bash
python -c "from gm.orchestrator import Orchestrator; print('import ok')"
```

Optional grep sanity:

```bash
rg "_setup_new_game_failure_message|PlayerDeathResult|already_emitted" app/gm/orchestrator.py
```

Full gates run in WS2.

### Prompt seed for Task subagent (WS1 impl)

```
backlog_ticket: APP-019
ticket: tmp/backlog/app-019-surface-new-game-failure-errors.md
run-folder: tmp/backlog/runs/app-019-surface-new-game-errors/
spec: spec.md | plan: plan.md §1–5, Code-path traces A/B/C | domain: tmp/app-session-persistence-spec.md (§ New game failure)
workstreams: workstreams.md § WS1

Implement WS1 only — orchestrator failure helpers + contexts A/B/C + combat caller already_emitted guards per plan.
AGENTS.md: claim APP-019 before app/ edits; only app/gm/orchestrator.py.
Do not edit app/ui/app.py, bridge.py, play/tomb_gm, or add tests (WS2).
Preserve success paths (R7); use _emit_recovery_narration on all failure paths; never _emit_narration on failure copy.
Write reflection-dev-impl-WS1.md before return.
```

---

## WS2 — Tests (T-019a–f)

**Scope:** Plan task §7 — new `test_setup_new_game_failure.py`; T-019a–f; regression filters; APP-071 mock patterns.

**Depends on:** WS1 — tests assert failure copy, emit contract, and success regression against wired orchestrator.

**Requirements covered:** domain T-019a–f; ticket AC; spec R1 drift silence (T-019e); R7 success (T-019f).

### Implementation order (within stream)

| # | Test ID | Setup | Action | Assert | Plan ref |
|---|---------|-------|--------|--------|----------|
| 1 | Module scaffold | `orchestrator` fixture; monkeypatch `log_gm_narration`, `log_error`, `log_creation_drift` | — | APP-071 style | §7 |
| 2 | **T-019a** | Mock `setup_new_game` → `{"ok": False, "error": "campaign not found: salt-road"}` | `process_turn("new game")` | R2 lead; mapped cause; `[Awaiting: new game]`; one `log_gm_narration`; `log_error("setup_new_game", …)`; no `Could not start game:` prefix | §7 table |
| 3 | **T-019b** | Mock → `{"ok": False, "error": "something weird"}` | `process_turn("new game")` | Default cause line; verbatim engine error not in player copy | §7 table |
| 4 | **T-019c** | Mock death + corpse ok; `setup_new_game` fail | `_handle_player_death([{...}])` + caller-branch simulation | R3 copy; no “new game has started”; `already_emitted is True`; one `gm_narration`; caller would skip `_emit_narration` | §7 table, T-019c notes |
| 5 | **T-019d** | Mock `session_resume` → `ok, run_ended=True, corpses=[…]`; `setup_new_game` fail | `process_turn("load game")` | R4 copy; no NAME/success prompt; dual JSONL; one `gm_narration` | §7 table |
| 6 | **T-019e** | Reuse T-019a + T-019c setups | Inspect `log_creation_drift` mock | No `awaiting_mismatch` in reasons | §7 table |
| 7 | **T-019f** | Isolated workspace; real `setup_new_game` | `process_turn("new game")` | Reaches creation / NAME path (`creation.active`, step `NAME` or creation turn content) | §7 table |
| 8 | Regression | — | Filtered pytest | APP-014 lifecycle + APP-071 resume + creation `new_game` green | plan § Tests |

### T-019c caller simulation

No full combat integration required. Optional helper `_simulate_combat_death_emit(orch, death_result)` mirroring ~1586 logic:

```python
if death_result is not None:
    if not death_result.already_emitted:
        orch._emit_narration(death_result.message)  # must NOT run when already_emitted
```

Assert mock `log_gm_narration` call count == 1 after failure path.

### T-019d bridge mock note

Monkeypatch `bridge.session_resume` on orchestrator’s bridge instance or module path `gm.orchestrator` if bound at call time.

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Mock level | Mock `orchestrator.setup_new_game` acceptable for T-019a–d (qa-plan note); bridge L4/L5 optional extra |
| Collection imports | Follow APP-049 — no module-level `Orchestrator` import in test module if conftest provides fixture |
| WS2 only | Do not re-open orchestrator except WS1 bugfix |
| Death/run_ended success | No dedicated pytest for B/C success — manual TC-D; do not regress existing combat/death flows |
| R4 prose | T-019d asserts `{where}` preservation + failure tail; avoid locking full duplicate prose vs R3 |

### Test gates (WS2 done when all pass)

```bash
python -m pytest app/tests/test_setup_new_game_failure.py -q
python -m pytest app/tests -q -k "setup_new_game_failure or setup_new_game"
python -m pytest app/tests/test_session_resume_failure.py -q
python -m pytest app/tests/test_creation_flow.py -q -k "new_game"
```

### Post-impl (not WS2 — ticket release)

- `tmp/app-session-persistence-spec.md`: check APP-019 task checkbox; confirm § New game failure matches impl; changelog if copy tweaked
- Mark ticket AC done; `release APP-019 --done`
- Manual Stage 7: TC-A–D in spec.md; inject L4/L5 failure; tail JSONL for paired `error` + `gm_narration`
- **Optional R6:** If command failure hard to notice after `clear_narration`, add minimal `_set_turn_idle("Error — try again")` in `app/ui/app.py` — update ticket Expected files before edit

### Prompt seed for Task subagent (WS2 impl)

```
backlog_ticket: APP-019
ticket: tmp/backlog/app-019-surface-new-game-failure-errors.md
run-folder: tmp/backlog/runs/app-019-surface-new-game-errors/
spec: spec.md | plan: plan.md §7 | domain: tmp/app-session-persistence-spec.md (§ Tests APP-019)
workstreams: workstreams.md § WS2

Prerequisite: WS1 merged — failure helpers + contexts A/B/C + combat callers in orchestrator.py.
Implement WS2 only — test_setup_new_game_failure.py T-019a–f; APP-071 mock patterns; optional _simulate_combat_death_emit helper.
AGENTS.md: claim APP-019 if not active; stay within app/tests/.
Run: pytest commands in workstreams.md § WS2 Test gates.
Write reflection-dev-impl-WS2.md before return.
```
