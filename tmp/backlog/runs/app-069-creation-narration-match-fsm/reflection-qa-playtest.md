# Reflection: QA — human playtest plans (APP-069 / 070 / 072)

**Agent:** QA (human playtest plan)  
**Round:** 1  
**Deliverables:** `human-test-plan.md` in each run folder; this shared reflection

## Completed

- Wrote PyGame manual plans mapped 1:1 to ticket acceptance criteria for:
  - **APP-069** — Rick/Undead flavor repro + Dumpy apprentice gated-body golden path
  - **APP-070** — Dumpy skills premature “registered Delver” / `PRE_DELVE` repro + false `yes` at schools
  - **APP-072** — Caddy/Dumpy NAME→RACE duplicate-table repro + invalid race re-prompt
- Cross-linked the three plans and listed optional pytest commands from domain spec.
- Entry point aligned with [app/README.md](../../../app/README.md): `cd app && python main.py`.

## Plan design choices

| Choice | Rationale |
|--------|-----------|
| Shared reflection in APP-069 folder only | Avoid triplicate QA meta; 070/072 plans link here |
| TC overlap called out explicitly | APP-069 TC-3 spot-checks PRE_DELVE; APP-070 owns full gate |
| JSONL steps optional | Live LLM variance; drift events may not fire on compliant models |
| Historical input strings preserved | Ticket evidence (`medicine, spellcasting, endurance`, Caddy 16:44) aids regression bisect |

## Self-critique

- Did **not** execute manual PyGame passes in this round — plans are ready for human tester.
- Live OpenRouter may not reproduce `finish_reason: length` on RACE every run; TC-1 step 7 for APP-072 is explicitly optional.
- APP-059 Description column removal not required for APP-072 close; plans use `\| Race \| Adjustments \|` fingerprint per spec.

## AC coverage matrix

| Ticket | Manual TCs | Automated backup cited |
|--------|------------|-------------------------|
| APP-069 | TC-1–4 | `test_roll_stats_flavor_reflects_committed_race`, `test_full_creation_apprentice_caster` |
| APP-070 | TC-1–4 | `test_skills_turn_rejects_premature_completion_flavor` (name may vary) |
| APP-072 | TC-1–4 | `test_creation_tables.py`, `test_race_narration_single_table_header` |

## Handoff

- **Human tester:** Run plans in order **072 → 069 → 070** on one fresh `new game` (race dedup first), then separate `Rick`/`undead` session for APP-069 TC-1.
- **Sign-off:** Fill sign-off tables in each `human-test-plan.md`; log failures with JSONL timestamp + narration screenshot if possible.
- **Escalate:** If live LLM still injects tables into **body** (not flavor), APP-069 Phase 2 assumption breaks — reopen impl, not just playtest.

## Paths written

| Path |
|------|
| `tmp/backlog/runs/app-069-creation-narration-match-fsm/human-test-plan.md` |
| `tmp/backlog/runs/app-069-creation-narration-match-fsm/reflection-qa-playtest.md` |
| `tmp/backlog/runs/app-070-block-premature-pre-delve/human-test-plan.md` |
| `tmp/backlog/runs/app-072-llm-truncation-race-tables/human-test-plan.md` |
