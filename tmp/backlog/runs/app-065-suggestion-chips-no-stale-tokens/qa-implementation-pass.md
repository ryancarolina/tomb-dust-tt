# QA PASS: implementation — round 1

**Task:** app-065-suggestion-chips-no-stale-tokens  
**backlog_ticket:** APP-065  
**ticket_path:** [tmp/backlog/app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md](../../app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md)  
**Round:** 1  
**domain_spec_creation:** synced (draft § Suggestion chips in `tmp/app-pygame-ui-spec.md`; checklist/changelog **done** row deferred to Stage 6 release)

## Verdict

**PASS** — Code-owned chips, unconditional turn-loop refresh (incl. `[]` and exception path), narration scrape removed, blocklist + maps match spec; automated tests green.

## Automated tests

```text
cd app && python -m pytest tests/test_ui_suggestions.py -q
.................                                                        [100%]
17 passed in 0.99s

cd app && python -m pytest tests/test_creation_flow.py tests/test_session_resume_failure.py -q
...........                                                              [100%]
11 passed in 2.05s
```

| Module | Tests | Result |
|--------|-------|--------|
| `app/tests/test_ui_suggestions.py` | blocklist, builder maps, inactive creation, SETUP, equipment regex, queue empty list, stale turn noop, exception refresh, post-finalize orchestrator | ✓ 17 |
| `app/tests/test_creation_flow.py` | narration `Awaiting:` asserts (regression) | ✓ |
| `app/tests/test_session_resume_failure.py` | footer `Awaiting:` asserts (regression) | ✓ |

## Grep / symbol checks

| Check | Evidence | Result |
|-------|----------|--------|
| `_extract_suggestions` removed from `app/ui/app.py` | `rg "_extract_suggestions" app/ui/app.py` — zero | ✓ |
| Turn path uses orchestrator only | `_queue_turn_suggestions` → `get_player_suggestions()` in `finally` | ✓ |
| No narration regex on turn path | `_extract_suggestions` deleted; no `Awaiting:` parse in `_process_turn` | ✓ |
| `get_player_suggestions` does not read narration | `orchestrator.py` L107–121: `creation` + `bridge.status()` + `has_save` only | ✓ |

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| Empty suggestions clear stale chips every turn | `_queue_turn_suggestions` always `put(("suggestions", …))`; `test_queue_turn_suggestions_empty_list_always_put` | ✓ |
| Never show raw internal tokens | `is_blocked_chip_token` + maps; `test_blocked_internal_tokens`, `test_builder_never_returns_blocked` | ✓ |
| Player-facing actions only (curated map) | `app/ui/suggestions.py` maps; no narration scrape | ✓ |
| Equipment: `Yes, confirm` / `I need different gear` | `PLAYER_SUGGESTIONS_BY_CREATION_STEP["EQUIPMENT_GOLD"]`; `test_equipment_gold_active_chips`, `test_equipment_confirm_regex_alignment` | ✓ |
| Startup `load game` / `new game` | SETUP branch + init seed L141–146; `test_setup_has_save` / `test_setup_no_save` | ✓ |
| Click submits display label | `input_box.py` L92–94 unchanged (label == submit) | ✓ |
| Domain spec documents source + blocklist | `tmp/app-pygame-ui-spec.md` § Suggestion chips (L38–88) | ✓ (checklist tick on close — see notes) |

_Outcome supersedes ticket wording that cites `_extract_suggestions` returning empty._

## Spec R1–R6 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | Always clear stale chips (`[]`, success + exception) | `finally` + `_queue_turn_suggestions`; `test_process_turn_exception_refreshes_suggestions` | ✓ |
| **R2** | Code-owned source; no narration | `suggestions.py` + `get_player_suggestions()`; scrape deleted | ✓ |
| **R2** | Post-finalize ignores stale `creation.step` | `build_player_suggestions` active guard; `test_inactive_creation_ignores_step`, `test_get_player_suggestions_empty_after_finalize` | ✓ |
| **R3** | Equipment player phrases | Map + tests above | ✓ |
| **R3** | Objection via non-confirm (no `EQUIPMENT_OBJECTION_RE`) | `test_equipment_confirm_regex_alignment` only asserts `is_equipment_confirm` | ✓ |
| **R4** | Blocklist defense | `is_blocked_chip_token`, `filter_player_suggestions`, parametrize bad tokens | ✓ |
| **R5** | Click never sends internal token | Maps + blocklist; chips are literals | ✓ |
| **R6** | Domain spec sync | § drafted in domain spec | ✓ (release hygiene) |

## Diff scope reviewed

| File | Change | In ticket Expected files? |
|------|--------|---------------------------|
| `app/ui/suggestions.py` | **new** — maps, blocklist, builder | ✓ (untracked `??`) |
| `app/gm/orchestrator.py` | `get_player_suggestions()` (+ unrelated batch edits in same file — see notes) | ✓ |
| `app/ui/app.py` | Remove scrape; `_queue_turn_suggestions` in `finally` | ✓ |
| `app/tests/test_ui_suggestions.py` | **new** — 17 tests | ✓ (untracked `??`) |
| `app/ui/panels/input_box.py` | no change (v1) | ✓ |
| `tmp/app-pygame-ui-spec.md` | § Suggestion chips (PM r2); APP-065 checklist still `[ ]` | ✓ |

## Scope notes (non-blocking)

| Item | Note |
|------|------|
| **Batch bleed in `orchestrator.py`** | Working tree diff also includes APP-073 (`strip_flavor_stats_table`, compose) and APP-075 (`format_skill_parse_error`, `_creation_table_flavor`) hunks. APP-065 addition (`get_player_suggestions`) is isolated and correct; full-file diff is not APP-065-only. |
| **Untracked new files** | `app/ui/suggestions.py`, `app/tests/test_ui_suggestions.py` must be staged before commit. |
| **Domain spec close** | Checklist L102 still open; add impl-done changelog row + `[x]` on `release APP-065 --done`. |
| **Ticket checkboxes** | Still unchecked in backlog file — update at close. |
| **`COMBAT_TURN` blocklist test** | Spec test-plan bullet; covered by `_BLOCKED_ENUMS` (awaiting keys) but no dedicated assert — optional hardening. |
| **Human playtest** | Bumpy repro (equipment chips → confirm → no stale token) not run in QA; defer to Stage 7 `human-test-plan.md`. |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-065 --done` (domain checklist + changelog, ticket AC ticks).  
**Stage 7:** Manual equipment / startup / stale-chip playtest per run spec.
