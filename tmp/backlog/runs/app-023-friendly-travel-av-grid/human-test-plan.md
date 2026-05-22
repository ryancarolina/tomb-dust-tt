# Human Playtest Plan: APP-023-friendly-travel-av-grid

**backlog_ticket:** APP-023  
**Commit:** pending (Stage 7 — use latest commit containing `resolve_surface_address` / APP-023 in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** APP-023 adds exit-scoped **`resolve_surface_address`** so friendly surface names (e.g. **`kings road`**) map to legal compass exits before `world_travel` / `process_beat` travel. **Primary manual repro:** party at Registry hub **`32-C`** (Breley Keep) during surface play → **`travel to kings road`** → land **`33-C`** (King's Road east bend), **not** route-only neighbor **`32-D`**. Automated pytest (T1–T8) passed at impl QA; manual play validates **LLM tool choice**, **PyGame map/status updates**, and **beat vs bridge** paths mocks do not fully cover.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=sk-or-v1-...`)
- [ ] Fresh or known save at surface **`32-C`** after creation finalize (see TC-2)
- [ ] Optional log tail: `app/logs/session-YYYY-MM-DD.jsonl` (recommended for TC-3 / TC-6)
- [ ] Right sidebar visible: **MAP** panel, stats, phase badge

## Pass / fail signals (global)

| Player-visible (good) | Player-visible (failure — file bug) |
|-----------------------|-------------------------------------|
| After friendly travel, MAP footer shows **`King's Road (east bend)`** and address **`[33-C]`** | Party still at **`32-C`** / **Breley Keep** after successful travel narration |
| Friendly query resolves to **`33-C`**, not **`32-D`** (Heartland mile post) | Lands on **`32-D`** or stays at **`32-C`** when query is **`kings road`** |
| GM narrates arrival on the King's Road; map center cell moves **east** from hub | **`[Mechanics failed — world_travel:`** with **`UNKNOWN_ADDRESS`** for **`kings road`** from **`32-C`** |
| Unknown name (not in legal exits) → failure message listing **nearby exit names**; **no** move | Silent no-op; party teleports to wrong region; travel succeeds with no tool call |
| **`travel to undercrypt`** → hint toward **`enter_dungeon`**, **no** surface hop to **`32-C-UG-1`** | Party address becomes **`32-C-UG-1`** via **`world_travel`** alone |

## Acceptance criteria map

| Ticket AC / Req | Test case(s) |
|-----------------|--------------|
| Map friendly place names to AV-GRID for surface travel via engine `world.py` | TC-3 (primary), TC-4 |
| R5 — `bridge.world_travel` pre-resolve | TC-3, TC-5 |
| R6 — `process_beat` shared resolver | TC-4 |
| R4 — layered fallback → `USE_ENTER_DUNGEON` | TC-6 |
| R3 — unknown → hints, no travel | TC-7 |
| R7 — canonical passthrough unchanged | TC-5 |
| Stay put / compound gate (not `32-C` for `kings road`) | TC-3 step 6 |

## Test cases

### TC-1: Automated regression gate (maps to T1–T8 — optional but recommended)

**Goal:** Confirm resolver + bridge + beat tests green before manual play.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest play/tomb_gm/tests/test_world.py play/tomb_gm/tests/test_beat.py play/tomb_gm/tests/test_site_resolve.py -q` | Exit code **0**; **32 passed** | [ ] |
| 2 | Optional focused: `python -m pytest play/tomb_gm/tests/test_world.py -k "kings_road or friendly" -q` | King's Road + bridge T8 tests pass | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

### TC-2: Setup — Breley Keep `32-C` ready for surface travel (maps to exploration fixture)

**Goal:** Reach post-creation Registry hub with map travel **unblocked** and party at **`32-C`**.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | **`new game`** → complete creation (Dumpy path: name → `human` → `apprentice` → skills → schools → spells → equipment → `yes`) | Roster populated; footer **`Location: 32-C`**; **`Awaiting: RECEPTION_CHOICE`** | [ ] |
| 3 | Complete reception (e.g. **`I take the Holt contract.`** or equivalent) | Phase **preparation** (or surface explore); still at **`32-C`** | [ ] |
| 4 | Inspect MAP sidebar | Center hub cell **`32-C`**; footer label **`Breley Keep`**; **no** grey “Finish Registry intake first” overlay (post-finalize) | [ ] |
| 5 | Confirm stats / narration footer | Address **`32-C`**; **not** in combat or site/dungeon mode | [ ] |

**Failure signals:** Stuck in creation; map travel blocked after finalize; crash; party not at **`32-C`**.

**Shortcut:** **`load game`** from a save already at **`32-C`** with finished roster — skip steps 2–3.

### TC-3: Primary — `travel to kings road` from Breley Keep (maps to T1, T6, T8, ticket AC) — **required**

**Goal:** Friendly name **`kings road`** resolves exit **`33-C`** (King's Road east bend), not current cell **`32-C`** or route-only **`32-D`**.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At TC-2 state, confirm MAP shows **`Breley Keep`** / **`[32-C]`** | Baseline hub position | [ ] |
| 2 | Type **`travel to kings road`** and submit | GM responds (thinking beat OK); no traceback | [ ] |
| 3 | Read MAP sidebar after response | Footer **`King's Road (east bend)`** (or equivalent display name); address **`[33-C]`**; center cell moved **east** from hub | [ ] |
| 4 | Read narration / status footer | **`Location: 33-C`** (or King's Road prose); party **not** still at Breley Keep | [ ] |
| 5 | Optional JSONL (same turn) | Tool **`world_travel`** (or beat travel) with **`"ok": true`**; payload includes **`"to": "33-C"`** and **`"from": "32-C"`**; optional **`resolved_from": "kings road"`** | [ ] |
| 6 | Sanity: address is **`33-C`**, not **`32-D`** or **`32-C`** | Compound gate: display-name match wins over route-only mile post | [ ] |
| 7 | Submit neutral line (e.g. **`I look around.`**) | Next turn completes; location remains **`33-C`** | [ ] |

**Failure signals (pre-APP-023 regression):** **`UNKNOWN_ADDRESS`** / **`NO_DESTINATION`** for **`kings road`**; party unchanged at **`32-C`**; lands on **`32-D`**; GM narrates travel with **no** successful tool/mechanical move.

**Variant inputs (same pass criteria):** **`Travel to King's Road.`** · **`We go to kings road.`** — apostrophe/casing should not block resolution.

### TC-4: Beat path — prose travel line (maps to T2, R6)

**Goal:** `process_beat` travel intent uses the same resolver when AV-GRID regex misses.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Return to **`32-C`** if needed (map click **`32-C`** neighbor or **`travel to 32-C`** / walk back via GM) | Party at Breley hub | [ ] |
| 2 | Type **`We travel to kings road.`** (beat-style prose, no explicit grid id) and submit | GM responds | [ ] |
| 3 | MAP + footer | Party at **`33-C`** / King's Road east bend — same as TC-3 | [ ] |
| 4 | Optional JSONL | **`process_beat`** tool with travel success; party address **`33-C`** in subsequent status | [ ] |

**Failure signals:** Beat travel leaves party at **`32-C`** while narration claims movement; **`NO_DESTINATION`** for valid friendly name.

**Skip if:** TC-3 already exercised beat path (LLM chose `process_beat` instead of `world_travel`) — note which tool fired in JSONL.

### TC-5: Canonical passthrough + map click regression (maps to R7, map unchanged)

**Goal:** Canonical ids and map clicks still work; friendly resolver does not break direct travel.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | From **`33-C`**, click an adjacent **legal** map cell that sends **`travel to <canonical-id>`** (e.g. back toward **`32-C`** if shown as clickable) | Travel succeeds; address updates to clicked id | [ ] |
| 2 | From **`32-C`**, type **`travel to 33-C`** and submit | **`ok`** travel to **`33-C`** without friendly resolution error | [ ] |
| 3 | MAP after step 2 | **`[33-C]`** centered; friendly-name TC-3 behavior unchanged | [ ] |

**Failure signals:** Map click no-op (non-blocked phase); canonical id rejected; double-resolve error in logs.

### TC-6: Undercrypt — layered fallback, not surface travel (maps to T5, R4)

**Goal:** Query matching UG exit returns **`USE_ENTER_DUNGEON`** intent; party must **`enter_dungeon`**, not `world_travel` into layered id.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Return party to **`32-C`** (load save or travel back) | At Breley hub | [ ] |
| 2 | Type **`travel to undercrypt`** and submit | GM responds | [ ] |
| 3 | MAP / status | Address still **`32-C`** (surface) — **not** **`32-C-UG-1`** | [ ] |
| 4 | Read narration | Directs player toward **`enter_dungeon`** / undercrypt entry / compass exits — **no** narrated arrival inside the crypt via surface travel alone | [ ] |
| 5 | Optional follow-up: **`enter breley undercrypt`** or **`enter dungeon at 32-C-UG-1`** | Site/dungeon entry succeeds separately (out of APP-023 scope but confirms layered id is valid via correct tool) | [ ] |

**Failure signals:** Party address jumps to **`32-C-UG-1`** from step 2 alone; silent failure with no enter hint.

### TC-7: Unknown friendly name — fail closed with hints (maps to T3/T7, R3)

**Goal:** Global duplicate names **outside legal exits** do not move the party; message lists nearby options.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At **`32-C`**, type **`travel to silversea cove`** and submit | GM responds | [ ] |
| 2 | MAP / status | Party **unchanged** at **`32-C`** | [ ] |
| 3 | Read narration | Travel **failed** or GM explains unknown destination; message mentions **legal exits** / nearby place names (e.g. Heartland, Crystaline hills, King's Road) — not a fake arrival at Silversea | [ ] |
| 4 | Optional JSONL | Tool result **`ok": false`** with resolver/beat error (**`UNKNOWN_ADDRESS`** / **`NO_DESTINATION`**) | [ ] |

**Failure signals:** Party teleports to a distant coast; silent no-op with success fiction; crash.

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket AC | Friendly **`kings road`** → AV-GRID surface travel from Breley | TC-3 (required) | [ ] |
| R5 | `bridge.world_travel` resolves friendly `to_address` | TC-3, TC-5 | [ ] |
| R6 | `process_beat` travel shares resolver | TC-4 | [ ] |
| R4 | UG name → enter_dungeon hint, not surface travel | TC-6 | [ ] |
| R3 | Unknown name → hints, no move | TC-7 | [ ] |
| R7 | Canonical id / map click unchanged | TC-5 | [ ] |
| Compound gate | **`33-C`**, not **`32-D`**, for **`kings road`** | TC-3 step 6 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **`tools.py` schema:** LLM tool description may still say AV-GRID-only (optional hygiene on close); behavior is what this plan validates — escalate if model never calls `world_travel` with friendly string despite player intent.
- **APP-063:** Friendly map labels / click-to-name UX depends on APP-023 strings but is **out of scope** here — map still submits canonical ids.
- **Reception step:** If LLM blocks travel until contract accepted, complete TC-2 step 3 first; travel mechanics are unchanged by reception flavor.
- **Wilderness encounter:** Rare travel flags may fire on **`33-C`** arrival — not a failure if address still updates correctly.
- **Minimum manual bar:** TC-1 + TC-2 + **TC-3** required; TC-4–TC-7 recommended before marking feature table-verified.
