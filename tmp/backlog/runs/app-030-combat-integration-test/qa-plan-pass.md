# QA PASS: plan — round 1

**Task:** app-030-combat-integration-test  
**backlog_ticket:** APP-030  
**ticket_path:** [tmp/backlog/app-030-combat-integration-test.md](../../app-030-combat-integration-test.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (qa-spec-pass round 1 confirmed `registry_gap: false`)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

**Blocker count:** 0

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec = `app-combat-play-spec.md`
- [x] Ticket domain spec matches plan (`spec.md`, `tmp/app-combat-play-spec.md` § Combat integration golden path APP-030)
- [x] Acceptance criteria testable — I1 bridge golden path, V4 absorption, domain spec changelog on close
- [x] Code traces match repo (Flows A–D spot-checked independently; symbols and control flow correct)
- [x] AGENTS.md / canon compliance — test-only; no `app/gm/` production edits; `grave-ghoul` canon JSON present under `build/data/monsters/`
- [x] Tests/commands listed — primary I1 module + APP-026/027/028 regression + engine reference
- [x] Plan files ⊆ ticket Expected files (strict subset + domain spec on close)
- [x] registry_gap matches reality (N/A at plan gate — spec QA confirmed `false`)

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/tests/test_combat_integration.py` — new helpers + I1 | Yes |
| `app/tests/test_combat_monster_validation.py` — delete V4 skip (L91–94) | Yes |
| `tmp/app-combat-play-spec.md` — remove § Open work APP-030, append done changelog | Yes (ticket § Spec sync) |

Explicit out-of-scope: orchestrator I2/I3, APP-029 auto-chain, bridge `seed` API, DRY `helpers.py` refactor, hit/damage assertions, production code — no unauthorized paths.

## Code trace audit

Independent spot-check against live repo:

| Symbol / flow | File | Present | Plan ref |
|---------------|------|---------|----------|
| `bridge` fixture + `make_isolated_workspace` | `app/tests/conftest.py` L24–36 | Yes | Flow A step 1 |
| `campaign_new` / `session_start` tolerance | `test_combat_monster_validation.py` L13–17 | Yes | Flow A steps 2–3 |
| `character_create` + auto `roster_set` slot 1 | `bridge.py` L466–541 | Yes | Flow A step 4 |
| `start_combat` → `validate_monster_specs` + engine | `bridge.py` L244–261 | Yes | Flow C step 2 |
| `combat_attack` direct service (no finalize) | `bridge.py` L265–279 → `combat.py` L625–719 | Yes | Flow C step 7 |
| `combat_end` → `{ok: true}` | `bridge.py` L281–284 → `combat.py` L967–995 | Yes | Flow C step 8 |
| `run_combat_monster_turns` → `run_monster_turns_until_pc_or_end` | `bridge.py` L314–324 → `combat.py` L834–864 | Yes | Flow B step 3 |
| `is_pc_turn` reads `turn_id` + combatant `kind` | `combat_fsm.py` L62–70 | Yes | Flow B step 2 |
| Nested combat shape in status | `cmd_core.py` L214–217 | Yes | Flow B step 1 |
| V4 skip awaiting APP-030 | `test_combat_monster_validation.py` L91–94 | Yes | Flow D |

Plan line anchors (e.g. `bridge.py` L244–324, validation L91–94) match current file; minor drift acceptable — use symbol search during impl.

## qa-spec-pass (round 1) → plan resolution

| Spec QA item | Plan handling |
|--------------|---------------|
| Adversarial 1 — fixture fail-fast on `character_create` | Flow A step 5; sketch asserts `{ok}`, `"id" in created` before combat |
| Adversarial 2 — no placeholder `skill_ids` | Flow A step 4: name + `background="militia"` only (matches domain fixture table) |
| Adversarial 3 — combatant resolution by kind/prefix | Flow C step 6 / R5; no hardcoded `sammy` |
| Adversarial 4 — distinct `pytest.fail` messages | Flow B steps 5–6; sketch separates combat-ended vs cap-exceeded |
| Adversarial 5 — DRY duplication acceptable v1 | Out of scope; optional follow-up noted |
| Adversarial 6 — domain § Open work on close | Task 3 close checklist |

## Ticket AC → plan / tests

| Ticket AC | Plan coverage | Test / mechanism |
|-----------|---------------|------------------|
| **I1** — bridge golden path with isolated workspace, roster PC, `grave-ghoul:1` | Task 1 + Flows A–C; R1–R5 | `test_bridge_combat_start_attack_end`; pytest step 1 |
| **V4 absorption** — remove skipped `test_bridge_valid_grave_ghoul` | Task 2 + Flow D | Delete L91–94; regression step 2 |
| Domain spec § APP-030 + changelog on close | Task 3 | Remove § Open work L221; append done entry |

### Requirement map

| ID | Plan locus | Test |
|----|------------|------|
| R1 | New module + helpers | I1 |
| R2 | `_ensure_combat_roster_session` (Flow A) | I1 step 1 |
| R3 | `test_bridge_combat_start_attack_end` (Flow C) | I1 |
| R4 | `_advance_to_pc_turn` (Flow B) | I1 steps 3–5 |
| R5 | Combatant resolution by `kind` / `grave-ghoul` prefix | I1 step 6 |
| R6 | V4 deletion (Flow D) | validation module regression |
| R7 | `conftest.py` `bridge` fixture only | implicit in I1 |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-030 `in_progress`; Expected files complete |
| Plan ⊆ Expected files | **PASS** | Three paths only; no TICKET-001 gap |
| Code traces | **PASS** | Flows A–D verified independently |
| Spec R1–R7 coverage | **PASS** | All requirements mapped to locus + tests |
| AC testability | **PASS** | I1 + V4 removal + close process |
| qa-spec-pass alignment | **PASS** | All round 1 adversarial notes addressed |
| Layer choice | **PASS** | Bridge-only I1 avoids APP-026 gate mocks and exploration batch guard |
| Non-goals | **PASS** | I2/I3, LLM, auto-chain explicitly deferred |

## Notes (non-blocking — impl QA)

1. **Stale combatants in sketch:** Suggested helper uses pre-advance `combatants` for `attacker_id`/`target_id` after `_advance_to_pc_turn`; Dev should re-read `status["combat"]["combatants"]` from the returned status (R5 intent unchanged).
2. **Outer loop vs engine loop:** One `run_combat_monster_turns()` call often suffices (engine loops to PC internally); outer `max_rounds=5` is defensive — acceptable per R4.
3. **Post-attack active assert:** Plan step 7 optional `status.combat is not None` before `combat_end` — recommended; catches silent finalize regressions on direct `combat_attack`.
4. **One-hit kill edge:** If PC one-shots ghoul, `combat_attack` may still leave combat active until `combat_end` (no auto-finalize on bridge path) — plan assertions align with qa-spec evidence.
5. **Initiative flake:** If I1 flakes in CI despite cap, escalate bridge `seed` API as follow-up ticket — plan already documents deferral.

**Verdict:** PASS — ready for workstreams + implementation.
