# QA PASS: spec — round 1

**Task:** app-083-mechanical-truth-narration-gate  
**backlog_ticket:** APP-083  
**ticket_path:** [tmp/backlog/app-083-creation-flavor-verification-gate.md](../../app-083-creation-flavor-verification-gate.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (registry_gap false; orchestrator + character-creation specs updated)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-llm-orchestrator-spec.md` primary; `tmp/app-character-creation-spec.md` Phase 1 rule matrix)
- [x] Phase 1 creation AC testable — N1–N10, creation rule table, wire-point table, pytest commands
- [x] Code traces match repo (research-brief: nine creation flavor call sites, no `narration_verify.py`, Sumpty L4743/L4749/L4755, `strip_flavor_equipment_claims` spec-only)
- [x] AGENTS.md / canon compliance (app-only gate; catalogs from `creation.py` / `build/data/spells/` — no mechanics drift)
- [x] Tests/commands listed (`test_narration_verify.py` new + creation regression trio)
- [x] `registry_gap: false` — orchestrator spec owns framework; creation spec owns Phase 1 rule matrix
- [x] PM batch-close scope documented — Phase 1 creation only; Phases 2–3 deferred in run spec + domain spec § Phase 1 batch close
- [x] Verify boundary explicit — flavor only; `_auto_finalize` code footer unchanged
- [x] APP-075 error skip path documented — `error=` re-present skips LLM; verify gate N/A

## Phase 1 AC coverage (ticket → run spec → domain)

| Ticket AC (Phase 1) | spec.md | Domain spec |
|---------------------|---------|-------------|
| `TurnTruth` + `build_creation_turn_truth` | N1–N2 | Orchestrator § `TurnTruth`; creation § allowed claims by step |
| `format_turn_truth_for_prompt` in `_creation_flavor_messages` | N3, N7 | Orchestrator § Truth-as-context; creation § Prompt block |
| `verify_narration` creation rule set | N4 | Orchestrator § rule classes; creation § verify fail examples + denylist |
| `narrate_with_verification` on all creation flavor paths | N5–N6 | Creation § Wire points (9 symbols); orchestrator § Where it wires in |
| Sumpty L4743/L4749/L4755 fail; mock retry pass | Test plan | Orchestrator § Tests APP-083; creation § Regression targets |
| Supersede APP-082 / APP-078/059/073 creation slices | Goals, N9 | Creation § Pass gate policy + Subsumed tickets |
| Verify→retry→publish canonical policy | Goals | Orchestrator § Mechanical-truth narration gate (pipeline + policy) |

## Adversarial notes (non-blocking)

1. **Ticket close criteria drift** — Ticket § Acceptance criteria still marks Phase 2–3 and exploration/combat unit tests as “required for close”; run spec § Batch close scope and orchestrator § Phase 1 batch close override. Dev plan and `release --done` must use **Phase 1 AC only** until PM updates ticket or splits follow-on tickets.
2. **Run spec N5 vs domain retry budget** — `spec.md` N5 cites only `NARRATION_VERIFY_MAX_RETRIES` (default 5); orchestrator spec § Config + § `narrate_with_verification` add shared `NARRATION_LLM_MAX_ATTEMPTS` (6) and APP-079 `handle_finish_reason_length` before verify. Dev plan must treat orchestrator spec as normative for loop order; align run spec N5 wording on close or in plan round 1.
3. **APP-079 parallel batch** — Neither helper nor `test_llm_truncation_recovery.py` exists yet. Domain spec allows 079 to land standalone; 083 must call the same helper inside step 3 — Dev plan should define stub vs shared PR with APP-079 to avoid duplicated length logic.
4. **Logging spec sync deferred** — `tmp/app-logging-qa-spec.md` lacks `narration_verify_*` events; N8 defers sync. Payload fields are in orchestrator § Observability — sufficient for impl; sync logging spec on ticket close.
5. **F4 vs truth block** — Creation spec F4 still documents `_committed_state_flavor_block()` append; APP-083 Phase 1 § Prompt block says truth replaces committed-only context. Implementers should fold committed fields into `format_turn_truth_for_prompt` and drop duplicate block — recommend one-line F4 cross-reference on close.
6. **Sumpty fixtures** — Regression cites session lines but domain Tests pattern (APP-080) prefers committed pytest excerpts, not gitignored JSONL in CI. Dev should embed L4743/L4749/L4755 flavor strings in `test_narration_verify.py`.
7. **`AllowedClaims` / `ForbiddenClaims` shape** — TurnTruth fields named but not typed; creation § allowed-by-step table is enough for Phase 1; Dev may use dict/list dataclass fields.

## Summary

Run `spec.md`, research brief, and updated domain specs (`app-llm-orchestrator-spec.md` § Mechanical-truth narration gate + APP-079 coordination; `app-character-creation-spec.md` § Mechanical-truth narration gate Phase 1) fully cover Phase 1 creation implementation: architecture, per-step verify rules, wire points, exhaustion fallback, observability, and tests. No registry gap. Spec package is implementation-ready; ticket close wording and run-spec N5 summary should align with domain spec during Dev plan or ticket close.

## Re-review focus

_Re-review only if PM revises batch-close scope, removes APP-079 coordination from orchestrator spec, or materially changes verify rule matrix / wire-point table._
