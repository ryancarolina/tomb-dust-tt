# QA PASS: plan — round 1

**Task:** app-026-combat-attack-gating  
**backlog_ticket:** APP-026  
**ticket_path:** [tmp/backlog/app-026-combat-attack-gating.md](../../app-026-combat-attack-gating.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (qa-spec-pass round 2 confirmed `registry_gap: false`)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

**Blocker count:** 0

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec = `app-combat-play-spec.md`
- [x] Ticket domain spec matches plan (`spec.md`, `tmp/app-combat-play-spec.md` § Combat attack gating)
- [x] Acceptance criteria testable (R1–R5 → G1–G8 + G6b; pytest commands listed)
- [x] Code traces match repo (symbols and flows spot-checked independently; line refs approximate but correct)
- [x] AGENTS.md / canon compliance (app-layer gate only; no engine/`build/` drift; Expected files respected)
- [x] Tests/commands listed (`test_combat_attack_gating.py`, APP-028 regression, engine combat pair)
- [x] Plan files ⊆ ticket Expected files (strict subset + domain spec on close)
- [x] registry_gap matches reality (N/A at plan gate — spec QA confirmed `false`)

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/gm/orchestrator.py` — `_resolve_combatant_id_for_gate`, `_gate_pc_attack`, R2/R3 wire | Yes |
| `app/tests/test_combat_attack_gating.py` — G1–G8 + G6b | Yes |
| `app/gm/tools.py` — optional R5 description | Yes (optional) |
| `tmp/app-combat-play-spec.md` — checklist + changelog on `release --done` | Yes (ticket § Spec sync) |

Explicit out-of-scope: turn-order enforcement in gate, removing `combat_attack` from exploration `TOOLS`, engine changes (APP-027), monster `monster_attack`, APP-030 golden path — no unauthorized paths.

## Code trace audit

Independent spot-check against live `app/gm/orchestrator.py`:

| Symbol / flow | File | Present (pre/planned) | Plan ref |
|---------------|------|------------------------|----------|
| `_execute_tool` combat-only guard before exploration tools | `orchestrator.py` L2538–2544 | Yes | Flow B |
| `_execute_tool` → direct `bridge.combat_attack` | `orchestrator.py` L2609–2612 (planned gate wire) | Yes (plan delta accurate) | Flow A / R2 |
| `_execute_combat_action` no initiative check | `orchestrator.py` L2378–2402 (planned ATTACK gate first) | Yes | Flow C / R3 |
| `_combat_active_in_db` reads `bridge.status().combat` | `orchestrator.py` L484–488 | Yes | G1 setup note |
| Engine `action.upper().strip() == "ATTACK"` | `combat.py` L714–715 | Yes | SPEC-001 / G8 |
| Engine `_resolve_combatant_id` semantics | `combat.py` L476–485 | Yes | Task 1 mirror |

Plan line anchors (~2315, ~2530) drift ~30–80 lines from current file; symbol names and control flow are correct.

## qa-spec-pass (round 2) → plan resolution

| Spec QA item | Plan handling |
|--------------|---------------|
| SPEC-001 ATTACK case normalization | R3 + Flow C **Case rule**; G8 lowercase `"attack"` |
| SPEC-002 G4 explicit gate error | G4 asserts `"no active combat for session"` |
| SPEC-003 G5 fixture clarity | G5/G8: `turn_id="pc1"`, `initiative=[{id:"m1"}]` |
| SPEC-004 G6b combat-loop happy path | G6b + `_combat_status()` factory with required keys |
| Adversarial G6b fixture detail | Shared `_combat_status()` lists `combat`, `turn_id`, `initiative`, `combatants` |
| Adversarial G7 regression looseness | Full-module command `test_combat_failure_narration.py -q` (G7) |

## Ticket AC → plan / tests

| Ticket AC | Plan coverage | Test / mechanism |
|-----------|---------------|------------------|
| Before attack: require `status.combat` | R1 step 1; R2/R3 wire; Flows A/C | G1, G4; mock `bridge.combat_attack` / `combat_action` not called |
| Attacker in initiative | R1 step 3; initiative id set | G2, G5, G8, G6b |
| Wire `combat_attack` + `combat_action` ATTACK | R2, R3; Flows A/C | G1, G4–G6, G6b, G8 |
| Spec sync on close | §6 domain spec on `release --done` | checklist + changelog |

### Requirement map

| ID | Plan locus | Test |
|----|------------|------|
| R1 | `_gate_pc_attack`, `_resolve_combatant_id_for_gate` | G2, G3 |
| R2 | `_execute_tool` `combat_attack` branch | G1, G6 |
| R3 | `_execute_combat_action` ATTACK branch | G4, G5, G6b, G8 |
| R4 | APP-028 paths unchanged; Flow D | G7 |
| R5 | optional `tools.py` description | none required |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-026 `in_progress` |
| Plan ⊆ Expected files | **PASS** | Three code paths + spec on close |
| Code traces | **PASS** | Flows A–D verified independently |
| Spec R1–R5 coverage | **PASS** | All requirements mapped to locus + tests |
| AC testability | **PASS** | G1–G8 + G6b; regression commands |
| APP-028 compatibility | **PASS** | Flow D; T4 parametrized case tolerant of gate error text |
| qa-spec-pass alignment | **PASS** | Round 2 blockers addressed in plan |

## Notes (non-blocking — impl QA)

1. **Line number drift:** Plan cites ~2315 / ~2530; live file ~2387 / ~2610 — use symbol search during impl, not absolute lines.
2. **Flow B untested:** When `combat.active` or `_combat_active_in_db()` is true, `combat_attack` hits combat-only guard before gate — documented; no dedicated test required for AC.
3. **Empty `attacker_id`:** Plan notes resolution → `"attacker not in combat: "`; no explicit G9 — acceptable edge; gate behavior follows engine.
4. **G7 subprocess:** Plan allows subprocess re-run of `test_combat_failure_narration.py`; prefer in-process import if subprocess proves flaky in CI (impl discretion).
5. **Dual no-combat strings:** ATTACK path returns `"no active combat for session"`; non-ATTACK keeps `"no active combat"` — documented in R3; APP-028 aligned.
6. **G6 exploration happy path:** Valid `status.combat` with `combat.active=False` is intentional — gate reads bridge status, not orchestrator combat flag.

**Verdict:** PASS — ready for workstreams + implementation.
