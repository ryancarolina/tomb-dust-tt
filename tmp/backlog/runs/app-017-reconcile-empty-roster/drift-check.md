# Drift Check: APP-017-reconcile-empty-roster

**backlog_ticket:** APP-017  
**Verdict:** **PASS**

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) § Reconcile empty roster on load (APP-017) | no | R1–R3, tests T-017a–f/c2 match `orchestrator.py`; checklist `[x]` APP-017; § AC `[x]`; changelog **APP-017 done** row added |
| Run `spec.md` R1–R5 | no | Verified against `app/gm/orchestrator.py`, `app/tests/test_reconcile_empty_roster_on_load.py` |
| [`tmp/backlog/app-017-reconcile-empty-roster-on-load.md`](../../app-017-reconcile-empty-roster-on-load.md) | no | AC checked; **Status** → `done`; **Closed** 2026-05-21 |
| [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry | no | Session persistence row unchanged — APP-017 additive reconcile on existing owner |

## Code ↔ domain spec (APP-017)

| Requirement | Code | Match |
|-------------|------|-------|
| **R1** Inactive + empty live `roster` + mid-creation → `creation.active = true` | `_force_creation_active_if_reconcile_needed` L406–422; sync elif L195–201 | yes |
| **R1** Non-empty live `roster` → do not reactivate | Early return L414–415; elif guard L192–194; T-017c | yes |
| **R1** Legacy / missing `engine_status` — no new errors | `_read_saved_engine_status` → `None`; T-017d | yes |
| **R1** Do not force when `awaiting` ≠ `CHARACTER_CREATION` | `effective != "CHARACTER_CREATION"` L420–421; T-017f | yes |
| **R1b** Empty check uses `roster` only (not `characters`) | `roster = live.get("roster") or []`; no `characters` in reconcile gates | yes |
| **R1b** `ROSTER_SETUP` + orphan `characters` → no-op | `live_awaiting == "ROSTER_SETUP": return` L417–418; T-017f | yes |
| **R2** Live `roster` wins over stale saved snapshot | Force gate reads live roster only; T-017c2 | yes |
| **R2** Live non-`SETUP` awaiting wins; cold `SETUP` → saved | `_effective_awaiting_for_reconcile` L397–404; T-017b | yes |
| **R2** Absent/null `engine_status` → live only, no error | Parse errors swallowed L390–391; T-017d | yes |
| **R3** APP-018 restore before APP-017 force-active | `_sync_creation_from_status` L184–187: restore → force | yes |
| **R3** APP-017 does not reset in-progress step to `NAME` | Force helper sets `active` only; T-017b step unchanged | yes |
| **R3** `WORLD_INTRO` → `NAME` only in sync body when active | L200–201 (allowed exception) | yes |
| **R5** Primary change in `orchestrator.py`; disk read via `_session_state_path()` | Helpers L384–422; tests patch path | yes |
| **R5** No APP-016 write / APP-015 clear changes | Diff scope: orchestrator + tests only | yes |
| Reconcile without successful `session_resume` | UI `_load_session` → `_sync_creation_from_status` on load commands (parallel queue L281–282); failure path still loads disk | yes |
| Call sites: `_load_session` + post-resume sync | `ui/app.py` L451; resume success L746–747; defensive L752–754 | yes |

## Ticket AC ↔ code

| Acceptance criterion | Result |
|----------------------|--------|
| Engine roster empty, creation inactive, `awaiting == CHARACTER_CREATION` (live or saved) → force creation mode | **PASS** — `_force_creation_active_if_reconcile_needed` + `_effective_awaiting_for_reconcile` |

## Tests ↔ domain spec § Tests APP-017

| Spec ID | Test | Result |
|---------|------|--------|
| **T-017a** | `test_t017a_force_active_when_inactive_and_disk_mid_creation` | **PASS** |
| **T-017b** | `test_t017b_force_active_from_disk_when_live_setup` | **PASS** |
| **T-017c** | `test_t017c_post_finalize_non_empty_roster_no_reactivate` | **PASS** |
| **T-017c2** | `test_t017c2_live_empty_roster_wins_over_stale_saved_roster` | **PASS** |
| **T-017d** | `test_t017d_legacy_without_engine_status_unchanged` | **PASS** |
| **T-017e** | `test_t017e_suggestions_nonempty_after_reconcile` | **PASS** |
| **T-017f** | `test_t017f_roster_setup_orphan_rows_no_force_active` | **PASS** |

```bash
cd app && python -m pytest tests/test_reconcile_empty_roster_on_load.py -q
cd app && python -m pytest tests -q -k "reconcile or empty_roster or engine_status or load_session or app_017"
```

**Result:** 7 passed (2.17s); 13 passed, 54 deselected (3.98s)

Focused filter includes APP-016 T4c/d and APP-015 T-015d regressions — no breakage.

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec § Reconcile empty roster + checklist + changelog aligned with code
- [x] Ticket **Status** → `done` / **Closed** 2026-05-21
- [ ] `python tmp/backlog/claim_ticket.py release APP-017 --done` — orchestrator (clears active session)

## Ancillary notes (non-blocking)

1. **T-017a/b/e** call `_sync_creation_from_status()` directly; only **T-017d** exercises `headless_app._load_session()` — acceptable: UI load is a thin wrapper to the same sync entry (L449–451).
2. No dedicated pytest for corrupt/unreadable `session_state.json` during reconcile — implementation swallows parse errors (L390–391); matches spec intent.
3. Resume-failure branch restores APP-018 fields but relies on UI `_load_session` for `_sync_creation_from_status` — satisfies “reconcile without successful `session_resume`”.
4. Resume success path calls `_force_creation_active_if_reconcile_needed` twice (inside sync + L752–754) — idempotent; no flip-flop.
5. Domain spec header **Status: In progress** reflects broader session backlog (APP-014–APP-020), not APP-017 regression.
6. Manual mid-creation load/continue playtest — deferred Stage 7 `human-test-plan.md`.
