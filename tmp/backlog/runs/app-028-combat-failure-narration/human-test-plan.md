# Human Playtest Plan: APP-028-combat-failure-narration

**backlog_ticket:** APP-028  
**Commit:** `5135958` (Stage 7 — use latest commit containing APP-028 orchestrator changes if drifted)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** APP-028 enforces **code-owned failure narration** when combat tools return `ok: false` — no success-leaning fiction (hits, damage, combat start, initiative, spell effects) when mechanics did not commit. Automated pytest (`test_combat_failure_narration.py`, T1–T11) passed at impl QA; manual play validates **live LLM + PyGame** behavior mocks cannot fully cover (beat-trigger dual-channel, model prose that would have leaked after the failure prefix).

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=sk-or-v1-...`)
- [ ] Fresh finalized character: **`new game`** through creation to Registry reception, **or** Continue from a save already on surface at Breley (`32-C`)
- [ ] Tail `app/logs/session-YYYY-MM-DD.jsonl` in a second terminal (recommended for TC-5 / TC-7)
- [ ] Stats sidebar visible (phase badge, HP, location address)

## Pass / fail signals (global)

| Player-visible (good) | Player-visible (failure — file bug) |
|-----------------------|-------------------------------------|
| Narration starts with **`[Mechanics failed — …]`** when a combat tool fails | GM describes a **hit**, **damage dealt**, **initiative order**, **combat joined**, or **spell effect** after a failed combat tool |
| Beat-trigger start failure includes second line **`Combat could not begin.`** | Ghoul **attacks** / **leaps from the crypt** while mechanics did not start combat |
| No `\n\n` block of model success prose **after** the failure prefix on total-failure turns | Old bug shape: `[Mechanics failed — …]` **followed by** hit/start fiction in the same bubble |
| Engine truth: no **`COMBAT ACTIVE`** context while failure stands (delve/exploration continues) | Footer or JSONL shows **`combat_start`** / active combat while narration claims failure — or inverse: failure line but UI behaves as mid-combat |

**Banned substrings after a failed combat tool (same response):** `your blade finds`, `deals damage`, `initiative`, `combat begins`, `rolls initiative`, `the spell hits`, `Fortune spent`, `enemy falls`, `ghouls leap`, `ghoul attacks` *(LLM may still use neutral scene-setting **before** the failure line on beat turns — TC-5 checks the **returned player text** is failure-only)*.

## Acceptance criteria map

| Ticket AC / Req | Test case(s) |
|-----------------|--------------|
| Enforce failure narration for **all** combat tools | TC-1 (pytest), TC-3–TC-4, TC-6–TC-8 |
| No success fiction when `ok: false` / `combat: null` | TC-3–TC-7 |
| **R1** Beat-trigger grave-ghoul / `combat: null` | TC-5 |
| **R2** Exploration `all_failed` content strip | TC-3, TC-4, TC-6 |
| **R3/R4** Combat inner loop strip + partial failure | TC-7 |
| **R6** State truth after failure | TC-3, TC-5, TC-7 |

## Test cases

### TC-1: Automated regression gate (maps to T1–T11)

**Goal:** Confirm APP-028 test module green before manual play.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_combat_failure_narration.py -q` | Exit code **0**; **11 passed** | [ ] |
| 2 | Optional engine sanity: `python -m pytest play/tomb_gm/tests/test_combat_beat_trigger.py play/tomb_gm/tests/test_combat_attack.py -q` | Exit code **0** | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

### TC-2: Setup — surface → Breley undercrypt (maps to all manual TCs)

**Goal:** Reach delve context where grave-ghoul beats and combat tools are valid to exercise.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | If prompted, **`new game`** → complete creation (Dumpy path: name → `human` → `apprentice` → skills → schools → spells → equipment → `yes`) | Roster populated; **Awaiting: RECEPTION_CHOICE** at Registry | [ ] |
| 3 | Complete reception (accept contract / travel prompt as GM offers — e.g. `I take the Holt contract` or `I head to the undercrypt`) | Phase **preparation** or travel allowed; still on surface **32-C** | [ ] |
| 4 | Enter dungeon: `enter breley undercrypt` or `enter dungeon at 32-C-UG-1` | Successful **`enter_dungeon`**; location moves to undercrypt / **UG** layer (not surface-only fiction) | [ ] |
| 5 | Confirm sidebar | Address shows **UG** (e.g. `32-C-UG-1`); phase **delve** (or dungeon mode) | [ ] |

