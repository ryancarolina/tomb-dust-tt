# QA PASS: spec

**Task:** APP-019-surface-new-game-errors
**backlog_ticket:** APP-019
**ticket_path:** tmp/backlog/app-019-surface-new-game-failure-errors.md
**Round:** 2
**domain_spec_creation:** not_needed

**Verdict:** PASS

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-session-persistence-spec.md` § New game failure + § Emit ownership)
- [x] Acceptance criteria testable (R0–R7, T-019a–f, manual TC-A–D)
- [x] Code traces match repo (`process_turn` 535–539, `_handle_player_death` 404–433, run_ended 558–564, combat callers 1586–1591 / 1680–1684, `_emit_recovery_narration` 309–311)
- [x] AGENTS.md / canon compliance (app-only; no parallel rules; orchestrator + tests Expected files)
- [x] Tests/commands listed (`test_setup_new_game_failure.py`; pytest `-k` filter in spec)
- [x] registry_gap false — domain § APP-019 authoritative; run `spec.md` detail via R1a/R1b link

## Round 1 findings — resolution

| ID | Round 1 | Round 2 status |
|----|---------|----------------|
| **SPEC-001** | Death-path emit contract ambiguous (double JSONL / drift) | **Resolved** — `spec.md` R1a/R1b: context B `_emit_recovery_narration` inside `_handle_player_death`; `(message, already_emitted)` (or equivalent); both combat sites MUST skip `_emit_narration` when emitted; forbidden patterns explicit. Domain § Emit ownership mirrors contract. |
| **SPEC-002** | T-019c/d JSONL asserts thin; combat integration implied | **Resolved** — T-019c direct `_handle_player_death` + caller-branch assert; T-019d dual JSONL; T-019e covers A **and** B drift silence. |
| **SPEC-003** | Stale Expected-files note; cause-line drift | **Resolved** — note removed; R5 table aligned with domain § Engine error → cause line. |

## Gates (round 2)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-019 `in_progress`; Expected files = orchestrator, optional `app/ui/app.py`, `test_setup_new_game_failure.py` |
| registry_gap | **PASS** | false |
| AC testability | **PASS** | Ticket AC ↔ R2–R5 copy + `[Awaiting: new game]`; blocked items from R1 cleared |
| Code traces | **PASS** | Silent-success paths and caller `_emit_narration` pattern match PM r2 problem statement |
| Domain spec sync | **PASS** | Run spec ↔ domain § APP-019 — contexts, emit ownership, mapping, tests |
| AGENTS.md | **PASS** | Session persistence domain; no `main.py` scope creep |
| Tests/commands | **PASS** | T-019a–f feasible (APP-071 `test_session_resume_failure.py` style for JSONL mocks) |

## Acceptance criteria mapping

| Ticket AC | Spec | Testable | QA |
|-----------|------|----------|-----|
| Show clear error with cause + retry hint when new game fails | R0–R5, contexts A/B/C | T-019a–d, T-019e, manual TC-A–C | **PASS** |

## Notes (non-blocking)

- Early `_handle_player_death` exits (`None` — no death / corpse failure) remain implicit; Dev plan should preserve `None` vs tuple discrimination at combat call sites.
- R6 optional UI sentinel still unpinned (deferred per PM r2).
- `test_setup_new_game_failure.py` does not exist yet — expected at implementation stage.

## Handoff

**Ready for:** Dev plan (inputs: `spec.md`, this PASS, `reflection-qa-spec-r2.md`)
