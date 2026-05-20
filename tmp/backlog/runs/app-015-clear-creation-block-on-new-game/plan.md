# Implementation Plan: APP-015-clear-creation-block-on-new-game

**Status:** draft  
**backlog_ticket:** APP-015  
**ticket_path:** tmp/backlog/app-015-clear-creation-block-on-new-game.md  
**domain_spec:** tmp/app-session-persistence-spec.md  
**Spec:** [spec.md](spec.md) · domain § **New game — creation block clear (APP-015)** (C1–C4, T-015a–**d**)  
**Revision:** round 2 — QA plan report 1 (PLAN-001 `engine_status` clear, PLAN-002 T-015d)

## Approach

Prepend **C1–C2** at the **first line** of `setup_new_game()` — before any bridge/engine call (and therefore before APP-014 L1 `end_session` when that lands in the same function). Extract a small disk helper so creation block clearing is explicit, testable, and survives early returns on `campaign_new` / `session_start` failure.

**Strategy (surgical C2, domain-preferred):**

1. Reset in-memory `self.creation` to a fresh `CreationState(active=True, step="NAME")` with no carry-over fields.
2. Persist to `app/session_state.json` via read-modify-write: set `creation_state` from C1 export; **remove** `engine_status` (`data.pop("engine_status", None)` or `data["engine_status"] = None` — domain treats absent and `null` as no snapshot). Leave `narration_lines`, `input_history`, etc. untouched. **APP-016** write-only on `_save_session`; stale snapshot clear is **APP-015** C2 (domain § Engine status snapshot — New game — stale snapshot).
3. Proceed with existing engine lifecycle (`wipe_all_data` → … → L7 `_delete_save_file()` on success).

**No UI change** unless QA finds orchestrator-first clear is undone — `_save_session()` in `finally` reads `export_creation_state()` from memory; once C1 runs, UI writes NAME-fresh data even on failure paths (QA-spec note T-015b).

**APP-014 merge:** APP-015 prepends C1–C2 **before** L1; APP-014 prepends L1/L1b before L2. Final order: **C1 → C2 → L1 → L1b → L2 → L3 → L4 → L5 → L6 → L7**. If APP-014 is not merged yet, implement C1–C2 at current `setup_new_game` entry (before `wipe_all_data`).

---

## Current state — code-path traces

### Trace A — Happy path `new game` (today)

| Step | Location | Behavior |
|------|----------|----------|
| 1 | `app/ui/app.py` `_submit` → worker `_process_turn` | Queues `clear_narration` for `new game` / `new` / `start` |
| 2 | `app/ui/app.py` `_process_turn` ~286–289 | `orchestrator.process_turn(text)` under `_turn_lock` |
| 3 | `app/gm/orchestrator.py` `process_turn` ~495–500 | `setup_new_game()`; on `ok` → `_creation_turn("[SYSTEM: New game started…]")` |
| 4 | `setup_new_game` ~350–360 | `wipe_all_data` → `init` → `campaign_new` → `session_start`; **then** `history.clear()`, fresh `CreationState`, `_delete_save_file()` |
| 5 | `app/ui/app.py` `_process_turn` `finally` ~323–325 | If narration returned → `_save_session()` writes full JSON including `creation_state` from `export_creation_state()` |
| 6 | Exit | Memory + disk aligned at NAME **only if** L4–L5 succeed |

**Gap:** Steps 4–5 leave a window where engine is wiped but disk still holds prior `step`/`name`/`roll_result` until L7 or UI save. Autosave (`_autosave` every 60s) can persist stale block during slow setup.

### Trace B — Failure path `campaign_new` (today — AC miss)

| Step | Location | Behavior |
|------|----------|----------|
| 1–3 | Same as Trace A | Entry through `process_turn("new game")` |
| 4 | `setup_new_game` ~352–356 | After `wipe_all_data` + `init`, `campaign_new` returns `{ok: false, error: …}` (not `"already exists"`) → **early return** |
| 5 | `process_turn` ~497–499 | Returns `"Could not start game: …"`; **no** creation reset, **no** `_delete_save_file` |
| 6 | `app/ui/app.py` `finally` | `_save_session()` still runs → rewrites **stale** `creation_state` from unchanged memory |
| 7 | Exit | Disk + memory both stale (e.g. `step: SKILLS`, `name: Flupps`) |

