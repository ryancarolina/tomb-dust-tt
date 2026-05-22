# QA Report: plan — round 1

**Task:** app-065-suggestion-chips-no-stale-tokens  
**backlog_ticket:** APP-065  
**ticket_path:** [tmp/backlog/app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md](../../app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md)  
**Verdict:** FAIL  
**Reviewer role:** QA (adversarial)

## Findings

### PLAN-001 — major

- **Location:** `plan.md` §4 Tests, § Open questions #3; vs `spec.md` R1 acceptance criteria
- **Issue:** Approved spec R1 requires an automated test that when `process_turn` raises, the UI still queues `("suggestions", …)` so stale chips do not persist beside the error line. Plan §4 explicitly defers this (“No full pygame test in v1 — `finally` block verified by QA plan gate reading `app.py`”) and leaves open question #3 unresolved to “avoid unless QA blocks.”
- **Implementation gap:** Impl could pass unit tests on `build_player_suggestions` while regressing the ticket’s core stale-chip bug on the exception path (today `except` returns at `app/ui/app.py` L319–322 with no suggestion refresh).
- **Suggested fix:** Add a concrete test row to §4, e.g.:
  - Extract a small testable helper on `App` such as `_queue_turn_suggestions(turn_id)` called from `finally`, and unit-test it with a mocked `_orchestrator` where `process_turn` raises; assert the queue receives `("suggestions", …)` (including `[]`), **or**
  - Add `test_process_turn_exception_refreshes_suggestions` in `test_ui_suggestions.py` using a minimal `App` stub / queue spy without full pygame loop.
  - Remove open question #3 default “defer”; mark resolved in plan changelog.

### PLAN-002 — major

- **Location:** `plan.md` Flow A pseudocode (§3.2 / § Approach); vs `app/ui/app.py` L319–322
- **Issue:** Planned `_process_turn` pseudocode shows `except` enqueueing `("error", …)` but **no** `return`. Current code **returns** from `except`, skipping TTS / `turn_idle` on failure. If Dev follows pseudocode literally, error turns may fall through and start TTS on partial `narration`.
- **Implementation gap:** Unintended behavior change on failed turns; not covered by planned tests.
- **Suggested fix:** In §3.2, state explicitly: **retain** `return` in `except` after error enqueue (Python still runs `finally` before return). Pseudocode should show:

  ```python
  except Exception as exc:
      if turn_id == self._current_turn_id:
          self._ui_queue.put(("error", str(exc)))
      return  # preserve: no TTS / turn_idle on error
  finally:
      ...
  ```

### PLAN-003 — minor

- **Location:** `plan.md` §4 Tests; vs `spec.md` Test plan bullet “App turn path: patch `get_player_suggestions` returning `[]` → verify queue”
- **Issue:** Plan covers builder/orchestrator tests but not the unconditional `put(("suggestions", suggestions))` guard (no `if suggestions:`). Risk of reintroducing the stale-chip gate during impl.
- **Suggested fix:** Add one test (helper or spy) asserting empty list is queued when `get_player_suggestions()` returns `[]`. Can combine with PLAN-001 helper test.

## Verified (no findings)

- [x] Plan files ⊆ ticket Expected files (`suggestions.py`, `orchestrator.py`, `app.py`, `test_ui_suggestions.py`, domain spec on close)
- [x] Code traces match repo (`_extract_suggestions` L315–317 `if suggestions:`; equipment branch L1004–1008; `EQUIPMENT_CONFIRM_RE` L93–97)
- [x] Lookup order aligns with spec R2/R3 and domain § Suggestion chips (inactive creation ignores step; `EQUIPMENT_GOLD` player phrases; SETUP + `has_save` order)
- [x] Equipment objection path correct (`not is_equipment_confirm` for “I need different gear”; no `EQUIPMENT_OBJECTION_RE` extension)
- [x] Post-finalize guard (`creation.active` false → ignore step map) traced to `_auto_finalize` L1196–1197
- [x] Regression commands listed (`test_creation_flow.py`, `test_session_resume_failure.py`)
- [x] Out of scope boundaries clear (`input_box.py`, `suggest.py`, APP-073 footers)
- [x] Maps to all ticket acceptance criteria in § Acceptance criteria mapping

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket Expected files ⊆ plan | **PASS** | |
| Spec R1–R6 coverage in plan | **PARTIAL** | R1 exception-path automation missing |
| Code traces | **PASS** | Line refs accurate |
| Test plan vs qa-spec-pass | **FAIL** | PLAN-001, PLAN-003 |
| Except-path behavior preservation | **FAIL** | PLAN-002 |

## Summary

Plan is implementation-ready for module/orchestrator work (maps, blocklist, `get_player_suggestions`, delete scrape) but **fails** round 1 because it does not commit to spec-mandated exception-path coverage and omits explicit preservation of the `except` + `return` control flow. Dev should revise `plan.md` §3.2–§4 and open questions, then re-submit for QA plan round 2.

## Re-review focus

- §4 includes named test(s) for `process_turn` exception → suggestion queue refresh (not only code review).
- §3.2 documents `return` in `except` (or equivalent guard so TTS does not run on error).
- Optional: queue spy test for unconditional empty-list refresh.
