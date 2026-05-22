# Reflection: QA — APP-041 spec (round 1)

**Agent:** QA  
**Round:** 1  
**Deliverables:** `qa-spec-report-1.md`, `reflection-qa-spec.md`

## Completed

- Read `spec.md`, ticket, domain spec § APP-041, `research-brief.md`, PM reflection
- Verified code paths: `app/ui/app.py` turn → panel vs TTS split; `scene.py` `parse_scene` pipeline; `queue.py` line vs text routing
- Ran live `parse_scene` probes for research leak matrix + AV-GRID preservation
- Checked CLI bypass: `cmd_speak.py` `--text` / `--lines` vs `--scene`; `cmd_narrate.py` push path
- Compared ticket Expected files and AC against spec/domain spec and APP-065 FAIL precedent for allow-list mismatch

## Self-critique

- Did not run full pytest suite (spec-stage review; no implementation yet) — appropriate for this gate
- Did not trace `cmd_speak --beat-id` with stored `speak_lines` payload — possible bypass but dev-only; noted in thinking, not elevated to finding
- SPEC-002 (inline unbracketed Location/Phase mid-line) marked minor; could be major if LLM prompt encourages inline pipe footers — judged low from `system_prompt.py` whole-line pattern in research

## Did I miss anything?

- [x] Ticket scope / Expected files — **FAIL** TICKET-001
- [x] Domain spec / registry_gap / AGENTS.md — PASS; no new domain spec needed
- [x] Acceptance criteria testability — core AC yes; panel AC missing on ticket
- [ ] Full pytest run — deferred to plan/impl QA
- [x] CLI / alternate speak paths — SPEC-001 bypass gap

## Orchestrator recommendation

**Dispatch PM agent (spec revision round 1)** with path to `qa-spec-report-1.md`. Blockers are ticket hygiene (Expected files + second AC) and R3 CLI scope — quick PM fix, no research re-run needed. Re-dispatch QA spec round 2 after PM updates ticket + spec.