**Evidence:** Live `app/session_state.json` with SKILLS block and `"new game"` in `input_history`.

### Trace C — Recovery probe reads stale disk (today)

| Step | Location | Behavior |
|------|----------|----------|
| 1 | `process_turn("load game")` ~502–508 | `session_resume()` fails → `_resume_failure_message` |
| 2 | `_is_mid_creation_resume_failure` ~294–321 | Checks: (a) `self.creation.active`, (b) engine `CHARACTER_CREATION` + empty roster, (c) **disk** `session_state.json` |
| 3 | Disk branch ~308–318 | `creation_state.active` or `step != "NAME"` → variant B |
| 4 | `_resume_failure_message` ~328–339 | Copy cites `self.creation.step` for prose; footer from `format_creation_status(self.creation)` |
| 5 | Exit | Stale disk can force variant B even after failed `new game` wipe intent |

### Trace D — UI autosave during setup (secondary risk)

| Step | Location | Behavior |
|------|----------|----------|
| 1 | `app/ui/app.py` `_autosave` (60s timer) | Main thread `_save_session()` |
| 2 | `_save_session` ~415–416 | `creation_state` = `export_creation_state()` |
| 3 | Worker runs `setup_new_game` synchronously | If creation not reset until end, autosave mid-setup persists old step |

**Mitigation:** C1 at `setup_new_game` entry — before worker spends time in bridge calls.

### Trace E — All `setup_new_game` callers (must inherit fix)

| Caller | Location | Notes |
|--------|----------|-------|
| Player `new game` / `start` / `new` | `process_turn` ~495–500 | Primary AC path |
| Player death | `_handle_player_death` ~383 | Same function; C1–C2 prepend applies |
| Resume `run_ended` | `process_turn` ~518 | Same function |

No duplicate lifecycle — single prepend point.

---

## Planned state — code-path traces

### Trace F — `new game` after C1–C2 (success)

| Step | File:symbol | Action |
|------|-------------|--------|
| 1 | `orchestrator:setup_new_game` entry | `_reset_creation_for_new_game()` — memory → fresh NAME |
| 2 | `orchestrator:_clear_creation_block_on_disk` | R-M-W `session_state.json`; set `creation_state` to `export_creation_state()`; remove `engine_status` |
| 3 | `orchestrator:setup_new_game` | APP-014 L1–L5 (or current wipe → campaign → session_start) |
| 4 | `orchestrator:setup_new_game` L6–L7 | Idempotent memory reset + `_delete_save_file()` on success |
| 5 | `orchestrator:process_turn` | `_creation_turn` → NAME desk narration |
| 6 | `app.py:_save_session` finally | Writes NAME-fresh block (consistent with step 2) |

### Trace G — `new game` after C1–C2 (engine failure)

| Step | File:symbol | Action |
|------|-------------|--------|
| 1–2 | Same as F | Memory + disk NAME-fresh; stale `engine_status` removed **before** wipe |
| 3 | `setup_new_game` | `campaign_new` or `session_start` fails → early return |
| 4 | `process_turn` | Error string to player; memory still NAME |
| 5 | `app.py:_save_session` finally | Persists NAME block, not SKILLS |
| 6 | `_is_mid_creation_resume_failure` | Memory `creation.active` → variant B at **NAME** (valid per domain non-regression); disk probe sees NAME, not prior step |

### Trace H — Test T-015c (load after new game)