**Failure signals:** Stuck in creation; cannot enter undercrypt (APP-024 refusal without tool success); crash.

**Shortcut:** Continue from an existing save already inside Breley undercrypt — skip steps 2–4 if location is `32-C-UG-*`.

### TC-3: Attack outside combat — `combat_attack` failure (maps to R2/R5, T4)

**Goal:** Declaring an attack before combat is active must show mechanical failure, **not** hit fiction.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At undercrypt (TC-2), ensure **no** combat yet (no initiative block in narration; JSONL has no active `combat_state` row) | Exploration/delve turn | [ ] |
| 2 | Type **`I swing my sword at the nearest grave-ghoul.`** (or **`I attack the ghoul with my blade.`**) and submit | GM responds | [ ] |
| 3 | Read narration body | Contains **`[Mechanics failed — combat_attack:`** (error likely **`attacker not in combat`**) | [ ] |
| 4 | Scan same response | **No** hit/damage/initiative prose (`deals`, `strikes home`, `rolls initiative`, `combat begins`) | [ ] |
| 5 | Optional JSONL | Tool result `"name": "combat_attack"` with **`"ok": false`**; player text matches failure prefix only | [ ] |
| 6 | Sidebar / next turn | Still exploration/delve — **not** stuck in combat UI loop | [ ] |

**Failure signals:** Narration describes a successful strike or damage while combat never started; silent no-op; traceback.

### TC-4: Unknown monster — direct `start_combat` failure (maps to R5, T3)

**Goal:** Invalid monster id returns prefix-only failure; no “knight charges” fiction appended.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Still in undercrypt, **outside combat** | — | [ ] |
| 2 | Type **`I fight a phantom-knight that isn't in the bestiary.`** or **`Start combat with not-a-real-monster.`** and submit | GM attempts start | [ ] |
| 3 | Read narration | **`[Mechanics failed — start_combat:`** with error mentioning missing JSON / unknown monster | [ ] |
| 4 | Same response | **No** appended paragraph describing enemies charging, initiative, or combat joining | [ ] |
| 5 | JSONL (optional) | `"name": "start_combat"`, **`"ok": false`** | [ ] |

**Failure signals:** `[Mechanics failed — …]` followed by `\n\n` success prose; combat actually starts with phantom enemy.

### TC-5: Beat-trigger grave-ghoul — start failure, no ghoul attack fiction (maps to **R1**, T1–T2) — **primary scenario**

**Goal:** Reproduce the logged **`combat_trigger` + `combat: null`** path: beat succeeds mechanically, `start_combat_from_trigger` fails, player sees canonical two-line failure **without** ghoul-attack fiction.

**Why a dev step:** Canon **`grave-ghoul.json` exists** — live encounters normally **succeed**. Temporarily hide the monster file to force the same error as session logs and unit tests.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | **Quit PyGame.** From repo root, rename monster file: `move build\data\monsters\grave-ghoul.json build\data\monsters\grave-ghoul.json.bak` (PowerShell) | File moved; start will fail with `monster JSON not found: grave-ghoul` | [ ] |
| 2 | Relaunch `cd app && python main.py`; load TC-2 save or re-enter undercrypt | Inside **32-C-UG-*** delve | [ ] |
| 3 | Type **`I taunt the grave-ghoul to attack me!`** and submit | Single GM response (no long second narrate pass after failure) | [ ] |
| 4 | Read narration | **Exactly** failure shape: **`[Mechanics failed — combat start: monster JSON not found: grave-ghoul]`** then blank line then **`Combat could not begin.`** | [ ] |
| 5 | Same response | **No** `Ghouls leap`, **no** ghoul attack/hit/damage, **no** initiative order | [ ] |
| 6 | JSONL | `"name": "process_beat"` may show **`"ok": true`** with `combat_trigger` in mechanical summary — **player text must still be failure-only** (dual-channel) | [ ] |
| 7 | JSONL | **No** `"name": "start_combat"` / `combat_start` with **`"ok": true`** on this turn | [ ] |
| 8 | Sidebar | Still delve/exploration — **no** active combat state | [ ] |
| 9 | **Restore file:** `move build\data\monsters\grave-ghoul.json.bak build\data\monsters\grave-ghoul.json` | Monster restored for TC-7 | [ ] |

