# QA Report: spec — round 1

**Task:** app-028-combat-failure-narration  
**backlog_ticket:** APP-028  
**ticket_path:** [tmp/backlog/app-028-combat-tool-failure-narration.md](../../app-028-combat-tool-failure-narration.md)  
**Verdict:** FAIL  
**Reviewer role:** QA (adversarial)  
**domain_spec_creation:** not_needed (registry_gap false)

## Findings

### TICKET-001 — blocker

- **Location:** Ticket § Expected files vs `spec.md` § Affected paths / § Test plan; `tmp/app-combat-play-spec.md` § File map (`app/tests/test_combat_failure_narration.py`)
- **Issue:** PM spec and domain spec require a **new** pytest module `app/tests/test_combat_failure_narration.py`, but the ticket allow-list lists only `app/gm/orchestrator.py`. Backlog hooks and plan QA gate treat Expected files as the edit allow-list.
- **Implementation gap:** Dev adding tests per spec risks hook denial or plan QA FAIL; ticket AC (“enforce failure narration for **all** combat tools”) cannot be closed without tests that are out of scope on paper.
- **Suggested fix:** Extend ticket Expected files to include `app/tests/test_combat_failure_narration.py` (and `tmp/app-combat-play-spec.md` if not already implied by spec-sync rule).

### SPEC-001 — blocker

- **Location:** `spec.md` R1 + § Test plan `test_handle_combat_trigger_start_failure_surfaces`; live `app/gm/orchestrator.py` `_handle_combat_trigger` (L1906–1917)
- **Issue:** R1 requires player-visible failure **before** exploration LLM treats the encounter as live, but `_handle_combat_trigger` is `-> None` and on `start.get("ok")` false performs **no branch** (silent return). The spec allows merge into beat payload, `_llm_loop` short-circuit, or `pending_start`, but does **not** define the observable contract (return value, instance flag, injected system/user message, or amended `process_beat` tool JSON).
- **Implementation gap:** The listed unit test only calls `_handle_combat_trigger` in isolation and asserts “orchestrator records failure for player/loop” without naming **where** failure is recorded. Current code has no such field; test author must invent mechanism or test nothing meaningful.
- **Suggested fix:** Pick one propagation contract in `spec.md` + domain § Beat-trigger start (e.g. `_llm_loop` returns `[Mechanics failed — combat start: …]\n\nCombat could not begin.` on same turn when beat post-hook fails; or `process_beat` tool message includes `start_failure` key). Add an end-to-end test: `process_beat` mock → failed `start_combat_from_trigger` → **player-visible string** before any further `chat_completion` narrate.

### SPEC-002 — blocker

- **Location:** `spec.md` R5 + tool table vs § Test plan / domain § Tests T2–T4; ticket AC “Enforce failure narration for **all** combat tools”
- **Issue:** Exploration inventory lists five tools (`start_combat`, `combat_attack`, `combat_end`, `cast_spell`, `fortune_spend`). Test plan covers `start_combat` and `combat_attack` only (plus combat-inner `combat_action`). No test case for `combat_end`, `cast_spell`, or `fortune_spend` `ok: false` with `all_failed` content strip (R2/R5).
- **Implementation gap:** A regression in one of the three untested tools would still satisfy pytest as written while violating ticket AC.
- **Suggested fix:** Add parametrized `test_llm_loop_all_failed_strips_content[<tool>]` for all five exploration combat tools (distinct failure payloads per tool), or three explicit tests with banned fiction strings (e.g. spell effect, combat ended, Fortune spent).

### SPEC-003 — blocker

- **Location:** `spec.md` R4 vs § Test plan; domain § Tests T1–T6
- **Issue:** R4 requires exploration-equivalent `TOOL FAILED` system injection in `_combat_llm_loop_inner` when the loop **continues** (partial failure / depth retry). No test ID maps to R4; live code (L1831–1846) appends only tool result messages on failure, no system line.
- **Implementation gap:** Dev can implement R2/R3 strip only and still pass listed tests while R4 remains unverified.
- **Suggested fix:** Add test: one failing + one succeeding `combat_action` in same turn (or depth-1 retry after single failure) asserting a system message containing `TOOL FAILED (combat_action)` before tool result.

### SPEC-004 — major

