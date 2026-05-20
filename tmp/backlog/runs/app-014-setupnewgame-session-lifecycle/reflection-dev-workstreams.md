# Reflection: Dev — APP-014 workstreams

**Agent:** Dev (workstreams)  
**Round:** 1  
**Deliverables:** `workstreams.md`, `reflection-dev-workstreams.md`

## Completed

- Read `plan.md`, `spec.md`, ticket APP-014, qa-plan-pass notes, and APP-068 / APP-057 workstream precedents.
- Split implementation into **WS1** (orchestrator: L1 `end_session` + L1b `force_close_all_sessions` before `wipe_all_data`) and **WS2** (new `test_setup_new_game_lifecycle.py`: T-014a–c).
- Mapped plan §1 → WS1, plan §2 → WS2; deferred plan §3 domain spec + `release --done` to post-impl release.
- Documented read-only paths (`bridge.py`, `ui/app.py`, `main.py`), batch coordination (APP-015 prepend risk), and prompt seeds per stream.

## Stream decision

| Option | Verdict |
|--------|---------|
| **Single stream** | Viable — ~6 LOC orchestrator + one test file; ticket is narrow |
| **WS1 + WS2 (chosen)** | Matches plan’s explicit code vs tests sections and APP-068/057 precedent; WS2 pytest depends on WS1 ordering |
| WS3 for spec | Rejected — release-step only, not code |
| WS3 for caller `ok` guards | Rejected — **APP-019** per plan open questions |

Did **not** split L1 vs L1b into separate streams — same function, same deploy unit, no import boundary.

## Self-critique

- Ticket **Expected files** still lists `app/main flow` but not `test_setup_new_game_lifecycle.py` — qa-plan-pass flagged; impl should add path to ticket before `impl-check` or at release (not blocking workstreams).
- T-014c fixture steps intentionally point at `test_death_rules.py` without duplicating full fixture recipe — WS2 impl must read death_db pattern (plan/reflection-dev-plan risk).
- WS1 has no mandatory pytest gate before WS2; smoke-only optional — orchestrator should not block WS1 on lifecycle file existing.

## Did I miss anything?

- [x] Plan §1–2 covered across WS1/WS2
- [x] Spec L1–L6 and T-014a–c mapped
- [x] Out-of-scope tickets listed (APP-015, APP-016, APP-019)
- [x] Bridge L1b nuance (explicit force_close on `not ok`, not only exception) in WS1 constraints
- [x] Caller paths D/E documented as verify-only in WS1
- [x] No code implemented (workstreams-only stage)

## Handoff

**Ready for:** Orchestrator dispatches impl subagents — **WS1 first**, then **WS2**  
**Escalate human if:** WS2 exposes bridge API gap requiring `bridge.py` edit (plan says none expected) or APP-015 lands same function before WS1 merges
