# Implementation Plan: APP-014 — setup_new_game session lifecycle

**Status:** draft (Dev plan round 1)  
**backlog_ticket:** APP-014  
**ticket_path:** [tmp/backlog/app-014-setupnewgame-session-lifecycle.md](../../app-014-setupnewgame-session-lifecycle.md)  
**domain_spec:** [tmp/app-session-persistence-spec.md](../../../app-session-persistence-spec.md) § setup_new_game lifecycle (APP-014)  
**run-folder:** `tmp/backlog/runs/app-014-setupnewgame-session-lifecycle/`  
**Spec:** [spec.md](spec.md) · [research-brief.md](research-brief.md) · [qa-spec-pass.md](qa-spec-pass.md)

## Approach

Prepend **L1 / L1b** (graceful `end_session`, then `force_close_all_sessions` on any `not ok`) to the existing `Orchestrator.setup_new_game` body. Keep **L2–L7** order unchanged: wipe → init → campaign_new → session_start → orchestrator reset → `_delete_save_file`. No bridge or engine edits unless tests expose a gap. UI (`app/ui/app.py`) stays read-only for APP-014; autosave / failure-path disk clear is **APP-015**.

Single hub method satisfies ticket AC and domain L6: all callers already route through `setup_new_game` — no duplicate lifecycle in death or resume branches.

---

## Root cause (current vs required)

```348:361:app/gm/orchestrator.py
    def setup_new_game(self, campaign_slug: str = "salt-road") -> dict:
        """Wipe session/campaign data and start completely fresh. World corpses persist."""
        self.bridge.wipe_all_data()
        self.bridge.init()
        result = self.bridge.campaign_new(campaign_slug, campaign_slug.replace("-", " ").title())
        ...
```

| Step | Today | Required (domain L1–L7) |
|------|--------|-------------------------|
| Session end | **Skipped** | L1 `end_session()`; L1b `force_close_all_sessions()` if L1 `not ok` |
| Wipe | First action | L2 after L1/L1b |
| Campaign + session | Same relative order | L4 → L5 after L3 `init()` |
| App save file | L7 on success only | Unchanged; APP-015 owns upfront creation block |

**Bridge nuance (L1b):** `GameBridge.end_session` only falls back to `force_close_all_sessions` on **exception**, not when `end_session` returns `{"ok": false, "error": "no active session"}` etc. Orchestrator **must** call `force_close_all_sessions()` explicitly when L1 is not ok ([qa-spec-pass.md](qa-spec-pass.md) L1b note).

```399:405:app/gm/bridge.py
    def end_session(self) -> dict:
        ...
        try:
            result = end_session(self.ctx.conn, self.ctx.config)
            return result
        except Exception:
            return self.force_close_all_sessions()
```

```311:324:play/tomb_gm/domain/session.py
def end_session(conn, cfg) -> dict:
    active = read_active(cfg)
    if not active or not active.get("session_id"):
        return {"ok": False, "error": "no active session"}
    ...
    if row["ended_at"] is not None:
        clear_active(cfg)
        return {"ok": False, "error": "session already ended", ...}
```

`wipe_all_data` already deletes `sessions` / `campaigns` and unlinks `active.json`; does **not** touch `world_corpses` ([bridge.py:423–440](app/gm/bridge.py)).

---

## Deep code-path traces

### A. Player types `new game` (post-fix target)

| Step | File:symbol | Action |
|------|-------------|--------|
| A1 | `app/main.py` → `App.run()` | PyGame entry; no `new game` handling in main |
| A2 | `app/ui/app.py:261–268` | `_submit` → daemon `_process_turn(text, turn_id)` |
| A3 | `app/ui/app.py:283–284` | If text ∈ `{new game, new, start}` → queue `clear_narration` |
| A4 | `app/ui/app.py:286–289` | `_turn_lock` → `orchestrator.process_turn(text)` |
| A5 | `app/gm/orchestrator.py:495–500` | `setup_new_game()`; on `not ok` → `log_error` + `Could not start game: …` |
| A6 | `app/gm/orchestrator.py:setup_new_game` | **L1** `end_session()` → **L1b** if needed → **L2–L7** (see § Implementation) |
| A7 | `app/gm/orchestrator.py:500` | Success → `_creation_turn("[SYSTEM: New game started…]")` |
| A8 | `app/ui/app.py:323–325` | `finally`: if `narration is not None` → `_save_session()` writes `creation_state` |

