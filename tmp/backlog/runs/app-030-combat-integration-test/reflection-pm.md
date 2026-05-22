# Reflection: PM — APP-030

**Date:** 2026-05-22  
**Stage:** PM spec draft  
**backlog_ticket:** APP-030

## What went well

- Research brief was actionable: live probe proved session-only V4 wording was wrong, identified `run_combat_monster_turns` + `is_pc_turn` loop, and mapped existing test modules so APP-030 does not duplicate APP-026/028 failure coverage.
- **registry_gap: false** — combat spec already listed APP-030 and V4 deferral; no master-spec registry change.
- APP-027 PM pattern (run `spec.md` + domain spec § + ticket Expected files) applied cleanly; V4 absorption is explicit in AC, R6, and APP-027 table row.

## Decisions

1. **I1-only AC:** Ticket AC "start → attack → end" maps to one required bridge test. I2/I3 orchestrator paths are optional stretch — exploration combat guard makes single-batch E2E misleading.
2. **Roster required:** Spec documents `_ensure_combat_roster_session` with `character_create` — not session-only "valid session" from original V4 skip text.
3. **V4 delete, not relocate:** Happy `start_combat` is step 2 of I1; keeping a separate `test_bridge_valid_grave_ghoul` would duplicate assertions. Remove skip test from validation module; update APP-027 V4 row to "absorbed → I1".
4. **`combat_attack` not `combat_action`:** I1 uses exploration tool name and matches APP-026 wire path; auto-chain and phased verify stay APP-029/090.
5. **No LLM in scope:** Mechanical bridge integration only; narration verify and `_combat_turn` paths explicitly non-goals to keep Dev scope within one new module + V4 removal.
6. **Initiative nondeterminism:** Turn-advance loop with cap — no bridge `seed` API required for this ticket.

## Risks flagged for QA / Dev

- **Turn cap too low:** If initiative loop exceeds `max_rounds`, I1 flakes — Dev should assert clear failure message; QA spec should require cap ≥ 5.
- **Hardcoded PC id:** Prefer resolving from `status["combat"]` after `character_create` rather than assuming `sammy` unless engine guarantees slug.
- **V4 removal regression:** QA must confirm V1–V3/V5–V8 still green and no duplicate happy-start gap after delete.
- **I2 temptation:** Dev may want orchestrator chain in same PR — spec marks optional; QA should not block close on I2 absence.

## QA spec pass expectations

- Verify ticket Expected files match spec affected paths (`test_combat_integration.py` explicit).
- Confirm AC does not require hit/damage, LLM mock paths, or APP-029 auto-chain.
- Check V4 absorption is test-plan item (validation module loses skip; I1 covers happy start).
- Cross-check APP-027 domain table V4 row points to APP-030 I1.

## Handoff

- **Run spec:** `tmp/backlog/runs/app-030-combat-integration-test/spec.md`
- **Domain spec:** `tmp/app-combat-play-spec.md` § Combat integration golden path (APP-030)
- **Ticket:** expanded AC + Expected files
- **Next:** QA spec adversarial pass → Dev plan → impl