**Failure signals (pre-APP-028 regression):** Rich ghoul-attack prose with empty combat; **silent** no feedback; failure prefix **plus** model success paragraph; second LLM narrate pass after beat.

**Without file rename (optional smoke only):** Repeat step 3 after restore — encounter should **start combat successfully** (initiative / combatants). That confirms the repro setup works; **TC-5 pass requires steps 1–9 with file hidden.**

### TC-6: `combat_end` outside combat (maps to R5, T5)

**Goal:** Ending combat when none is active fails visibly without victory prose.

| Step | Action | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Outside combat (after TC-3 or fresh explore turn) | — | [ ] |
| 2 | Type **`I end combat.`** or **`Combat is over — I sheathe my weapon.`** and submit | GM responds | [ ] |
| 3 | Read narration | **`[Mechanics failed — combat_end:`** (likely **`no active combat`**) | [ ] |
| 4 | Same response | **No** victory, loot, or “combat ended” celebration prose | [ ] |

**Failure signals:** False combat-end narration; appended success paragraph after prefix.

### TC-7: In-combat failed action — inner loop strip (maps to R3, T8–T9)

**Goal:** After **successful** combat start, an invalid PC action shows failure-only text, not hit fiction.

| Step | Action | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | With **`grave-ghoul.json` restored**, in undercrypt, provoke live combat: **`I taunt the grave-ghoul to attack me!`** or **`The ghoul attacks!`** | Combat starts: initiative / combatants in narration or JSONL **`combat_start` ok: true** | [ ] |
| 2 | Read footer / context | **COMBAT** turn — awaiting PC or monster action | [ ] |
| 3 | On **monster's turn** (if GM narrates ghoul acting first), wait until **your** turn, **or** deliberately act early: **`I attack the ghoul again.`** when it is **not** your turn | GM responds | [ ] |
| 4 | If mechanics reject turn | Narration shows **`[Mechanics failed — combat_action:`** (e.g. **`not your turn`**) **without** appended hit/damage prose | [ ] |
| 5 | Optional: during combat, type **`I cast a fireball.`** (exploration-style tool) | Failure prefix for wrong tool / unavailable tool — **no** spell effect narration | [ ] |
| 6 | JSONL | Failed tool **`"ok": false`**; player channel matches prefix-only rule on total failure | [ ] |

**Failure signals:** Hit described when turn was invalid; exploration tools succeed mid-combat without `combat_action`.

**Note:** Exact error string varies (`not your turn`, `During combat only combat_action is available`). Pass/fail hinges on **prefix + no success fiction**, not exact wording.

### TC-8: Optional — `cast_spell` / `fortune_spend` outside combat (maps to R5, T6–T7)

**Goal:** Non-attack exploration combat tools also strip success fiction on total failure.

| Step | Action | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Outside combat, type **`I cast ember-touch at the ghoul.`** (use a spell on your sheet) | **`[Mechanics failed — cast_spell:`** (e.g. **`not in combat`**) | [ ] |
| 2 | Same response | **No** spell damage / ignite effect described | [ ] |
| 3 | If Fortune > 0, type **`I spend Fortune to reroll.`** outside combat | Either failure prefix or non-combat refusal — **no** “Fortune spent — success” fiction if tool failed | [ ] |

**Skip if:** Caster has no spells / no Fortune — pytest T6–T7 remain authoritative.

## Automated cross-check (optional before sign-off)

```bash
python -m pytest app/tests/test_combat_failure_narration.py -q
python -m pytest play/tomb_gm/tests/test_combat_beat_trigger.py -q
```

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **APP-027:** Engine-side monster id validation at start — separate from narration enforcement verified here.
- **APP-026:** Pre-check gating before `combat_attack` — overlaps TC-3; failure must still be **visible** if gating misses.
- **APP-030:** Full combat golden-path integration test — not required for APP-028 sign-off.
- **Flaky LLM:** Player phrasing in TC-3–TC-4 may need one retry; pass/fail is **mechanical prefix + no banned fiction**, not exact player command echoed.
- **TC-5 file rename:** Dev-only repro — **must restore** `grave-ghoul.json` before other content/engine work.
- **Mixed tool batch:** Same turn with `process_beat` + other tools is rare; APP-028 accepts beat-only grave-ghoul path as primary.
