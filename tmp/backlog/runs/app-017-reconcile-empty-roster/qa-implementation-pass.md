# QA PASS: Implementation

**Task:** APP-017-reconcile-empty-roster  
**backlog_ticket:** APP-017  
**Round:** 1  
**Verdict:** **PASS**

## Summary

`orchestrator.py` adds disk-aware reconcile helpers (`_read_saved_engine_status`, `_effective_awaiting_for_reconcile`, `_force_creation_active_if_reconcile_needed`) and invokes them at the top of `_sync_creation_from_status()` after the optional APP-018 restore hook. Empty-roster mid-creation detection uses **live `roster` only** (not `characters`); `ROSTER_SETUP` is an explicit no-op. Sync body uses `_effective_awaiting_for_reconcile` so live `SETUP` + saved `CHARACTER_CREATION` is not undone by the else branch. Resume path drops inline `NAME` clobber in favor of the reconcile helper. All seven tests in `test_reconcile_empty_roster_on_load.py` pass; focused spec filter passes 13 tests.

**Blocker count:** 0

---

## Tests run

| Command | Result |
|---------|--------|
| `cd app; python -m pytest tests/test_reconcile_empty_roster_on_load.py -q` | **pass** — 7 passed in 2.40s |
| `cd app; python -m pytest tests -q -k "reconcile or empty_roster or engine_status or load_session or app_017"` | **pass** — 13 passed, 54 deselected in 11.44s |

---

## Ticket AC → code + tests

| Ticket AC | On disk | Result |
|-----------|---------|--------|
| Engine roster empty, creation inactive, `awaiting == CHARACTER_CREATION` (live or saved) → force creation mode | `_force_creation_active_if_reconcile_needed()` + sync elif; saved fallback via `_effective_awaiting_for_reconcile` | **PASS** — T-017a, T-017b, T-017c2, T-017e |

---

## Spec R1 — Force creation active

| AC | Status | Evidence |
|----|--------|----------|
| `creation.active == false` + empty live `roster` + mid-creation → `creation.active = true` | **PASS** | `_force_creation_active_if_reconcile_needed` L406–422; T-017a/b/c2/e |
| Non-empty live `roster` → do not reactivate | **PASS** | Early return L414–415; T-017c |
| Legacy / missing `engine_status` — no new errors | **PASS** | `_read_saved_engine_status` → `None`; T-017d via `_load_session` |
| Do not force when `awaiting` not `CHARACTER_CREATION` | **PASS** | `effective != "CHARACTER_CREATION"` guard; T-017f (`ROSTER_SETUP`) |

## Spec R1b — `roster` vs `characters`

| AC | Status | Evidence |
|----|--------|----------|
| Empty check uses `roster` only | **PASS** | `roster = live.get("roster") or []`; no `characters` in reconcile gates |
| `ROSTER_SETUP` + orphan `characters` → no-op | **PASS** | `live_awaiting == "ROSTER_SETUP": return` L417–418; T-017f |

## Spec R2 — Live vs saved precedence

| AC | Status | Evidence |
|----|--------|----------|
| Live `roster` wins over stale saved snapshot | **PASS** | Force gate reads live roster only; T-017c2 |
| Live non-`SETUP` awaiting wins; cold `SETUP` falls back to saved | **PASS** | `_effective_awaiting_for_reconcile` L397–404; T-017b |
| Absent/null `engine_status` → live only, no error | **PASS** | T-017d |

## Spec R3 — APP-018 boundary

| AC | Status | Evidence |
|----|--------|----------|
| APP-017 owns `creation.active` flip only | **PASS** | Force helper sets `active` only (L422) |
| APP-018 restore before force-active | **PASS** | `_sync_creation_from_status` prelude: restore hook → force helper (L184–187) |
| No step reset to `NAME` when saved step in progress | **PASS** | T-017b `pre_step == post_step`; force helper does not touch `step` |
| Minimal `WORLD_INTRO` → `NAME` only in sync body when active | **PASS** | L200–201 (allowed exception) |

## Spec R5 — Implementation locus

| AC | Status | Evidence |
|----|--------|----------|
| Primary change in `orchestrator.py` | **PASS** | Helpers + sync prelude + resume trim L752–754 |
| Orchestrator reads disk via `_session_state_path()` | **PASS** | `_read_saved_engine_status`; tests patch path |
| No APP-016 write / APP-015 clear changes | **PASS** | Out of diff scope |

---

## Test plan T-017a–f / T-017c2 → tests

| ID | Test | Result |
|----|------|--------|
| **T-017a** | `test_t017a_force_active_when_inactive_and_disk_mid_creation` | **PASS** |
| **T-017b** | `test_t017b_force_active_from_disk_when_live_setup` | **PASS** |
| **T-017c** | `test_t017c_post_finalize_non_empty_roster_no_reactivate` | **PASS** |
| **T-017c2** | `test_t017c2_live_empty_roster_wins_over_stale_saved_roster` | **PASS** |
| **T-017d** | `test_t017d_legacy_without_engine_status_unchanged` | **PASS** |
| **T-017e** | `test_t017e_suggestions_nonempty_after_reconcile` | **PASS** |
| **T-017f** | `test_t017f_roster_setup_orphan_rows_no_force_active` | **PASS** |

---

## Diff scope reviewed

| Path | Role | Verdict |
|------|------|---------|
| `app/gm/orchestrator.py` | Reconcile helpers, sync prelude/body, resume defensive force | **PASS** |
| `app/tests/test_reconcile_empty_roster_on_load.py` | T-017a–f, T-017c2 | **PASS** |
| `app/ui/app.py` | Unchanged — load still calls `_sync_creation_from_status()` | **PASS** (per spec R5) |

**Out of scope (correct):** APP-016 save path, APP-015 new-game clear, domain spec changelog/checkbox (release stage).

---

## Non-blocking (release / drift stage)

- **T-017a/b/e** exercise `_sync_creation_from_status()` directly; only **T-017d** hits `headless_app._load_session()`. Behavior is still correct because UI load delegates to the same sync entry point (A3 in plan).
- No dedicated test for corrupt/unreadable `session_state.json` during reconcile (spec: fall back to live, no error) — implementation swallows parse errors in `_read_saved_engine_status`.
- Domain spec APP-017 checklist `[x]` and impl changelog row — defer to `release APP-017 --done`.
- `test_engine_status_on_save.py` fixtures reused via import — acceptable hygiene per plan.

---

## Handoff

**Ready for:** Drift check, `release APP-017 --done`, domain spec changelog sync, Stage 7 `human-test-plan.md` PyGame playtest.
