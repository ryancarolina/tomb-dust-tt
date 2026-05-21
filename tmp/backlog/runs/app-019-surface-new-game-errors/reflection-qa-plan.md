# Reflection: QA plan — round 1

**Role:** QA (plan gate)  
**backlog_ticket:** APP-019  
**Deliverable:** `qa-plan-pass.md` (PASS)

## Completed

- Reviewed `plan.md` against ticket APP-019, `spec.md` (PM r2 / `qa-spec-pass.md` round 2), `research-brief.md`, domain § New game failure, and live code in `app/gm/orchestrator.py`.
- Independently verified failure gaps at command (~535–539), death (~424–432), run_ended (~558–564), and combat caller `_emit_narration` pattern (~1586, ~1680).
- Confirmed plan resolves spec QA SPEC-001 via `PlayerDeathResult.already_emitted` and dual combat-site caller guards.
- Checked plan file table ⊆ ticket Expected files; domain spec close is release-only.
- Mapped T-019a–f to APP-071 `test_session_resume_failure.py` mock patterns (feasible without impl).
- Wrote `qa-plan-pass.md` with verdict **PASS**.

## Self-critique

- Did not run pytest (no impl yet); review is static only.
- Did not deep-read `test_setup_new_game_lifecycle.py` / `test_creation_block_on_new_game.py` for T-019f fixture conflicts — assumed `orchestrator` + `isolated_workspace` conftest patterns from plan citations are sufficient.
- R6 UI path in `app/ui/app.py` not line-traced — optional defer per spec; acceptable for plan gate.

## Missed?

- [x] Ticket Expected files vs plan § Files
- [x] All ticket AC rows in § Acceptance mapping
- [x] Spec R1a/R1b emit ownership vs plan tasks §3 + §5 — **aligned**
- [x] R5 cause table vs domain spec — **aligned**
- [x] Combat `None` early exits preserved — **noted in plan + dev reflection**
- [x] APP-014/015/071 non-goals — **documented in plan**
- [ ] Full combat integration test for death failure — explicitly out of scope (T-019c direct handler + caller sim)
- [ ] Automated run_ended/death **success** regression — manual TC-D only; not escalated (spec QA accepted)

## Handoff

**Ready for:** Dev workstreams + implementation (Stage 4).

Do **not** dispatch implementation until orchestrator updates `status.md` plan QA checkbox.

**Blocker count:** 0.
