# Human Playtest Plan: APP-030-combat-integration-test

**backlog_ticket:** APP-030  
**Commit:** pending (Stage 7 — use commit containing `app/tests/test_combat_integration.py` + V4 removal)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** APP-030 adds an **automated bridge golden path** (`test_bridge_combat_start_attack_end`): isolated workspace, roster PC, canon `grave-ghoul:1`, advance to PC turn, `combat_attack`, `combat_end`. Ticket AC is **pytest-only** — this plan is an **optional** manual smoke that the live PyGame + LLM path can reach the same mechanical milestones (start → PC action → end). **I1 passing is sufficient for sign-off**; skip manual play when time-boxed.

**Layer difference (important):** I1 calls `bridge.combat_attack` directly. During active combat in production, the orchestrator routes PC attacks through **`combat_action`** (ATTACK), not exploration `combat_attack`. Manual TC-4 validates the **player-facing** path; I1 validates the **bridge contract**.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=…`)
- [ ] Finalized roster PC: **`new game`** through creation to Registry reception, **or** Continue from a save inside Breley undercrypt (`32-C-UG-*`)
- [ ] Canon monster present: `build/data/monsters/grave-ghoul.json` (do **not** hide — unlike APP-027/028 failure repros)
- [ ] Optional log watch: `app/logs/session-YYYY-MM-DD.jsonl` — confirm `start_combat` / `combat_action` / `combat_end` tool results

## Pass / fail signals (global)

| Good (pass) | Bad (fail — file bug) |
|-------------|------------------------|
| Combat **starts** after grave-ghoul encounter; narration or JSONL shows **`combat_start` ok: true** | Start fails with validation error on canon `grave-ghoul` (regression to APP-027) |
| PC + ghoul appear in combat context (initiative / combatants) | Combat starts with **monsters only** — no roster PC in fight |
| After monster turn(s), PC can **attack** on own turn — hit **or** miss both OK | `[Mechanics failed — combat_action:` on valid PC turn without turn-order excuse |
| **`combat_end` ok** — phase returns to **`DELVE`**; exploration input works next turn | Phase stuck **`COMBAT`**; `combat_end` refused when fight should be over |
| JSONL: mechanical tools succeed in order (start → action → end) | Silent no-op; traceback; combat row left active after “end” narration |

**Out of scope for this plan:** APP-028 failure-prefix shapes, APP-026 outside-combat gating, APP-090 phased verify narration, full fight-to-death, APP-029 auto-chain unit tests.

## Acceptance criteria map

| Ticket AC / Req | Authoritative check | Optional manual TC |
|-----------------|---------------------|-------------------|
| **I1** bridge golden path | TC-1 pytest | TC-3–TC-5 |
| **V4 absorption** (no skipped happy-start test) | TC-1 step 2 (7 validation tests, 0 skipped) | — |
| Domain spec § APP-030 | TC-1 | TC-3–TC-5 smoke |

## Test cases

### TC-1: Automated regression gate (required — ticket sign-off)

**Goal:** Confirm I1 and combat regression modules green before optional manual play.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_combat_integration.py -q` | Exit code **0**; **1 passed** (`test_bridge_combat_start_attack_end`) | [ ] |
| 2 | From repo root: `python -m pytest app/tests/test_combat_monster_validation.py -q` | Exit code **0**; **7 passed**, **0 skipped** (V4 absorbed into I1) | [ ] |
| 3 | From repo root: `python -m pytest app/tests/test_combat_attack_gating.py app/tests/test_combat_failure_narration.py -q` | Exit code **0** | [ ] |
| 4 | Optional: `python -m pytest play/tomb_gm/tests/test_combat_attack.py -q` | Exit code **0**; engine reference unchanged | [ ] |

**Failure signals:** Any pytest failure — stop; file bug against APP-030. Manual play does not override a red I1.

---

### TC-2: Setup — surface → Breley undercrypt (manual TCs only)

**Goal:** Reach delve context with a **roster PC in slot 1** (I1 fixture contract in live save).

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | **`new game`** → complete creation (name → race → class/skills/spells → equipment confirm) **or** Continue finalized save | Roster populated; not stuck in creation | [ ] |
| 3 | Complete Registry reception / travel to undercrypt entry | Surface **32-C** or travel allowed | [ ] |
| 4 | Enter dungeon: `enter breley undercrypt` or `enter dungeon at 32-C-UG-1` | Location **UG** layer (e.g. `32-C-UG-1`) | [ ] |
| 5 | Sidebar | Phase badge **`DELVE`**; HP/Fortune visible | [ ] |

**Shortcut:** Continue from save already at `32-C-UG-*` with finalized delver — skip steps 2–3.

**Failure signals:** No roster PC; cannot enter undercrypt; crash.

---

### TC-3: Combat start — grave-ghoul beat (maps to I1 steps 2–4, V4 happy start)

**Goal:** Canon encounter starts combat with PC + ghoul in combatants; initiative resolves.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At undercrypt (TC-2), confirm **no** active combat | Phase **`DELVE`** | [ ] |
| 2 | Type **`I taunt the grave-ghoul to attack me!`** or **`The grave ghoul attacks!`** and submit | GM responds; combat begins | [ ] |
| 3 | Read narration | Initiative / combatants / ghoul presence — **no** `[Mechanics failed — start_combat:` | [ ] |
| 4 | Sidebar | Phase may show **`COMBAT`** (or combat clearly active in narration) | [ ] |
| 5 | Optional JSONL | `"name": "start_combat"` or beat → start with **`"ok": true`**; `combat_start` action | [ ] |
| 6 | Optional JSONL / status | Combatants include **PC** (roster name) and **grave-ghoul** | [ ] |

**Failure signals:** Validation error on `grave-ghoul`; combat starts without PC; silent no-op.

**Flaky LLM note:** Retry with explicit **`Start combat with grave-ghoul.`** Pass/fail is **mechanical start + PC in fight**, not exact player phrasing.

---

### TC-4: PC attack on own turn (maps to I1 step 5)

**Goal:** On PC turn, attack resolves **`ok: true`** (hit or miss both pass).

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Continuing from TC-3 | Combat still active | [ ] |
| 2 | If narration shows **monster acting first**, wait for GM to finish monster turn(s) — APP-029 may auto-chain | Turn returns toward PC | [ ] |
| 3 | On **your** turn, type **`I attack the grave ghoul with my weapon.`** or **`I swing at the ghoul.`** and submit | GM responds | [ ] |
| 4 | Read narration | Attack outcome (hit, miss, or mechanical summary) — **not** `[Mechanics failed — combat_action: not your turn` **unless** you acted early | [ ] |
| 5 | Optional JSONL | `"name": "combat_action"` (ATTACK) with **`"ok": true`** | [ ] |
| 6 | Sidebar | Combat still active (I1 asserts combat non-null after attack) | [ ] |

**Failure signals:** Valid PC-turn attack blocked; exploration `combat_attack` error mid-fight without turn-order reason; crash.

**Early-action check (optional):** Deliberately attack before your turn once — expect **`not your turn`** failure (APP-028/029 territory). Retry on correct turn for TC-4 pass.

---

### TC-5: End combat — return to delve (maps to I1 step 6–7)

**Goal:** `combat_end` clears combat; player can explore again.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Still in combat from TC-4 (or TC-3 if skipping attack) | — | [ ] |
| 2 | Type **`I end combat.`**, **`Combat is over — I withdraw.`**, or **`I sheathe my weapon and leave the fight.`** and submit | GM responds | [ ] |
| 3 | Read narration | Combat concludes — **no** `[Mechanics failed — combat_end:` | [ ] |
| 4 | Sidebar | Phase returns to **`DELVE`** (not stuck **`COMBAT`**) | [ ] |
| 5 | Type **`I look around the crypt.`** and submit | Normal exploration response — not “not your turn” / combat-only refusal | [ ] |
| 6 | Optional JSONL | `"name": "combat_end"` with **`"ok": true`**; no active combat row after turn | [ ] |

**Failure signals:** Combat state stuck; false victory without tool ok; cannot explore after end.

---

### TC-6: Optional — monster-first initiative smoke (maps to I1 `_advance_to_pc_turn`)

**Goal:** Confirm live session tolerates ghoul-before-PC initiative without manual bridge advance.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Repeat TC-3 start (new encounter or reload save pre-combat) | Combat starts | [ ] |
| 2 | Observe first round narration | Monster may act before PC — **expected** | [ ] |
| 3 | Proceed to TC-4 on PC turn | Attack succeeds as in TC-4 | [ ] |

**Skip if:** Time-boxed — I1 `_advance_to_pc_turn` loop is authoritative for bridge advance.

---

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | TC-1 pass (required) / TC-2–5 optional pass / issues: … |

**Ticket close:** APP-030 AC met when **TC-1 passes**. Manual TC-2–5 are **optional** production smoke.

## Notes for next ticket

- **APP-029:** Monster auto-chain after PC `combat_action` — TC-4 step 2 may show multiple monster turns without player input.
- **APP-090:** Phased combat narration + TurnTruth verify — not required for APP-030 bridge integration.
- **I2/I3 stretch:** Orchestrator `_execute_tool` chain tests remain pytest backlog; manual plan does not substitute.
- **APP-027 TC-6:** Optional valid grave-ghoul smoke from APP-027 plan — superseded by TC-3 here for happy-path coverage.
- **Roster requirement:** Session-only saves without `character_create` may start monster-only combat — mirrors I1 fixture lesson; always use finalized roster for manual golden path.
- **Commit pending:** `test_combat_integration.py` may be uncommitted at plan authoring — use Stage 7 commit hash when available.
