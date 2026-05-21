# QA PASS: spec — round 2

**Task:** APP-017-reconcile-empty-roster
**backlog_ticket:** APP-017
**ticket_path:** [tmp/backlog/app-017-reconcile-empty-roster-on-load.md](../../app-017-reconcile-empty-roster-on-load.md)
**Round:** 2 (re-review after `qa-spec-report-1.md`)
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Round 1 findings — resolution

| ID | Severity | Status | Evidence |
|----|----------|--------|----------|
| SPEC-001 | blocker | **Fixed** | Run `spec.md` § R4 merge order: **APP-018 restore first → APP-017 force-active if still inactive → `_sync_creation_from_status`**. Matches domain § Merge order and APP-016 Consumers (017 after 018). Cross-link to [APP-018 run spec](../app-018-continue-creation-state/spec.md) present. |
| SPEC-002 | blocker | **Fixed** | R1 AC table row requires inactive + empty **`roster`** + mid-creation (`CHARACTER_CREATION` live or saved). Standalone “empty roster only” bullet removed; line 44 forbids force-active for non–`CHARACTER_CREATION` **`awaiting`**. Aligns with domain § R1 table. |
| TICKET-001 | blocker | **Fixed** | Ticket Expected files include `app/tests/test_reconcile_empty_roster_on_load.py` (T-017a–f, T-017c2). Run spec § Affected paths lists orchestrator + test module. |
| SPEC-003 | blocker | **Fixed** | Run spec § R3: force-active uses **`roster` only** (not **`characters`**); **`ROSTER_SETUP`** + orphan rows = no-op. **T-017f** covers no force-active; **T-017c2** covers stale saved roster vs live empty. Domain § R1b mirrors. |

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec = `app-session-persistence-spec.md`
- [x] Ticket Expected files ⊆ run `spec.md` Affected paths (orchestrator + dedicated test module)
- [x] Acceptance criteria testable (R1–R5, ticket AC, T-017a–f / T-017c2, pytest commands)
- [x] Code traces match repo (`_sync_creation_from_status` at `orchestrator.py` ~177–186 still uses `characters` guard — spec explicitly requires switch to `roster` + `CHARACTER_CREATION`)
- [x] AGENTS.md / canon compliance (session persistence only; no mechanics drift)
- [x] Tests/commands listed with hygiene note (monkeypatch `save_path`; no dev `session_state.json`)
- [x] registry_gap false — domain § Reconcile empty roster on load (APP-017) owns behavior
- [x] Every ticket AC row mapped in run spec + domain § Spec AC mapping

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 feature; in_progress |
| registry_gap | **PASS** | false |
| AC testability | **PASS** | Mid-creation guard, roster-only empty check, ROSTER_SETUP no-op, stale snapshot |
| Code traces | **PASS** | Research + live `_load_session` → `_sync_creation_from_status`; no `engine_status` read today |
| Expected files ⊆ plan scope | **PASS** | TICKET-001 resolved |
| Merge order (017/018 batch) | **PASS** | SPEC-001 resolved — 018 → 017 canonical |
| Domain spec sync | **PASS** | PM r2 changelog; R1b, T-017f, T-017c2 in domain § Tests |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Empty roster + inactive + `CHARACTER_CREATION` → force creation | R1 table row; domain R1 + R1b | T-017a, T-017b | **PASS** |
| Post-finalize non-empty roster unchanged | R1 row 2; T-017c | T-017c | **PASS** |
| Legacy / missing `engine_status` | R2 absent/null; T-017d | T-017d (T4c baseline) | **PASS** |
| Live vs saved precedence | R2; T-017b, T-017c2 | T-017b, T-017c2 | **PASS** |
| Orphan unslotted rows (`ROSTER_SETUP`) | R3 no-op; T-017f | T-017f | **PASS** |
| Suggestion chips after reconcile | T-017e | `get_player_suggestions` regression | **PASS** |
| APP-018 step restore boundary | R4 merge order | Dev integrates with 018 hook | **PASS** |

## Adversarial notes (non-blocking)

1. **Domain ticket AC bullet** — Domain § Acceptance criteria (ticket) line “empty roster + inactive → force creation” is looser than R1 table; **Spec AC mapping** and “per R1” reference resolve intent. Dev should implement R1 table row, not the bare bullet.
2. **Run vs domain section numbering** — Run spec R3/R4/R5 vs domain R1b/R2/R3; content aligned; Dev plan should cite run spec section IDs.
3. **`ROSTER_SETUP` recovery** — Explicitly deferred (no owner ticket); acceptable per PM r2; file follow-up if playtest shows orphan-row stuck state.
4. **APP-018 coupling** — Shared load helper order (018 → 017 → sync) is spec’d but implementation lands in orchestrator only; Dev plan must sequence with APP-018 batch without editing out-of-scope files.

## Summary

All four round 1 blockers (**SPEC-001**, **SPEC-002**, **TICKET-001**, **SPEC-003**) are fully addressed in ticket, run `spec.md` (PM r2), and `tmp/app-session-persistence-spec.md` § APP-017. Spec is implementation-ready for Dev plan.

## Re-review focus

_None — proceed to Dev plan + QA plan gates._
