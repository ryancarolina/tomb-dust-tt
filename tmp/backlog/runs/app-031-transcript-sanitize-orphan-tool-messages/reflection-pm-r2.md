# Reflection: PM — APP-031 transcript-sanitize-orphan-tool-messages (r2)

**Agent:** PM  
**Round:** 2 (QA spec report 1 remediation)  
**Deliverables:** `spec.md`, `tmp/app-llm-orchestrator-spec.md`, `tmp/backlog/app-031-transcript-sanitize-orphan-tool-messages.md`, `reflection-pm-r2.md`

## QA findings addressed

| ID | Fix |
|----|-----|
| **TICKET-001** | Ticket Expected files → `app/gm/orchestrator.py`, `app/tests/test_transcript_sanitize.py`. Run spec § Affected paths aligned; deferral footnote removed. |
| **SPEC-001** | R1 safe-prefix fallback pinned: walk per R2; if empty output from non-empty input → leading `system` messages + last `user` (else `[]`). Edge cases (empty input, tool-only) explicit. Added `test_tail_invalid_returns_safe_prefix` to run + domain test matrices. |
| **SPEC-002** | Mutability contract pinned: **non-mutating** — new list, shallow-copy dicts, caller list/dicts unchanged. Removed optional in-place wording. Added `test_sanitize_does_not_mutate_caller_list` to run + domain test rows. Domain § Helper contract mirrors run R1. |

## Decisions

- **Safe prefix vs narrow R1:** Chose explicit fallback algorithm + fixture test (QA option a) so APP-032 truncate→sanitize path has a documented floor when the tail is all invalid tool roles.
- **Mutability:** Non-mutating only — shared in-turn arrays and APP-032 reuse make in-place mutation risky; one negative test is enough for v1.

## Self-critique

- Holt fixture test name unchanged (`test_holt_session_shape`); tail/mutability tests are separate — Dev should not collapse into one case.
- Observability (R5) still optional/deferred to APP-034 — acceptable; not a round-1 finding.

## Did I miss anything?

- [x] Ticket scope / Expected files — TICKET-001 resolved
- [x] Domain spec / registry_gap — Helper contract + test rows; changelog r2
- [x] Run spec ↔ domain spec — R1, tests, Affected paths synced
- [x] Tests or AC mapped — ten pytest rows (eight original + mutability + tail fallback)
- [x] QA round 1 blockers — TICKET-001; SPEC-001 and SPEC-002 tightened

## Handoff

**Ready for:** QA spec re-review (round 2)

**Escalate human if:** Safe-prefix fallback should include last `assistant` content-only message (would widen APP-032 contract — not in v1 spec).
