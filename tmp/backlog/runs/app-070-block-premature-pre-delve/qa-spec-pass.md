# QA PASS: spec

**Task:** APP-070-block-premature-pre-delve  
**backlog_ticket:** APP-070  
**ticket_path:** tmp/backlog/app-070-block-premature-pre-delve-narration.md  
**Round:** 1  
**domain_spec_creation:** not_needed (registry_gap false; APP-070 § in existing `tmp/app-character-creation-spec.md`)

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`app-character-creation-spec.md`)
- [x] Acceptance criteria testable (compose C1–C5, drift D1–D2, test T1)
- [x] Code traces match repo (`_compose_creation_narration` ~520–537; `_check_creation_drift` ~192–234; `_auto_finalize` roster gate ~1018–1055; `strip_llm_status_tags` / `format_creation_status` in `creation.py`)
- [x] AGENTS.md / canon compliance (app-only; no canon mechanics drift)
- [x] Tests/commands listed (`test_creation_flow.py`, `test_creation_gating.py`)
- [x] registry_gap matches reality (false — character-creation spec owns paths)

## Acceptance criteria mapping

| Ticket AC | Spec / domain coverage | Testable |
|-----------|------------------------|----------|
| No `PRE_DELVE`, `RECEPTION_CHOICE`, or “registered Delver” until finalize + non-empty roster | C1–C5 compose (flavor-only); extends APP-009; terminology guards legitimate `WORLD_INTRO` footer | T1 + existing turn-8 `PRE_DELVE not in last` |
| `_check_creation_drift` → `premature_exploration_phase` for PRE_DELVE / preparation reception when `roster_len == 0` | D1a–D1c (+ scope intro); D2 optional for registration prose | Drift optional in T1 if compose strip is total |
| Regression test: mock LLM PRE_DELVE at SKILLS; FSM/UI unchanged | T1 `test_skills_turn_rejects_premature_completion_flavor` | Turn 4→5 golden path + bad flavor stub |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P0 bug; Expected files ⊆ domain owner |
| registry_gap | **PASS** | false per research + domain § Ticket boundaries |
| Drift policy | **PASS** | Behavior in domain spec § APP-070; run `spec.md` pointers only |
| Testability — compose | **PASS** | C2 flavor-only; C3/C4 patterns distinct from `_auto_finalize` body `is registered` |
| Testability — drift | **PASS** | D1b/D1c require `creation.active`; post-finalize `WORLD_INTRO` + roster excluded |
| Testability — T1 | **PASS** | Turn indices align with `INPUTS` in `test_creation_flow.py` |
| Scope vs APP-009/069/072/073 | **PASS** | Non-goals + domain boundaries table |
| Template completeness | **PASS** | Human playtest hints in `spec.md` § Stage 7 |
| Code traces | **PASS** | Line refs within ~20 lines of current `orchestrator.py` / `creation.py` |

## Notes (non-blocking)

- **D1 roster_len:** Section intro states triggers when `roster_len == 0`; per-row table omits explicit check — Dev should gate D1a–D1c with `len(roster)==0` (or rely on `_creation_drift_scope()` + `creation.active` during desk steps).
- **`"Yes"` at `SPELL_SCHOOLS`:** Domain § Other scenarios references APP-070 § Tests but only T1 (SKILLS) is automated; `spec.md` human playtest covers false-yes — acceptable; optional follow-up test not required by ticket AC.
- **`parse_narration_status_line`:** First `Phase:` / `Awaiting:` match in full composed narration — footer during creation is `Awaiting: *_INPUT` only (no `Phase:`), so leaked phase/awaiting in flavor is the primary drift signal pre-finalize.
- **Existing `strip_llm_status_tags`:** Bracket block `[Phase: PRE_DELVE | Awaiting: RECEPTION_CHOICE]` already stripped before sanitizer; APP-070 C3/C5 still required for prose and unbracketed markers.
- **Changelog:** APP-070 behavior draft lives in domain spec § APP-070; dated changelog entry on ticket **close** per ticket Spec sync (not a spec-gate blocker).
- **Session log:** `app/logs/session-2026-05-20.jsonl` gitignored — repro anchored on ticket + code trace (same as research).

**Verdict:** PASS — ready for Stage 3 (Dev plan + QA plan).