**APP-064 follow-on:** Boot with empty roster + active session → chip `new game` only → A3–A7 must reach NAME without A5 error string.

### B. `setup_new_game` internal (planned)

| Step | Action | Notes |
|------|--------|-------|
| B1 | `end_result = bridge.end_session()` | Sets `ended_at`, clears `active.json` when pointer valid |
| B2 | If `not end_result.get("ok")`: `bridge.force_close_all_sessions()` | DB `ended_at` for all open rows; unlink `active.json` |
| B3 | `bridge.wipe_all_data()` | Hard DELETE session/campaign tables; corpses retained |
| B4 | `bridge.init()` | Migrations |
| B5 | `bridge.campaign_new(slug, display_name)` | Keep `"already exists"` swallow; other errors → early return (L4 failure) |
| B6 | `bridge.session_start(slug)` | `start_session`: `_clear_save_slot`, `write_active`, INSERT `current` |
| B7 | `history.clear()`, `CreationState(active=True, step="NAME")`, `_delete_save_file()` | L6–L7 success path |
| B8 | `return session` dict | Must include `ok: true` from L5 |

### C. Failure path (unchanged semantics; ordering fix only)

| Step | Condition | Outcome |
|------|-----------|---------|
| C1 | B5 returns `not ok` (non–already-exists) | Return error dict; **no** B6–B7 |
| C2 | B6 fails | Return error; **no** B7 |
| C3 | `process_turn` A5 | Narration error only (**APP-019** for toast) |
| C4 | A8 `finally` + failed setup | May persist stale `creation_state` — **APP-015**, not APP-014 |

L1–L2 still run before C1 so engine state is closed/wiped even when campaign insert fails.

### D. Death restart (`_handle_player_death`)

| Step | File:symbol | Action |
|------|-------------|--------|
| D1 | `orchestrator.py:365–381` | `extract_death_from_mechanical` → `process_delver_death(char_id)` |
| D2 | `bridge.process_delver_death` | Inserts/updates `world_corpses` (outside wipe table list) |
| D3 | `orchestrator.py:382–383` | `combat.active = False`; `setup_new_game(campaign_slug)` — **no `ok` check** (APP-019) |
| D4 | `orchestrator.py:389–392` | Success narration assumes new game started |

**Invariant L5:** B3 must not DELETE `world_corpses`; T-014c asserts row count ≥ 1 after D3.

### E. Resume `run_ended` → new game

| Step | File:symbol | Action |
|------|-------------|--------|
| E1 | `orchestrator.py:502–508` | `session_resume()` failure → recovery message (unchanged) |
| E2 | `orchestrator.py:509–525` | `run_ended` → build corpse `where` → `setup_new_game(campaign_slug)` → death_msg |
| E3 | Same B1–B8 | Shared lifecycle; no duplicate wipe/start in caller |

### F. Bridge / engine (read-only for impl)

| API | Path | Role in B1–B6 |
|-----|------|----------------|
| `end_session` | `play/tomb_gm/domain/session.py:311–345` | Graceful close |
| `force_close_all_sessions` | `app/gm/bridge.py:407–421` | L1b fallback |
| `wipe_all_data` | `app/gm/bridge.py:423–440` | L2 |
| `campaign_new` | `play/tomb_gm/domain/campaign.py` | L4 |
| `session_start` → `start_session` | `play/tomb_gm/domain/session.py:161–207` | L5; `replaced_previous: True` |

---

## Implementation steps

### 1. Code — `app/gm/orchestrator.py`

**Function:** `setup_new_game` (~348–361)

Insert before `self.bridge.wipe_all_data()`:

```python
end_result = self.bridge.end_session()
if not end_result.get("ok"):
    self.bridge.force_close_all_sessions()
```

| Rule | Detail |
|------|--------|
| Do not | Short-circuit on L1 failure — always proceed to L1b then L2 |
| Do not | Change `campaign_new` swallow or caller sites in this ticket |
| Do not | Add APP-015 C1–C2 (disk creation clear before L1) |
| Docstring | Update one line: end prior session before wipe |

**Callers (verify only, no edits unless test fails):**

- `process_turn` ~495–500  
- `_handle_player_death` ~383  
- `process_turn` resume `run_ended` ~518  

Optional follow-up (out of APP-014): check `setup_new_game` return before success narration — **APP-019**.

