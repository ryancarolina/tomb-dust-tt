# Reflection: PM — APP-019 spec

**Agent:** PM
**Round:** 1
**Deliverables:** spec.md, app-session-persistence-spec.md (§ APP-019), ticket Expected files, reflection-pm.md

## Completed

- Confirmed `registry_gap: false` — session persistence spec already owns `setup_new_game` failure path; expanded § New game failure (APP-019) in domain spec.
- Expanded ticket Expected files: `orchestrator.py`, optional `ui/app.py`, `test_setup_new_game_failure.py`; removed `main.py` (no session logic).
- Defined three failure contexts (command, death, run_ended) with distinct copy templates and shared cause mapping + `[Awaiting: new game]` retry footer.
- Specified JSONL dual-logging via existing `_emit_recovery_narration` (APP-071 parity); rejected toast (no infrastructure).
- Mapped six engine error patterns to player `{cause_line}`; deferred verbatim errors to JSONL `error` only.
- Added tests T-019a–f and human playtest hints TC-A–D.

## Self-critique

- Death/run_ended failure copy is structurally similar (intentional — both are post-run restart failures); Dev may factor shared tail into one helper with context-specific lead lines.
- Optional UI R6 (`Error — try again` status) left ambiguous on purpose until manual QA; could have pinned orchestrator sentinel string more strictly.
- Did not verify every bridge error string from wipe/init failures — default bucket covers unknowns but mapping table may need expansion after impl.

## Did I miss anything?

- [x] Ticket scope / Expected files — orchestrator added; main.py removed
- [x] Domain spec / registry_gap / AGENTS.md — no new spec; session persistence updated
- [x] Code paths not traced — death, run_ended, command paths covered per research brief
- [x] Tests or AC not mapped — T-019a–f + AC bullets in R1–R7
- [ ] APP-014 human-test “Could not start game after partial creation = blocker” — APP-019 makes that message actionable when it occurs; QA should not treat absence of errors as proof setup never fails

## Handoff

**Ready for:** QA spec review (round 1)
**Escalate human if:** QA insists on toast UI — requires new ticket/infrastructure; narration-only closes ticket AC per APP-071 precedent
