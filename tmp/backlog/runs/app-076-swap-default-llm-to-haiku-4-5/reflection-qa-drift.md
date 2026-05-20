# Reflection: QA — APP-076 drift

**Agent:** QA (drift)  
**Round:** 1  
**Deliverables:** `drift-check.md`, `reflection-qa-drift.md`, ticket close update

## Completed

- Re-read `app/config.yaml` and `tmp/app-shell-config-spec.md` shipped-default table (L23) + changelog (L79) — `llm.model` is `anthropic/claude-haiku-4.5` in both with no other `llm` key drift.
- Traced read-only consumers: `main.load_config()` → `Orchestrator.self.model` (L91) → `log_llm_request` (L84–85) → UI `Model:` label (`ui/app.py` L246–247).
- Confirmed code fallback documentation unchanged (`anthropic/claude-sonnet-4` when key omitted) per ticket non-goals.
- Ran `cd app; python -c "import main"` — exit 0.
- Wrote `drift-check.md` with **PASS** verdict; updated ticket status `done` + Closed 2026-05-20 with AC notes.

## Self-critique

- Did not run live OpenRouter calls or PyGame — config-only drift; runtime model availability deferred to human playtest.
- Did not run `claim_ticket.py release APP-076 --done` — left for orchestrator per drift-stage convention.
- Historical Flash Lite strings in APP-046 artifacts and run-folder pre-impl docs are expected; only live config + domain spec table are drift gates.

## Did I miss anything?

- [x] Ticket scope / Expected files (`config.yaml`, domain spec only)
- [x] Domain spec / AGENTS.md drift policy (spec ↔ config on `llm.model`)
- [x] Code paths traced (config → orchestrator → logger → UI)
- [x] Tests mapped to AC (import smoke; human R3/R4 in playtest plan)
- [ ] OpenRouter runtime model-id proof — human Stage 7
- [ ] `release --done` CLI — orchestrator

## Handoff

**Ready for:** Orchestrator `release APP-076 --done` + Stage 7 commit; human tester runs `human-test-plan.md`.

**Escalate human if:** UI label or JSONL shows a model other than `anthropic/claude-haiku-4.5` after fresh launch with unmodified config — would indicate override or wiring regression outside APP-076 scope.
