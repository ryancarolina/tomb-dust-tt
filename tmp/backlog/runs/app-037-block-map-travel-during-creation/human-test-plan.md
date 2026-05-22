# Human Playtest Plan: APP-037-block-map-travel-during-creation

**backlog_ticket:** APP-037  
**Commit:** pending (Stage 7 — use latest commit with APP-037 in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** Validates **map travel UI gate** during Registry intake — muted overlay, hover hint, no map-click travel submit, re-enable after finalize. Automated pytest already passed at impl QA (`test_ui_map_creation_gate.py`). **APP-063** map cell hit-testing is still a stub (`handle_click` returns `None` even when unblocked); this plan verifies **blocked state UX** and **unblock after finalize**, not successful travel to a neighbor cell.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=sk-or-v1-...`)
- [ ] Fresh session: type **`new game`** (do not Continue from a mid-creation save for TC-2–TC-4)
- [ ] Window wide enough to see **right sidebar MAP panel** (3×3 grid under stats)
- [ ] Optional log watch: `app/logs/session-YYYY-MM-DD.jsonl`
- [ ] Repo root cwd for pytest TC-1

## Test cases

### TC-1: Automated regression gate (maps to spec R1–R6 — optional but recommended)

**Goal:** Confirm map-creation gate unit tests and creation finalize regression before manual play.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_ui_map_creation_gate.py -q` | Exit code **0**; **10 passed** | [ ] |
| 2 | From repo root: `python -m pytest app/tests/test_ui_suggestions.py app/tests/test_creation_flow.py -q` | Exit code **0**; all pass (APP-065 + post-finalize unblock) | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

### TC-2: Map blocked during creation — display on, travel off (maps to ticket AC + spec R4/R5)

**Goal:** During Registry intake the MAP panel still renders hub/fog grid but travel is visually disabled.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | Type `new game` and submit | GM asks for delver name; creation active (footer shows creation awaiting, e.g. name input) | [ ] |
| 3 | Type a short name (e.g. `GateTest`) and submit | Race table appears; still in creation | [ ] |
| 4 | Look at **right sidebar → MAP** panel | **MAP** title visible; 3×3 grid renders (fog + center hub cell with player marker) | [ ] |
| 5 | Compare grid to pre-creation baseline | Location name and scene dots still shown **below** grid (display preserved) | [ ] |
| 6 | Observe grid cells | Semi-transparent **muted/grey overlay** covers the grid area (travel disabled affordance) | [ ] |
| 7 | Move mouse **off** the map panel | Overlay remains; no crash | [ ] |

**Failure signals:** Blank map panel during creation; full-color clickable-looking grid with no overlay; map panel missing hub cell entirely; crash on creation start.

### TC-3: Hover hint while blocked (maps to ticket AC + spec R4)

**Goal:** Hovering the map during creation shows the locked hint copy.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Continuing from TC-2 (creation still active) | MAP panel shows blocked overlay | [ ] |
| 2 | Move mouse over the **MAP** panel (grid area) | Hint text appears below/near grid: **`Finish Registry intake first`** (exact string) | [ ] |
| 3 | Move mouse away from MAP panel | Hint text disappears (overlay may remain) | [ ] |
| 4 | Repeat hover on stats panel above map | Hint does **not** appear on stats — only on map hover | [ ] |

**Failure signals:** No hint on hover; wrong/paraphrased copy; hint visible without hovering; hint persists after mouse leaves map.

### TC-4: Map click no-op while blocked (maps to spec R3/R4)

**Goal:** Map clicks during creation do not queue travel input (defense in depth before APP-063 hit-test).

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Continuing from TC-2/3 at any creation step before finalize | Blocked overlay visible | [ ] |
| 2 | Click several cells on the 3×3 map grid (center + neighbors if visible) | **No** new line appears in the input box (`travel to …`); narration does not advance a travel turn | [ ] |
| 3 | Wait for any in-flight GM turn to finish, then click map again | Still no travel submit; creation step unchanged by map clicks alone | [ ] |
| 4 | Optional JSONL: tail `app/logs/session-<today>.jsonl` | No player turn text matching `travel to` from map clicks during creation | [ ] |

**Failure signals:** Input prefilled or auto-submitted with `travel to 32-C` (or similar); GM narrates travel/movement from map click alone; creation step jumps unexpectedly.

### TC-5: Map re-enabled after finalize (maps to ticket AC + spec R6)

**Goal:** After Registry intake completes, overlay and hint clear; map is no longer travel-blocked.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | From TC-2 session **or** fresh `new game`, complete creation through finalize | Use APP-057 eight-input path: `Dumpy` → `human` → `apprentice` → `Lore, Spellcasting, Arcana` → `pyromancy, ether` → `ember-touch, static-lash` → `yes` | [ ] |
| 2 | Read final narration | **Phase: preparation** / **Awaiting: RECEPTION_CHOICE**; roster shows Dumpy | [ ] |
| 3 | Inspect MAP panel | **No** muted travel-block overlay on grid | [ ] |
| 4 | Hover MAP panel | **`Finish Registry intake first`** hint does **not** appear | [ ] |
| 5 | Click map cells | Behavior unchanged from pre-APP-037 baseline (APP-063 stub: clicks may still no-op, but **blocked overlay must stay off**) | [ ] |
| 6 | Optional: resize window wider/narrower | Overlay stays off; grid still renders (APP-062 resize non-regression) | [ ] |

**Failure signals:** Overlay or hint persists after finalize; map still looks greyed at reception; creation completed but map behaves as if intake still active.

### TC-6: Block persists across creation steps (maps to spec R2 — optional)

**Goal:** Gate refreshes after each creation turn, not only on first step.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Fresh `new game` → name → pick `human` | After stats/class tables, MAP still shows blocked overlay | [ ] |
| 2 | Hover map | Hint **`Finish Registry intake first`** still appears | [ ] |
| 3 | Advance one more step (e.g. pick `apprentice`) | Overlay + hover hint still present | [ ] |

**Failure signals:** Overlay disappears mid-creation; hint missing after first creation advance.

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket | Map travel disabled during creation / desync | TC-2, TC-4, TC-6 | [ ] |
| Ticket | Hint *"Finish Registry intake first"* | TC-3 | [ ] |
| Ticket | Re-enable after finalize | TC-5 | [ ] |
| Ticket | Map displays; only travel actions blocked | TC-2 steps 4–5 | [ ] |
| Ticket | APP-062 layout compatible | TC-5 step 6 (optional) | [ ] |
| Spec R1–R6 | Automated coverage | TC-1 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **APP-063:** When map cell hit-testing lands, re-run TC-4/TC-5 step 5 — expect `travel to {addr}` submit **only** when unblocked.
- **Typed travel:** Orchestrator still rejects `travel to …` during creation (APP-008); this ticket does not block typed travel in the input box — not a failure here.
- **Resume mid-creation:** Overlay may lag until first post-resume turn refresh (known open Q2 in impl QA); use fresh `new game` for primary sign-off.
- **Minimum pass bar:** TC-2 + TC-3 + TC-5 required; TC-1 recommended preflight; TC-6 optional if time-constrained.
