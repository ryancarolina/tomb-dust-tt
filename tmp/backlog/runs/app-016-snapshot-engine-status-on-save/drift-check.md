# Drift Check: APP-016-snapshot-engine-status-on-save

**backlog_ticket:** APP-016  
**Verdict:** **PASS**

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) § Engine status snapshot on save (APP-016) | no | S5a–e, field table, batch notes match `_save_session()`; checklist `[x]` APP-016; AC `[x]`; changelog **APP-016 done** row added |
| Run `spec.md` R1–R3, T4a–d | no | Verified against `app/ui/app.py`, `app/tests/test_engine_status_on_save.py` |
| [`tmp/backlog/app-016-snapshot-engine-status-on-save.md`](../../app-016-snapshot-engine-status-on-save.md) | no | AC checked; **Status** → `done`; **Closed** 2026-05-20 |
| [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry | no | Session persistence row unchanged — APP-016 additive on existing owner |

## Code ↔ domain spec (APP-016)

| Requirement | Code | Match |
|-------------|------|-------|
| **S5a** Every `_save_session()` trigger unchanged (60s, Escape, post-turn `finally`) | `app/ui/app.py` call sites L57, L78, L220, L325 | yes |
| **S5b** Success: full `get_status()` dict under `engine_status` | L401–409 assigns full `status`; L429–430 conditional write | yes |
| **S5c** Single `get_status()` per save for active fields + snapshot | One call L404–409 serves `session_id`, `campaign_slug`, and `engine_status` | yes |
| **S5d** Failure: save proceeds; `engine_status` key omitted | Exception swallowed L410–411; gates `ok is False` / `_error` L408–409; no `null` write | yes |
| **S5e** Legacy load unchanged; no read of `engine_status` | `_load_session` L436+ unchanged; T4c | yes |
| **S1** Full `handle_status` payload (awaiting, roster, party, combat, active, …) | Full dict reference assigned; T4a compares live `get_status()` | yes |
| **Batch** APP-016 write-only; no orchestrator / load edits | Diff scope: `app/ui/app.py`, `app/tests/test_engine_status_on_save.py` only | yes |
| **Batch** APP-015 C2 clear on `setup_new_game` (T-015d) | Not APP-016 impl; T-015d green in focused filter | yes |

## Ticket AC ↔ code

| Acceptance criterion | Result |
|----------------------|--------|
| On save, snapshot engine `status()` alongside app state | **PASS** — `_save_session()` persists `engine_status` when success-shaped |

## Tests ↔ domain spec § Tests APP-016

| Spec ID | Test | Result |
|---------|------|--------|
| **T4a** | `test_save_includes_engine_status_mid_creation` | **PASS** |
| **T4b** | `test_save_includes_engine_status_after_finalize` | **PASS** |
| **T4c** | `test_load_session_legacy_without_engine_status` | **PASS** |
| **T4d** | `test_save_omits_engine_status_on_get_status_failure` | **PASS** |

```bash
cd app && python -m pytest tests -q -k "engine_status or save_session"
cd app && python -m pytest tests -q
```

**Result:** 6 passed, 17 deselected (2.37s); 23 passed (4.33s)

Focused filter includes 2× APP-015 **T-015d** regression (`engine_status` clear on `setup_new_game`).

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec § Engine status snapshot + checklist + changelog aligned with code
- [x] Ticket **Status** → `done` / **Closed** 2026-05-20
- [ ] `python tmp/backlog/claim_ticket.py release APP-016 --done` — orchestrator (clears active session)

## Ancillary notes (non-blocking)

1. **T4d** covers exception path only; error-shaped payload (`ok: false`, `_error`) omit is implemented (L408–409) but not separately pytest'd — acceptable per impl QA.
2. **T4a/T4b** do not assert every reconcile key explicitly; mitigated by persisting the full status dict.
3. Domain spec header **Status: In progress** reflects broader session backlog (APP-014–APP-020), not APP-016 regression.
4. Manual mid-creation autosave / Escape inspect — deferred Stage 7 `human-test-plan.md`.
5. Read path (`engine_status` on load) intentionally absent — **APP-017** / **APP-018** scope.