### 2. Tests — `app/tests/test_setup_new_game_lifecycle.py` (new)

Use existing fixtures: `orchestrator`, `bridge`, `isolated_workspace` from [app/tests/conftest.py](../../../app/tests/conftest.py).

| ID | Test | Setup | Assert |
|----|------|-------|--------|
| **T-014a** | `test_setup_new_game_from_mid_creation` | `bridge.session_start("salt-road")`; set `orch.creation` to `step="SKILLS"`, `name="Test"`; `setup_new_game()` | `result["ok"]`; `orch.creation.step == "NAME"`; `bridge.status()["active"]`; open sessions: at most one logical current (query `ended_at IS NULL` → 0 or 1 ending in new current) |
| **T-014b** | `test_setup_new_game_closes_prior_session` | `session_start` → write `active.json` via engine; `setup_new_game()` | Prior row `ended_at` set **or** row deleted; new session id `current`; `creation.step == "NAME"` |
| **T-014c** | `test_setup_new_game_preserves_corpses` | Use `play/tomb_gm/tests/test_death_rules.py` pattern: create character, `process_delver_death` via bridge, count `world_corpses`; `setup_new_game()` | Corpse count unchanged; `result["ok"]` |

**Helpers (module-local or `helpers.py` if reused):**

- `count_open_sessions(conn)` → `SELECT COUNT(*) FROM sessions WHERE ended_at IS NULL`
- `count_corpses(conn)` → `SELECT COUNT(*) FROM world_corpses`

**Pytest marker / name:** file enables `-k "setup_new_game or session_lifecycle"`.

### 3. Domain spec on close (not in impl commit unless same PR)

| File | Action |
|------|--------|
| `tmp/app-session-persistence-spec.md` | Mark checklist APP-014 `[x]`; changelog dated **done** |
| Ticket | `release APP-014 --done` |

### 4. Out of scope (explicit)

| Item | Owner |
|------|--------|
| `_save_session` / failure autosave race | APP-015 |
| `engine_status` on save | APP-016 |
| UI toast for setup failure | APP-019 |
| Remove `"already exists"` swallow | Only if post-wipe insert still fails in QA |
| `app/ui/app.py` edits | None for APP-014 |
| `app/gm/bridge.py` edits | None unless test proves API gap |

---

## Files (must ⊆ ticket Expected files)

| Path | Role |
|------|------|
| `app/gm/orchestrator.py` | **Edit** — L1/L1b prepend in `setup_new_game` |
| `app/tests/test_setup_new_game_lifecycle.py` | **Add** — T-014a, T-014b, T-014c |
| `app/ui/app.py` | **Read-only** — trace A3–A8; no diff APP-014 |
| `app/gm/bridge.py` | **Read-only** — L1/L1b/L2 API reference |

Ticket lists `app/main flow` → interpreted as orchestrator + UI turn pipeline (`app/ui/app.py`); entry remains `app/main.py` (no change).

---

## Tests

| Step | Command | Expected |
|------|---------|----------|
| 1 | `python -m pytest app/tests/test_setup_new_game_lifecycle.py -q` | T-014a–c green |
| 2 | `python -m pytest app/tests -q -k "setup_new_game or session_lifecycle or creation_flow"` | No regressions |
| 3 | `python -m pytest play/tomb_gm/tests -q -k session` | Engine session domain unchanged |
| 4 | Manual | APP-064 partial creation → `new game` → NAME, no setup error (Stage 7 human-test-plan) |

---

## Rollback / flags

- Revert `setup_new_game` L1/L1b block restores wipe-first behavior (known stuck-creation risk returns).
- No feature flags.

---

## Batch coordination

| Ticket | Merge risk |
|--------|------------|
| **APP-014** | Owns first lines of `setup_new_game` |
| **APP-015** | May prepend C1–C2 **before** L1 in same function — land APP-014 first or rebase 015 atop 014 |
| **APP-016** | Independent (`_save_session`) |

---

## Open questions

- **Caller `ok` checks:** Spec says SHOULD; defer to APP-019 unless impl-QA requires minimal guard in death/resume branches.
- **T-014b assertion style:** Prefer “no open sessions after setup except new current” over matching obsolete log strings.
- **T-014c fixture depth:** Minimal corpse via `process_delver_death` vs full combat death — prefer bridge death service (matches D2).