- **Location:** `spec.md` § Test plan `test_beat_trigger_failure_no_success_fiction`; grave-ghoul / `combat: null` scenario in Problem + human playtest
- **Issue:** Grave-ghoul scenario is the **primary** bug (research path A; domain Problem L117). The beat-fiction test depends on mocking `chat_completion` and an unspecified beat→loop wiring; it does not assert that `process_beat` tool JSON still contains `ok: true` + `combat_trigger` while **player** text is failure-only (dual-channel ambiguity PM left open).
- **Implementation gap:** Implementer could inject failure only into logs or internal state while LLM still receives success-leaning beat summary in tool role message — test may pass on return string while fiction leaks on retry turn.
- **Suggested fix:** In R1 contract, state whether beat tool message must carry `start_failure` / amended `ok` or whether player return alone is sufficient; test must assert tool-role content **or** document explicit non-goal for tool-message truth on beat path.

### SPEC-005 — minor

- **Location:** `spec.md` R8; domain § Logging
- **Issue:** Logging requirement has no pytest or human-playtest checkpoint (acceptable as non-player-facing, but APP-034 coordination is pointer-only).
- **Suggested fix:** Add one test with `caplog` / mock `log_error` for beat-trigger short-circuit or `all_failed` strip; or add human-playtest bullet to grep `app/logs/*.jsonl` for `all tools failed` / combat start error after repro.

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | Valid P1 feature; `in_progress`; domain spec field matches `app-combat-play-spec.md` |
| registry_gap | **PASS** | false — combat-play spec owns behavior; PM updated § Combat tool failure narration |
| Code traces | **PASS** | Silent `_handle_combat_trigger` failure, `_llm_loop` / `_combat_llm_loop_inner` `all_failed` + content append confirmed at L1999–2006, L1848–1854 |
| AGENTS.md / canon | **PASS** | App orchestration only; no mechanics drift |
| AC testability (all combat tools) | **FAIL** | SPEC-002 — three exploration tools untested |
| Beat-trigger / grave-ghoul testability | **FAIL** | SPEC-001, SPEC-004 — propagation + dual-channel |
| Scope ⊆ Expected files | **FAIL** | TICKET-001 |
| Domain spec sync | **PASS** (content) | Run spec and domain § APP-028 aligned on R1–R8 intent |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Enforce failure narration for **all** combat tools | R5 table + R3/R4 combat_action | Partial pytest | **FAIL** — SPEC-002, SPEC-003 |
| (Implied) no success fiction on `ok: false` | R1–R3, R5–R6 | Partial | **FAIL** — SPEC-001, SPEC-004 |
| Spec sync on close | Expected files + changelog | Process | **PASS** (intent) |

## Verified (code evidence)

| Claim | Evidence |
|-------|----------|
| Beat trigger silent on start failure | `orchestrator.py` L1912–1917 — no branch when `not start.get("ok")` |
| Exploration `all_failed` appends pre-tool content | `orchestrator.py` L1999–2006 |
| Combat inner `all_failed` appends content | `orchestrator.py` L1848–1854 |
| Good `pending_start` failure shape exists | `orchestrator.py` L1717 |
| `pending_start` never set True | research-brief grep; no assign in repo |
| Combat tools in inventory | `tools.py` L155, L174, L190, L242, L272; `COMBAT_ACTION_TOOL` L24 |
| Default grave-ghoul specs | `orchestrator.py` L1909; `beat.py` L352 |
| No app-layer failure narration tests | `app/tests/test_combat_failure_narration.py` absent |

## Summary

PM draft correctly identifies the grave-ghoul / `combat_trigger` silent-failure path and the `all_failed` content-leak bugs, and domain spec § APP-028 matches run `spec.md` on intent. **FAIL** because (1) ticket Expected files omit required tests, (2) R1 lacks an observable propagation contract and end-to-end beat test, (3) ticket AC “all combat tools” is not backed by tests for `combat_end`, `cast_spell`, or `fortune_spend`, and (4) R4 has no test mapping.

**Blocker count:** 4 blockers (TICKET-001, SPEC-001, SPEC-002, SPEC-003) + 1 major (SPEC-004) + 1 minor (SPEC-005).

## Re-review focus

- Ticket Expected files include `app/tests/test_combat_failure_narration.py`
- R1 names single propagation mechanism + E2E beat→player test
- Parametrized or explicit tests for `combat_end`, `cast_spell`, `fortune_spend`
- R4 partial-failure system injection test
- Optional: R8 log assertion or playtest grep step
