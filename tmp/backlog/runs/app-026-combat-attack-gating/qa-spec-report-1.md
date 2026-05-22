# QA Report: spec — round 1

**Task:** app-026-combat-attack-gating  
**backlog_ticket:** APP-026  
**ticket_path:** [tmp/backlog/app-026-combat-attack-gating.md](../../app-026-combat-attack-gating.md)  
**Verdict:** FAIL  
**Reviewer role:** QA (adversarial)  
**domain_spec_creation:** not_needed (registry_gap false)

## Findings

### SPEC-001 — blocker

- **Location:** `spec.md` R3 (`action == "ATTACK"`); domain spec § Wire points (`action == "ATTACK"`); test plan G4/G5 (uppercase only)
- **Issue:** Gate wiring is case-sensitive, but engine attack dispatch normalizes action: `action_upper = action.upper().strip()` then `if action_upper == "ATTACK"` (`play/tomb_gm/services/simulation/combat.py` ~714–715). App tests and combat inner loop often pass lowercase `"attack"` (`test_combat_failure_narration.py` T8/T10; `_execute_combat_action(**args)` receives raw LLM args — `tool_args._normalize_combat_action` does **not** uppercase).
- **Implementation gap:** Dev implementing literal `action == "ATTACK"` skips `_gate_pc_attack` for lowercase `"attack"`. Initiative membership check is bypassed on the combat-loop path while bridge/engine still resolve the attack — **ticket AC “attacker in initiative” not enforced for that casing**.
- **Suggested fix:** R3 + domain wire table: gate when `action.upper().strip() == "ATTACK"` (mirror engine). Add test (extend G5 or new G8): `_execute_combat_action("attack", actor_id=…)` with actor absent from initiative → gate error before `bridge.combat_action`.

### SPEC-002 — minor

- **Location:** `spec.md` R3 (“Existing … `no active combat` may remain”); R1 step 1 vs `_execute_combat_action` line 2325
- **Issue:** Two no-combat strings coexist (`no active combat` vs `no active combat for session`). PM documented as defense-in-depth; acceptable if gate runs first on ATTACK.
- **Implementation gap:** None if R3 gate order is followed; G4 should assert gate string when ATTACK path is wired.
- **Suggested fix:** Optional: G4 expected error `"no active combat for session"` explicitly; or one sentence that ATTACK path always uses gate string.

### SPEC-003 — minor

- **Location:** `spec.md` test plan G5 setup (“Combat + turn match but actor absent from initiative”)
- **Issue:** Normal `handle_status` derives `turn_id` from `initiative[turn_index]` — inconsistent “turn match + absent from initiative” requires artificial mock; setup steps not spelled out.
- **Implementation gap:** Dev may struggle to construct G5 fixture or skip the test.
- **Suggested fix:** G5 setup bullet: monkeypatch `bridge.status()` returning `turn_id="pc1"` with `initiative=[{id:"m1"}]` (actor `pc1` requested but not listed).

### SPEC-004 — minor

- **Location:** `spec.md` G6 vs R3; domain spec tests table
- **Issue:** Happy-path gate coverage is exploration-only (`bridge.combat_attack`). No explicit pass-through test for `combat_action` ATTACK after gate (`bridge.combat_action` called once).
- **Implementation gap:** R3 wiring could regress without a combat-loop happy-path assertion.
- **Suggested fix:** Add G6b or extend G6: `_execute_combat_action("ATTACK", …)` valid initiative + turn → `bridge.combat_action` called once.

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 feature; `in_progress`; domain spec field matches `app-combat-play-spec.md` |
| registry_gap | **PASS** | false — combat spec owns behavior; PM added § Combat attack gating |
| AC testability (core) | **WARN** | Mappable after SPEC-001 fix |
| Code traces | **PASS** | Exploration direct bridge dispatch ~2530–2531; partial combat pre-check ~2323–2328; engine `_resolve_combatant_id` ~476–485 |
| Expected files ⊆ plan scope | **PASS** | Ticket lists orchestrator, optional `tools.py`, new test module — matches run spec § Affected paths (domain spec sync on close is ticket § Spec sync, not hook-gated) |
| Domain spec sync | **PASS** (content) | § APP-026 mirrors run spec R1/R2/R3/tests; changelog dated |
| ATTACK gate completeness | **FAIL** | SPEC-001 — case-sensitive gate vs engine normalization |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Before attack: require `status.combat` | R1 step 1; R2/R3; G1, G4 | pytest + mock bridge not called | **PASS** (intent) |
| Attacker in initiative | R1 step 3; G2, G5, G6 | unit + integration mocks | **WARN** until SPEC-001 (lowercase bypass) |
| Wire both attack paths | R2, R3; domain wire table | G1, G4–G6 | **PASS** (intent) |
| Spec sync on close | Ticket § Spec sync; domain § APP-026 | review | **PASS** |

## Verified (code evidence)

| Claim | Evidence |
|-------|----------|
| Exploration `combat_attack` hits bridge with no orchestrator pre-check | `orchestrator.py` 2530–2531 |
| Combat loop partial pre-check (combat + turn, no initiative) | `orchestrator.py` 2323–2328 |
| Engine no-combat error for session | `combat.py` ~625–627, ~956 `no active combat for session` |
| Engine attacker membership after dispatch | `combat.py` ~638–640 `attacker not in combat` |
| Display-name resolution pattern | `combat.py` `_resolve_combatant_id` ~476–485 |
| APP-028 T4 uses mocked bridge failure (no pre-gate today) | `test_combat_failure_narration.py` parametrized `combat_attack` case |
| `combat_action` args not uppercased in app layer | `tool_args.py` `_normalize_combat_action` ~129–135 |
| Domain spec PM draft present | `tmp/app-combat-play-spec.md` § Combat attack gating (APP-026) |

## Summary

**FAIL** — fix **SPEC-001** (case-insensitive ATTACK gate condition + lowercase test) before Dev plan. PM draft is otherwise strong: AC mapped, research traces confirmed, Expected files aligned, APP-028 regression called out, turn enforcement correctly scoped as non-goal. Address **SPEC-003** / **SPEC-004** in the same PM revision for clearer Dev fixtures.

## Re-review focus

- R3 + domain wire: `action.upper().strip() == "ATTACK"`
- Test asserting lowercase `"attack"` hits gate on combat loop path
- G5 mock setup for inconsistent turn_id vs initiative (optional)
- Optional combat-loop happy-path test through gate (G6b)
