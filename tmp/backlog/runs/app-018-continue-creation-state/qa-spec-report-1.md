# QA Report: spec — round 1

**Task:** APP-018-continue-creation-state  
**backlog_ticket:** APP-018  
**Verdict:** FAIL  
**Reviewer role:** QA (adversarial)

## Findings

### SPEC-001 — blocker — Relaunch gate contradicts `engine_status` precedence

- **Location:** `spec.md` § PM decisions — Relaunch bullet (line 53) vs `engine_status` vs live engine table (lines 61–62); domain spec § Creation restore G1 / G3a (`tmp/app-session-persistence-spec.md` ~435–461)
- **Issue:** Relaunch requires **live** `awaiting == CHARACTER_CREATION`, but the same spec and domain **G1a** require the shared gate to **prefer saved `engine_status.awaiting`** when the snapshot is present (needed for live `SETUP` + saved mid-creation — APP-017 **T-017b** class). Implementers cannot satisfy both without picking one; relaunch after cold engine would skip restore while resume/load paths would restore.
- **Evidence:** `app/gm/orchestrator.py` `_is_mid_creation_resume_failure()` (~331–357) already treats disk `creation_state.active` as mid-creation; G1/G3b intend restore before `_resume_failure_message` (~359–375) uses `self.creation.step` — relaunch desk input with live `SETUP` + saved `CHARACTER_CREATION` is a realistic post-quit path per research-brief risks.
- **Suggested fix:** Unify relaunch with **G1**: first `process_turn` (non–`new game`) calls `_restore_creation_from_session_state()` whenever **G1** passes (saved awaiting **or** live awaiting + empty roster + active `creation_state`); delete the live-only relaunch clause in PM decisions. Mirror the same wording in domain **G3a** (“when G1 passes”, not “live + disk mid-creation”).

### TICKET-001 — blocker — Test paths missing from Expected files

- **Location:** Ticket `tmp/backlog/app-018-continue-restores-creation-state.md` § Expected files; `spec.md` § Test plan (T-018a–f); domain spec § Tests APP-018
- **Issue:** Domain spec mandates **T-018a–f** and pytest `-k "creation_restore or continue_creation or app018"`, but ticket **Expected files** lists only `app/gm/orchestrator.py`. Run `spec.md` § Affected paths also omits `app/tests/` (unlike APP-017 run spec, which explicitly flags ticket expansion). Hooks and plan QA require edits ⊆ Expected files — Dev cannot land tests without ticket amendment.
- **Suggested fix:** Add concrete test module path(s) (e.g. `app/tests/test_creation_restore.py` or extend `app/tests/test_session_resume_failure.py`) to ticket Expected files and `spec.md` § Affected paths before Dev plan.

## Verified (no blocker)

| Gate | Result | Notes |
|------|--------|-------|
| Backlog ticket valid | PASS | APP-018 `in_progress`; domain spec matches ticket |
| `registry_gap` | PASS | `false`; domain § Creation restore (APP-018) added; no new registry row |
| Merge order vs APP-017 | PASS | Run spec + domain § R3 / Merge order: **018 restore → 017 force-active → sync**; consistent with batch-board parallel impl + shared helper note |
| `import_creation_state` gate | PASS (once SPEC-001 fixed) | G1/G2 forbid post-import NAME clobber; R5 legacy fallback; T-018f APP-015 regression named |
| Relaunch AC scope | PASS (intent) | First-turn `process_turn` hydration satisfies “Save mid-creation → relaunch → same step” within `orchestrator.py`-only scope; boot chips stay APP-064 |
| Resume fail/success ordering | PASS | R3/R4 + domain G3b/G3c align with code at `orchestrator.py` ~542–579 (`_resume_failure_message`, NAME clobber) |
| Code traces | PASS | Research-brief paths match repo; bug lines 573–576 cited correctly |

## Summary

Spec and domain content are strong on restore helper design, APP-017 batch ordering, and `import_creation_state` rules, but **FAIL** until: (1) relaunch gate matches **G1** / saved-`engine_status` precedence, and (2) ticket Expected files authorize pytest modules for T-018a–f.

**Blocker count:** 2

## Re-review focus

- Single normative gate (G1) for relaunch, resume fail, and resume success — no live-only relaunch carve-out
- Ticket Expected files + run `spec.md` Affected paths include test module(s)
- Confirm domain G3a wording updated in same PM revision