| Step | Action |
|------|--------|
| 1 | Seed tmp `session_state.json` with SKILLS + name |
| 2 | Set orchestrator memory to match (or call `import_creation_state`) |
| 3 | `setup_new_game()` (mock bridge success) or `process_turn("new game")` |
| 4 | Assert disk `creation_state.step == "NAME"`, no stale `name`/`roll_result` |
| 5 | `process_turn("load game")` with no engine save |
| 6 | Assert variant B copy references **race/name step from memory (NAME)**, not SKILLS; no disk-only stale step in footer |

---

## Task breakdown

### WS1 — Orchestrator helpers + ordering (`app/gm/orchestrator.py`)

1. **Add `_session_state_path() -> Path`** (or module-level `SESSION_STATE_PATH`) — single source for orchestrator disk ops; used by `_delete_save_file`, `_is_mid_creation_resume_failure`, and new helper. Keeps path logic in one place for test monkeypatch.

2. **Add `_reset_creation_for_new_game() -> None`**
   - `self.creation = CreationState(active=True, step="NAME")` — default dataclass clears all carry-over (`name`, `race`, `roll_result`, table flags, etc.).

3. **Add `_clear_creation_block_on_disk() -> None`** (implements C2 + domain T-015d)
   - Call **after** `_reset_creation_for_new_game` so `export_creation_state()` reflects NAME.
   - If save file exists: `json.loads`, set `data["creation_state"] = self.export_creation_state()`, then **`data.pop("engine_status", None)`** (preferred) or `data["engine_status"] = None`; write back with same indent style as UI (`indent=2`).
   - If save file missing: **no-op** (nothing stale on disk; C3 satisfied via memory).
   - On JSON/IO errors: swallow (match `_delete_save_file` tolerance) — do not block `new game`.
   - **Do not** strip other keys (`narration_lines`, `input_history`, etc.) — only `creation_state` + `engine_status` per domain C2.
   - **Rationale:** Prevents post-wipe disk with fresh NAME `creation_state` and pre-wipe `engine_status.awaiting` / `roster` (batch row APP-015 ↔ APP-016). Fresh `engine_status` is recreated on next `_save_session()` after engine session exists (APP-016).

4. **Prepend to `setup_new_game`** (first statements in function body):
   ```python
   self._reset_creation_for_new_game()
   self._clear_creation_block_on_disk()
   ```
   Then existing engine steps unchanged.

5. **L6 idempotency:** Keep post-success `self.creation = CreationState(active=True, step="NAME")` and `history.clear()` — redundant but harmless; avoids behavior change if someone reorders later.

6. **L7:** Keep `_delete_save_file()` on success path — domain allows whole-file unlink at start **or** end; surgical C2 at start + L7 on success is valid.

7. **Optional refactor (same PR, low risk):** Point `_is_mid_creation_resume_failure` disk probe at `_session_state_path()` instead of inline `Path(__file__)…` — reduces drift with helper.

### WS2 — Tests (`app/tests/`)

**New file:** `app/tests/test_creation_block_on_new_game.py`

**Fixtures / helpers:**

- `session_state_file(tmp_path, monkeypatch)` — monkeypatch `orchestrator._session_state_path` (or module constant) to `tmp_path / "session_state.json"`.
- `seed_stale_creation(save_path, *, with_engine_status=True)` — write JSON with `creation_state: {active: true, step: "SKILLS", name: "Flupps", roll_result: {…}}`, dummy `narration_lines` / `input_history`, and optional **`engine_status`** (e.g. `awaiting: "IN_DELVE"`, non-empty `roster: [{…}]`) to verify surgical write clears snapshot but preserves non-creation keys.

**Cases (domain T-015a–d + QA note on T-015b memory):**

