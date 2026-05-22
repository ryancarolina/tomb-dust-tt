# Human Playtest Plan: APP-026-combat-attack-gating

**backlog_ticket:** APP-026  
**Commit:** pending (Stage 7 — use latest commit containing `_gate_pc_attack` / `test_combat_attack_gating.py`)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** APP-026 adds orchestrator **`_gate_pc_attack`** so exploration `combat_attack` (and combat-loop ATTACK) fail **before** `bridge.combat_attack` / `bridge.combat_action` when `status.combat` is null or the attacker is not on initiative. This plan focuses on the **primary ticket gap: attack outside combat**. Automated pytest (G1–G8 + APP-028) passed at impl QA; manual play validates **live LLM + PyGame** paths mocks cannot fully cover (model still calls `combat_attack`, APP-028 strip, player-visible error string).

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=sk-or-v1-...`)
- [ ] Fresh finalized character: **`new game`** through creation to Registry reception, **or** Continue from a save on surface **32-C** (Breley)
- [ ] Tail `app/logs/session-YYYY-MM-DD.jsonl` in a second terminal (recommended for TC-3 / TC-4)
- [ ] Stats sidebar visible (phase badge, HP, location address — **no** combat phase)

## Pass / fail signals (global)

| Player-visible (good) | Player-visible (failure — file bug) |
|-----------------------|-------------------------------------|
| Narration contains **`[Mechanics failed — combat_attack:`** with error **`no active combat for session`** when attacking outside combat | GM describes a **hit**, **damage**, **initiative**, or **combat joined** while combat never started |
| Failure prefix only (APP-028 strip) — **no** `\n\n` success paragraph after prefix | Old shape: prefix **plus** blade-finds / deals-damage fiction in same bubble |
| Sidebar stays **delve** or **preparation** — not combat turn loop | Footer stuck on **COMBAT** / initiative after failed attack |
| JSONL tool result: `"name": "combat_attack"`, **`"ok": false`**, `"error": "no active combat for session"` | Tool `"ok": true` with hit/damage mechanical while player saw failure; or engine combat row created |

**Banned substrings in the same GM response after a failed outside-combat attack:** `deals damage`, `strikes home`, `your blade finds`, `rolls initiative`, `combat begins`, `initiative order`, `enemy falls`.

## Acceptance criteria map

| Ticket AC / Req | Test case(s) |
|-----------------|--------------|
| Before attack: require `status.combat` | TC-1 (G1, G4), TC-3, TC-4 |
| Attacker in initiative (orchestrator gate) | TC-1 (G2, G5, G8) — pytest; **not** manual focus for this plan |
| Wire exploration `combat_attack` | TC-3, TC-4 |
| APP-028 compatibility (visible failure, no hit fiction) | TC-1 (G7), TC-3 |

## Test cases

### TC-1: Automated regression gate (maps to G1–G8, G7 / APP-028)

**Goal:** Confirm gate module and APP-028 narration still green before manual play.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_combat_attack_gating.py -q` | Exit code **0**; **9 passed** | [ ] |
| 2 | From repo root: `python -m pytest app/tests/test_combat_failure_narration.py -q` | Exit code **0**; **11 passed** | [ ] |
| 3 | Optional engine sanity: `python -m pytest play/tomb_gm/tests/test_combat_attack.py play/tomb_gm/tests/test_combat_turn_enforcement.py -q` | Exit code **0** | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

### TC-2: Setup — exploration with no active combat (maps to TC-3 / TC-4)

**Goal:** Reach a phase where `status.combat` is null so attack gating can fire.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | If prompted, **`new game`** → complete creation (Dumpy path: name → `human` → `apprentice` → skills → schools → spells → equipment → `yes`) | Roster populated; **Awaiting: RECEPTION_CHOICE** at Registry | [ ] |
| 3 | Complete reception (accept contract / travel — e.g. `I take the Holt contract`) | Phase **preparation**; surface **32-C** | [ ] |
| 4 | Confirm sidebar | **Not** combat phase; no initiative / round footer in narration | [ ] |
| 5 | Optional delve path: `enter breley undercrypt` or `enter dungeon at 32-C-UG-1` | Location **UG** (e.g. `32-C-UG-1`); phase **delve**; still **no** combat | [ ] |

**Failure signals:** Stuck in creation; crash; already in active combat before attack test.

**Shortcut:** Continue from save at **32-C** or **32-C-UG-*** with no combat active — skip steps 2–3 if applicable.

### TC-3: Attack outside combat — gate + APP-028 strip (maps to R1/R2, G1, ticket AC) — **primary scenario**

**Goal:** Player declares an attack while `status.combat` is null. Orchestrator gate returns **`no active combat for session`**; player sees mechanical failure with **no hit fiction**; game stays in exploration/delve.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At TC-2 location (surface **or** undercrypt), confirm **no** combat | No initiative block in recent narration; JSONL has no active `combat_state` / `"combat"` block in status snapshot | [ ] |
| 2 | Type **`I swing my sword at the nearest grave-ghoul.`** (undercrypt) **or** **`I attack the clerk with my blade.`** (surface — absurd target is OK; gate fires on missing combat, not target validity) and submit | GM responds (may take a thinking beat) | [ ] |
| 3 | Read narration body | Contains **`[Mechanics failed — combat_attack:`** and substring **`no active combat for session`** | [ ] |
| 4 | Scan same response | **No** hit/damage/initiative prose (see banned list above) | [ ] |
| 5 | JSONL (same turn) | Tool result `"name": "combat_attack"`, **`"ok": false`**, `"error": "no active combat for session"` | [ ] |
| 6 | JSONL / status | **No** new `"combat_start"` with **`"ok": true`** on this turn | [ ] |
| 7 | Sidebar / next input | Still **preparation** or **delve** — not mid-combat turn loop | [ ] |
| 8 | Submit a neutral explore line (e.g. **`I look around.`**) | Turn completes normally — not soft-locked | [ ] |

**Failure signals (pre-APP-026 regression):** Error text **`attacker not in combat`** only (bridge reached before gate); narrated hit/damage while combat null; silent no-op; traceback; combat UI activates without valid start.

**Note:** APP-028 TC-3 (APP-028 run folder) allowed `attacker not in combat` — after APP-026 the canonical gate error is **`no active combat for session`**. Prefix shape unchanged.

### TC-4: Second attack phrasing — gate idempotence (maps to R2, exploration path)

**Goal:** Repeat outside-combat attack with different player phrasing; gate still blocks before engine; no success fiction leak on retry.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Still outside combat (after TC-3 or fresh explore turn) | — | [ ] |
| 2 | Type **`I strike the ghoul with my weapon.`** or **`Attack the enemy!`** and submit | GM responds | [ ] |
| 3 | Read narration | Again **`[Mechanics failed — combat_attack:`** + **`no active combat for session`** | [ ] |
| 4 | Same response | **No** hit/damage fiction | [ ] |
| 5 | Optional JSONL | Second `"combat_attack"` tool row with same gate error — still **no** combat start | [ ] |

**Failure signals:** First failure then second turn narrates a successful hit; model-only success without failure prefix.

### TC-5: Optional — surface preparation attack (maps to G1 exploration path)

**Goal:** Confirm gate fires on **surface / preparation**, not only undercrypt.

| Step | Action | Expected result | Pass |
|------|------|-----------------|------|
| 1 | At Registry reception completed, **before** entering dungeon (phase **preparation**, **32-C**) | No combat | [ ] |
| 2 | Type **`I draw my sword and attack.`** and submit | **`[Mechanics failed — combat_attack:`** + **`no active combat for session`** | [ ] |
| 3 | Same response | No hit fiction | [ ] |

**Skip if:** TC-3 already run from surface with equivalent input.

## Out of scope (pytest-owned)

| Behavior | Covered by |
|----------|------------|
| Attacker not in initiative during combat-loop ATTACK (G5, G8) | `test_combat_attack_gating.py` |
| DisplayName resolution (`Aldric` → `pc1`) (G3) | Unit test |
| Valid combat attack happy path (G6, G6b) | [APP-030](../../../app-030-combat-integration-test.md) / future golden path |
| Beat-trigger grave-ghoul start failure | [APP-028](../app-028-combat-failure-narration/human-test-plan.md) TC-5 |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **APP-028:** Owns failure **narration** strip; APP-026 owns **pre-bridge gate**. TC-3 pass requires both.
- **APP-027:** Engine monster validation at combat start — separate from outside-combat attack gate.
- **Flaky LLM:** Model may need 1–2 phrasing retries to call `combat_attack`; pass/fail is **gate error string + no banned fiction**, not exact player command echoed.
- **In-combat `combat_attack`:** Existing guard returns `During combat only combat_action is available` — gate not reached (Flow B in plan); not tested here.
- **Commit hash:** Update header when Stage 7 commit lands for APP-026 only.
