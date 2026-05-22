# Human Playtest Plan: APP-027-validate-monster-id-combat

**backlog_ticket:** APP-027  
**Commit:** pending (Stage 7 — use latest commit containing APP-027 validation changes)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** APP-027 adds **layered monster-spec validation** before any `combat_state` DB write (engine R1, bridge R2, tool-args R3). On unknown or malformed ids, the player must see a **clear mechanical error**, **no combat-start fiction**, and **no combat HUD transition**. APP-028 owns the failure-narration strip; this plan verifies the **validation + state-truth** contract in live PyGame with a real LLM. Automated pytest (V1–V9) passed at impl QA; manual play catches beat-trigger dual-channel and sidebar regressions mocks may miss.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=sk-or-v1-...`)
- [ ] Fresh finalized character: **`new game`** through creation to Registry reception, **or** Continue from a save already inside Breley undercrypt (`32-C-UG-*`)
- [ ] Tail `app/logs/session-YYYY-MM-DD.jsonl` in a second terminal (recommended for TC-3 / TC-4)
- [ ] Stats sidebar visible (phase badge, HP, location address)

## Pass / fail signals (global)

| Player-visible (good) | Player-visible (failure — file bug) |
|-----------------------|-------------------------------------|
| Narration shows **`[Mechanics failed — start_combat:`** or **`[Mechanics failed — combat start:`** with a readable reason (`monster JSON not found: …`, `monster_specs required`, `invalid monster spec`) | GM narrates **initiative**, **enemies charge**, **combat begins**, **ghoul attacks**, or **damage dealt** when start failed |
| Beat-trigger failure includes second line **`Combat could not begin.`** | Rich encounter fiction with **no** failure prefix |
| Stats sidebar phase badge stays **`DELVE`** (or current exploration phase) — **not** `COMBAT` | Phase badge flips to **`COMBAT`** while error stands |
| Map address unchanged; input accepts next exploration command | UI stuck in combat turn loop; map blocked as if mid-fight |
| JSONL: `"name": "start_combat"` or beat path with **`"ok": false`**; **no** `combat_start` with **`"ok": true`** on same turn | Active `combat_state` row written despite failure narration |

**Banned substrings after a failed start (same GM response):** `initiative`, `combat begins`, `rolls initiative`, `enemies charge`, `leap from the crypt`, `ghoul attacks`, `deals damage`, `your blade finds`, `joins the fight`.

**Required error substrings (any one):** `monster JSON not found:`, `monster_specs required`, `invalid monster spec`.

## Acceptance criteria map

| Ticket AC / Req | Test case(s) |
|-----------------|--------------|
| Validate monster specs at `start_combat` | TC-1 (pytest V1–V9), TC-3, TC-4 |
| Clear error (no fiction on unknown id) | TC-3, TC-4 |
| **R5** `status.combat` null; no combat HUD | TC-3 steps 6–8, TC-4 steps 7–8, TC-5 |
| **R2** Beat path (`start_combat_from_trigger`) | TC-4 |
| **R3** Tool-args gate before bridge | TC-1 (V5 pytest); TC-3 (live LLM path) |
| **R6** Tool schema uses canon ids only | TC-1 optional grep (non-blocking) |

## Test cases

### TC-1: Automated regression gate (maps to V1–V9)

**Goal:** Confirm APP-027 test modules green before manual play.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_combat_monster_validation.py -q` | Exit code **0**; **7 passed**, **1 skipped** (V4) | [ ] |
| 2 | From repo root: `python -m pytest play/tomb_gm/tests/test_validate_monster_specs.py -q` | Exit code **0**; **4 passed** | [ ] |
| 3 | From repo root: `python -m pytest app/tests/test_combat_failure_narration.py -k start_combat -q` | Exit code **0**; **1 passed** (APP-028 substring stability) | [ ] |
| 4 | Optional hygiene: `rg "hollow-knight" app/gm/tools.py` | Zero matches (R6 canon examples) | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

### TC-2: Setup — surface → Breley undercrypt (maps to all manual TCs)

**Goal:** Reach delve context where `start_combat` and grave-ghoul beats are exercisable.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | If prompted, **`new game`** → complete creation (Dumpy path: name → `human` → `apprentice` → skills → schools → spells → equipment → `yes`) | Roster populated; **Awaiting: RECEPTION_CHOICE** at Registry | [ ] |
| 3 | Complete reception (accept contract / travel — e.g. `I take the Holt contract` or `I head to the undercrypt`) | Phase **preparation** or travel allowed; surface **32-C** | [ ] |
| 4 | Enter dungeon: `enter breley undercrypt` or `enter dungeon at 32-C-UG-1` | Successful **`enter_dungeon`**; location **UG** layer | [ ] |
| 5 | Confirm sidebar | Address shows **UG** (e.g. `32-C-UG-1`); phase badge **`DELVE`** | [ ] |

**Failure signals:** Stuck in creation; cannot enter undercrypt; crash.

**Shortcut:** Continue from an existing save already inside Breley undercrypt — skip steps 2–4 if location is `32-C-UG-*`.

### TC-3: Unknown monster id — exploration `start_combat` (maps to R2/R3/R5, V1/V6/V8) — **primary scenario**

**Goal:** Player prompt that causes LLM to call `start_combat` with a non-existent monster id fails **before** combat enters DB; player sees prefix-only failure and sidebar stays non-combat.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At undercrypt (TC-2), confirm **no** active combat (phase **`DELVE`**; no initiative block in recent narration) | Exploration/delve turn | [ ] |
| 2 | Type **`Start combat with hollow-knight.`** or **`I fight a phantom-knight that isn't in the bestiary.`** and submit | GM responds (may take one retry if model chooses a different tool first) | [ ] |
| 3 | Read narration body | Starts with **`[Mechanics failed — start_combat:`** | [ ] |
| 4 | Error detail in same line | Contains **`monster JSON not found:`** and the bogus id (e.g. `hollow-knight`, `phantom-knight`, or `not-a-real-monster`) | [ ] |
| 5 | Scan same response | **No** banned success-fiction substrings (initiative, charge, combat begins, damage) | [ ] |
| 6 | Stats sidebar | Phase badge still **`DELVE`** — **not** `COMBAT` | [ ] |
| 7 | Map panel | Address still **UG** undercrypt; no combat-only overlay change | [ ] |
| 8 | Next turn: type **`I look around the crypt.`** and submit | Normal exploration response — **not** “not your turn” / combat-action refusal | [ ] |
| 9 | Optional JSONL | `"name": "start_combat"`, **`"ok": false`**; error contains `monster JSON not found`; **no** subsequent `combat_start` ok:true | [ ] |

**Failure signals (pre-APP-027 regression):** GM describes knights charging or initiative after tool failure; phase badge shows **`COMBAT`**; second narrate pass appends success prose after failure prefix; silent no-op.

**Flaky LLM note:** If the model does not call `start_combat` on first try, retry with explicit wording: **`Use start_combat with monster_specs hollow-knight:1.`** Pass/fail is **mechanical error + no fiction + no HUD**, not exact player phrasing.

### TC-4: Beat-trigger start failure — hidden `grave-ghoul.json` (maps to R2/R5, V7) — **primary beat path**

**Goal:** Beat extracts valid-looking specs from encounter prose, but R2 validation fails when JSON is missing; player sees canonical two-line failure without ghoul-attack fiction.

**Why a dev step:** Canon **`grave-ghoul.json` exists** — live beats normally **start combat successfully**. Temporarily hide the file to force the same `monster JSON not found: grave-ghoul` error as unit tests.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | **Quit PyGame.** From repo root: `move build\data\monsters\grave-ghoul.json build\data\monsters\grave-ghoul.json.bak` (PowerShell) | File moved | [ ] |
| 2 | Relaunch `cd app && python main.py`; load TC-2 save or re-enter undercrypt | Inside **32-C-UG-*** delve | [ ] |
| 3 | Type **`I taunt the grave-ghoul to attack me!`** and submit | Single GM response (no long second narrate pass after failure) | [ ] |
| 4 | Read narration | **`[Mechanics failed — combat start: monster JSON not found: grave-ghoul]`** then blank line then **`Combat could not begin.`** | [ ] |
| 5 | Same response | **No** ghoul leap/attack/hit/damage/initiative prose | [ ] |
| 6 | Stats sidebar | Phase badge **`DELVE`** — **not** `COMBAT` | [ ] |
| 7 | JSONL | `"name": "process_beat"` may show **`"ok": true`** with `combat_trigger` — **player text must still be failure-only** | [ ] |
| 8 | JSONL | **No** `"name": "start_combat"` / `combat_start` with **`"ok": true`** on this turn | [ ] |
| 9 | **Restore file:** `move build\data\monsters\grave-ghoul.json.bak build\data\monsters\grave-ghoul.json` | Monster restored | [ ] |

**Failure signals:** Ghoul-attack fiction with empty combat; failure prefix **plus** model success paragraph; phase badge **`COMBAT`**; silent no feedback.

**Without file rename (optional smoke only):** After restore, repeat step 3 — encounter should **start combat** (initiative / combatants). Confirms setup works; **TC-4 pass requires steps 1–9 with file hidden.**

### TC-5: Sidebar / HUD non-regression after failure (maps to R5, ticket “no combat HUD”)

**Goal:** Explicit HUD checklist after TC-3 or TC-4 failure — validation failure must not partially flip UI into combat mode.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Immediately after TC-3 or TC-4 failure response | — | [ ] |
| 2 | Stats panel phase pill | Reads **`DELVE`** (uppercase pill) — **not** `COMBAT` | [ ] |
| 3 | HP / Fortune / gold | Same values as before the failed start attempt (no combat damage applied) | [ ] |
| 4 | Map | Current **UG** cell highlighted; travel clicks still gated only by normal delve rules (not combat lock) | [ ] |
| 5 | Input bar | Enabled when GM idle; suggestion chips exploration-appropriate (not combat-action-only set) | [ ] |
| 6 | Optional JSONL / status export | No active combat row; orchestrator `combat.active` false after turn completes | [ ] |

**Failure signals:** Any combat-phase UI signal without successful `combat_start`; HP dropped from phantom combat; input permanently “thinking” or combat-gated.

### TC-6: Optional — valid monster smoke after restore (maps to V4 deferral / APP-030)

**Goal:** Confirm validation does not block **canon** grave-ghoul starts after TC-4 restore.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | With **`grave-ghoul.json` restored**, in undercrypt, type **`I taunt the grave-ghoul to attack me!`** | Combat **starts** — initiative or combatants in narration | [ ] |
| 2 | Sidebar | Phase may show **`COMBAT`** (or combat context in narration) — **expected on success** | [ ] |
| 3 | JSONL | `"name": "start_combat"` or beat path with **`"ok": true`** / `combat_start` | [ ] |

**Skip if:** Time-boxed — pytest V4 remains skipped; APP-030 owns full golden-path combat.

### TC-7: Optional — empty `monster_specs` (maps to R3/V5)

**Goal:** Structural validation blocks empty lists before bridge (hard to trigger via natural play).

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Rely on pytest V5: `_dispatch_like_llm_loop` with `monster_specs: []` | `{ok: false}`, `monster_specs required`; bridge not called | [ ] |

**Manual live repro:** Not required for sign-off — LLM rarely emits empty `monster_specs`. If attempted via dev tooling, expect **`[Mechanics failed — start_combat: monster_specs required]`** and same HUD rules as TC-5.

## Automated cross-check (optional before sign-off)

```bash
python -m pytest app/tests/test_combat_monster_validation.py -q
python -m pytest play/tomb_gm/tests/test_validate_monster_specs.py -q
python -m pytest app/tests/test_combat_failure_narration.py -k start_combat -q
```

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **APP-028:** Failure narration strip — overlapping TC-3/TC-4 shapes; APP-027 adds **validation determinism** and **empty-spec gate** (R3).
- **APP-030:** Full combat golden-path integration (V4 happy `grave-ghoul:1` pytest) — optional TC-6 only.
- **Beat content ids:** Non-canon ids in beat regex (`hollow-knight`, `rust-slime`) still fail at R2 — content fix is a separate ticket; TC-4 uses file-hide on canon `grave-ghoul`.
- **TC-4 file rename:** Dev-only repro — **must restore** `grave-ghoul.json` before other content/engine work.
- **Mixed-tool turns:** Failed `start_combat` + successful tool same batch is out of scope (APP-027 non-goal).
- **Flaky LLM:** TC-3 may need explicit retry phrasing; pass/fail is **error prefix + no fiction + DELVE HUD**, not model echo of player text.
