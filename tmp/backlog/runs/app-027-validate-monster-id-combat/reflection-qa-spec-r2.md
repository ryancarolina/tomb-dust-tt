# Reflection: QA — APP-027 spec (round 2)

**Agent:** QA (adversarial spec review)  
**Round:** 2  
**Deliverables:** `qa-spec-pass.md`, `reflection-qa-spec-r2.md`

## Completed

- Re-read `qa-spec-report-1.md` findings (TICKET-001, SPEC-001 blockers; SPEC-002–004 minors).
- Verified PM r2 fixes in ticket Expected files, run `spec.md`, and `tmp/app-combat-play-spec.md` § APP-027.
- Re-traced orchestrator `_llm_loop` L2573–2576 vs `_execute_tool("start_combat")` L2684–2685; confirmed `_dispatch_like_llm_loop` helper exists in `test_tool_args.py`.
- Confirmed engine `load_monster_json` error substring matches APP-028 contract.
- Wrote **PASS** — all round 1 items resolved; no new blockers.

## Self-critique

- Did not run pytest — spec review only; implementation QA will confirm baselines.
- Accepted `play/tomb_gm/` glob for V9 engine test module without reading hook script — consistent with PM r2 and sibling tickets.
- Non-blocking notes on R1/R3 error-string duality and domain L369 wording — did not escalate to FAIL because run spec + ticket are unambiguous on dedicated module and V5 message.

## Did I miss anything?

- [x] TICKET-001 — test module in Expected files
- [x] SPEC-001 — V5 `_dispatch_like_llm_loop`; R3/R4 wire prose
- [x] SPEC-002 — engine-only R1
- [x] SPEC-003 — V8 integration contract
- [x] SPEC-004 — V9 vs CLI split
- [x] Domain spec sync + r2 changelog
- [ ] Beat `pending_start` path — covered in R4 wire table; not re-traced in orchestrator L2487

## Handoff

**Ready for:** Dev plan (Stage 4) + QA plan gate  
**Escalate human if:** Product wants duplicate validation inside `_execute_tool` — spec forbids (conflicts with APP-080)
