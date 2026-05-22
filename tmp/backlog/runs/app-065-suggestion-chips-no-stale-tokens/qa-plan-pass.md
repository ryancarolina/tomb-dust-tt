# QA PASS: plan — round 2

**Task:** app-065-suggestion-chips-no-stale-tokens  
**backlog_ticket:** APP-065  
**ticket_path:** [tmp/backlog/app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md](../../app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md)  
**Round:** 2 (re-review after `qa-plan-report-1.md`)  
**domain_spec_creation:** not_needed (`registry_gap: false`; PM r2 domain § Suggestion chips)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Round 1 findings — resolution

| ID | Severity | Status | Evidence in `plan.md` |
|----|----------|--------|------------------------|
| PLAN-001 | major | **Fixed** | Flow A `_queue_turn_suggestions` + `finally` refresh; §4 `test_process_turn_exception_refreshes_suggestions`; Tests § step 3; open Q3 **Resolved**; changelog r2 |
| PLAN-002 | major | **Fixed** | Flow A pseudocode L58–61 `return` in `except`; L72–73 mandatory note; §3.2 explicit retain `return` (no TTS/`turn_idle` on error) |
| PLAN-003 | minor | **Fixed** | §4 `test_queue_turn_suggestions_empty_list_always_put`; Flow A unconditional `put`; §4 L267 maps to spec test-plan bullet |

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec `tmp/app-pygame-ui-spec.md`
- [x] Ticket Expected files ⊆ plan § Files (strict: `suggestions.py`, `orchestrator.py`, `app.py`, `test_ui_suggestions.py`, domain spec on close; `input_box.py` no change)
- [x] Acceptance criteria testable — ticket AC + spec R1–R6 mapped in § Acceptance criteria mapping
- [x] Code traces match repo (`app/ui/app.py` L315–317 `if suggestions:`; L319–322 `except` + `return` with no chip refresh; `_extract_suggestions` L339–348; equipment L1007; `EQUIPMENT_CONFIRM_RE` L93–97; `_auto_finalize` active=false ~1196–1197)
- [x] AGENTS.md / canon compliance (app-only; no `build/` drift; no `suggest.py` parse)
- [x] Tests/commands listed (new module + creation-flow/session regressions + R1-focused pytest subset)
- [x] Spec R1–R6 coverage in plan (always refresh, builder lookup, maps, blocklist, label==submit, domain changelog on close)
- [x] Batch APP-073 note — chips independent of narration footer shape
- [x] Round 1 “verified” items still hold (lookup order, inactive creation, SETUP order, out-of-scope boundaries)

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/ui/suggestions.py` (new) | Yes |
| `app/gm/orchestrator.py` — `get_player_suggestions()` | Yes |
| `app/ui/app.py` — turn loop, delete scrape | Yes |
| `app/tests/test_ui_suggestions.py` (new) | Yes |
| `tmp/app-pygame-ui-spec.md` — checklist + changelog on close | Yes |
| `app/ui/panels/input_box.py` | Yes (explicit no change v1) |

## Spec / ticket AC → plan / tests

| Requirement | Plan locus | Test / mechanism |
|-------------|------------|------------------|
| R1 always clear (incl. `[]`) | §3 `_queue_turn_suggestions` + `finally` | `test_queue_turn_suggestions_empty_list_always_put` |
| R1 exception path | §3.2 `return` + `finally` | `test_process_turn_exception_refreshes_suggestions` |
| R2 code-owned source | §1–2 builder + orchestrator | builder/orchestrator unit tests |
| R2 inactive creation | Flow C step 5 | `test_inactive_creation_ignores_step` |
| R3 equipment phrases | §1 `EQUIPMENT_GOLD` map; Flow D | `test_equipment_gold_active_chips`, regex alignment |
| R4 blocklist | §1.2–1.4 | `test_blocked_internal_tokens`, `test_builder_never_returns_blocked` |
| R5 label == submit | §6 out of scope `input_box` | map strings only |
| R6 domain spec | §5 PM draft + close checklist | release gate |
| Ticket stale-chip AC | §3 remove `if suggestions:` | empty-list queue test + post-finalize test |
| Ticket no internal tokens | §1 blocklist + delete scrape | blocklist tests |
| Ticket startup chips | §1 SETUP map; Flow E seed | `test_setup_has_save` / `test_setup_no_save` |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-065 `in_progress` |
| Plan ⊆ Expected files | **PASS** | No scope creep |
| Spec R1–R6 in plan | **PASS** | Exception-path automation committed (was PARTIAL r1) |
| Code traces | **PASS** | Line refs spot-checked against live `app.py` / `orchestrator.py` |
| Test plan vs `qa-spec-pass` | **PASS** | PLAN-001, PLAN-003 resolved |
| Except-path behavior preservation | **PASS** | PLAN-002 resolved |
| Round 1 re-review focus | **PASS** | All three items addressed |

## Notes (non-blocking — implementation QA)

1. **`App` without pygame:** §4 relies on `_queue_turn_suggestions` extraction — impl should avoid full display init; if `App.__init__` is heavy, construct minimal instance or test helper on a thin mixin; not a plan gate failure.
2. **Early `return` inside `try` still runs `finally`:** Plan documents helper `turn_id` guard — impl must not refresh superseded turns; acceptable.
3. **Import path (open Q2):** Verify `ui.suggestions` vs repo convention during impl; defer acceptable.
4. **Ticket AC wording** still references `_extract_suggestions` — behavior superseded by unconditional orchestrator refresh; align ticket checkbox text on close if desired.
5. **Blocklist regex** `{2,}` vs spec `*` — aligned with domain spec; paste Supa fixtures if edge tokens slip through filter.

**Verdict:** PASS — ready for workstreams + implementation (Stage 4).
