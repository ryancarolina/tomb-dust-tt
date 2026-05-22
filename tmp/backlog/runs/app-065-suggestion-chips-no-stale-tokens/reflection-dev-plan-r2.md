# Reflection: Dev — APP-065 plan (round 2)

**Agent:** Dev  
**Round:** 2  
**Trigger:** qa-plan-report-1.md FAIL (PLAN-001–003)  
**Deliverables:** revised `plan.md`, `reflection-dev-plan-r2.md`

## Blockers addressed

| ID | Severity | Fix in plan |
|----|----------|-------------|
| PLAN-001 | major | Committed to `_queue_turn_suggestions(turn_id)` helper + `test_process_turn_exception_refreshes_suggestions`; removed “defer unless QA blocks” language |
| PLAN-002 | major | Flow A pseudocode and §3.2 now explicitly retain `return` in `except` after error enqueue, with note that `finally` still runs |
| PLAN-003 | minor | Added `test_queue_turn_suggestions_empty_list_always_put` for unconditional `("suggestions", [])` queue (no `if suggestions:` gate) |

## Changes made

- **Flow A pseudocode:** Introduced testable `_queue_turn_suggestions`; documented `return` in `except` and post-`finally` TTS unreachable on error path.
- **§3.1–3.2:** Helper extraction + mandatory `except` return preservation called out as impl requirement.
- **§4 Tests:** Two named App turn-path tests (queue spy, no pygame loop); cross-linked to spec R1 AC and spec test-plan bullet.
- **§ Tests table:** Step 3 runs the two new tests explicitly before manual repro.
- **Open questions #3:** Marked resolved with concrete test names.
- **AC mapping:** Added exception-path row tied to new test.
- **Changelog:** r2 entry dated 2026-05-20.

## Self-critique

- **App stub shape unspecified:** Plan names tests but not whether `App.__init__` needs pygame display mocking — impl may need a minimal constructor bypass or `@pytest.fixture` that sets `_ui_queue`, `_orchestrator`, `_current_turn_id` only. Low risk; QA impl gate can flag if fixture is heavy.
- **Early-return inside `try` vs refresh:** Plan states stale `turn_id` early returns before `process_turn` should not refresh; current code returns from inside `try` without hitting `finally` suggestion refresh — that matches today (no turn processed). Left implicit; acceptable because behavior is unchanged for superseded turns.
- **Import path still open Q2:** Unchanged from r1; impl verifies `ui.suggestions` import from orchestrator.

## Did I miss anything?

- [x] PLAN-001 exception-path automation — named test + helper, open Q3 resolved
- [x] PLAN-002 except return preservation — pseudocode + §3.2 bullet
- [x] PLAN-003 empty-list queue test — named test + spec cross-ref
- [x] qa-plan-report re-review focus items — all three listed in changelog
- [ ] Pygame init for `_process_turn` test — may need fixture note at impl if QA blocks again

## Handoff

**Ready for:** QA plan gate round 2

**Re-review focus:** Confirm §4 test rows satisfy spec R1 AC and spec test-plan “patch `get_player_suggestions` returning `[]`”; confirm §3.2 + Flow A pseudocode show `return` in `except`.