| ID | Test | Assert |
|----|------|--------|
| **T-015a** | Stale file + `setup_new_game()` with real isolated bridge (success) | Disk: `step == "NAME"`, `name == ""`, `roll_result == {}`; `narration_lines` / `input_history` preserved; `orchestrator.creation.step == "NAME"` |
| **T-015b** | Stale file + mock `bridge.campaign_new` → `{ok: false, error: "simulated failure"}` | Early return; disk still NAME-fresh; **`orchestrator.creation.step == "NAME"`** and `creation.name == ""` (QA follow-up) |
| **T-015c** | After T-015a setup, `process_turn("load game")` with no engine save | Result is variant B or A per memory; must **not** mention stale SKILLS step or old name from pre-wipe disk; `[Awaiting: NAME_INPUT]` or equivalent NAME footer |
| **T-015d** | Stale file with mismatched `engine_status` + stale `creation_state`; `setup_new_game()` (success **or** mocked early return after C1–C2) | `engine_status` key **absent** or **`null`**; `creation_state.step == "NAME"`; `narration_lines` preserved |

**Hygiene:** Never write to dev `app/session_state.json`; tmp path only; teardown via tmp_path.

**Regression:** Run existing suite:
```bash
python -m pytest app/tests -q -k "creation_block or new_game_creation"
python -m pytest app/tests -q -k "creation_flow or session_resume"
```

### WS3 — Out of scope (do not implement unless blocked)

| File | Reason |
|------|--------|
| `app/ui/app.py` | Orchestrator-first clear makes `_save_session` idempotent; domain spec defers UI-only clear |
| `app/gm/bridge.py` | Engine lifecycle is APP-014 |
| Domain spec changelog | Impl stage / ticket close |

---

## Files (must ⊆ ticket Expected files)

| File | Change |
|------|--------|
| `app/gm/orchestrator.py` | `_session_state_path`, `_reset_creation_for_new_game`, `_clear_creation_block_on_disk`; prepend C1–C2 in `setup_new_game`; optional unify disk path in `_is_mid_creation_resume_failure` / `_delete_save_file` |
| `app/tests/test_creation_block_on_new_game.py` | **New** — T-015a–**d** |
| `app/tests/conftest.py` | **Optional** — shared `session_state_file` fixture if reused; otherwise keep helpers in test module |

**Not expected:** `app/ui/app.py` (orchestrator owns authoritative clear).

---

## Tests

| Step | Command | Expected |
|------|---------|----------|
| 1 | `python -m pytest app/tests/test_creation_block_on_new_game.py -q` | T-015a–**d** green |
| 2 | `python -m pytest app/tests -q -k "creation_block or new_game_creation"` | Same |
| 3 | `python -m pytest app/tests -q -k "creation_flow or session_resume"` | No regressions |
| 4 | Manual (Stage 7) | Mid-creation SKILLS → `new game` → inspect save → NAME `creation_state`; no stale `engine_status.awaiting` / `roster` until next autosave |

---

## Rollback / flags

- No feature flag. Rollback = revert orchestrator prepend + delete test file.
- Surgical disk write is backward-compatible with existing save schema.

---

## Open questions

| # | Question | Recommendation |
|---|----------|----------------|
| 1 | Create save file when missing vs no-op? | **No-op** if file absent — AC targets clearing stale blocks; `_is_mid_creation_resume_failure` disk branch already returns false when missing |
| 2 | Clear `orchestrator_history` creation messages on new game? | **No** — out of scope (C2: only `creation_state`); L7 whole-file delete on success clears history anyway |
| 3 | APP-014 merge conflict in `setup_new_game`? | Prepend C1–C2 **above** L1; coordinate batch merge order per domain § batch table |
| 4 | Shared `SAVE_PATH` between `orchestrator.py` and `ui/app.py`? | **Defer** — not required for AC; optional follow-up ticket to DRY path constant |

## Acceptance criteria mapping

| Ticket AC | Implementation | Test |
|-----------|----------------|------|
| Explicitly clear `session_state.json` creation block on `new game` | C1 memory + C2 `_clear_creation_block_on_disk` at `setup_new_game` entry | T-015a, T-015b |
| All exit paths | C1–C2 before engine calls | T-015b, T-015d (early return) |
| Recovery does not cite stale disk step | Disk + memory NAME before failure | T-015c |
| Stale `engine_status` cleared on new game (domain C2 / APP-016 batch) | C2 `pop` or `null` on every `setup_new_game` entry | T-015d |
