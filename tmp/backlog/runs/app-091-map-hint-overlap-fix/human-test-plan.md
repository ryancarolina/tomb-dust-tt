# Human Playtest Plan: APP-091-map-hint-overlap-fix

**backlog_ticket:** APP-091  
**Commit:** pending (Stage 7 — use latest commit with APP-091 in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** Layout-only fix for the **map travel-block hover hint** during Registry intake. [APP-037](../app-037-block-map-travel-during-creation/human-test-plan.md) shipped overlay + hint; APP-091 moves the hint **inside** the muted 3×3 grid so footer labels (**Breley Keep**, scene line) stay legible at hub **`32-C`**. Gate behavior (`is_map_travel_blocked`, gated click, enriched status) is unchanged — this plan focuses on **hint placement**, **footer readability**, and **APP-037 non-regression**.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=sk-or-v1-...`)
- [ ] Fresh session: type **`new game`** (do not Continue from a mid-creation save for TC-2–TC-6)
- [ ] Window wide enough to see **right sidebar MAP panel** (3×3 grid under stats); default config width OK for TC-2–TC-4
- [ ] For TC-5: ability to **narrow the window** until sidebar map column is tight (~240 px map width or minimum usable window width)
- [ ] Optional log watch: `app/logs/session-YYYY-MM-DD.jsonl`
- [ ] Repo root cwd for pytest TC-1

## Test cases

### TC-1: Automated regression gate (maps to spec R3/R4 — optional but recommended)

**Goal:** Confirm hint-placement unit test and APP-037 gate suite green before manual play.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_ui_map_creation_gate.py -q` | Exit code **0**; **11 passed** (includes `test_map_view_hint_blit_inside_overlay_not_footer_row`) | [ ] |
| 2 | From repo root: `python -m pytest app/tests/test_creation_flow.py -q` | Exit code **0**; all pass (post-finalize unblock regression) | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

### TC-2: Primary repro — hint inside grid, Breley Keep legible at 32-C (maps to ticket AC + spec R1)

**Goal:** Fix the reported overlap: hover hint must sit **inside** the grey grid overlay; location name below the grid stays readable.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | Type `new game` and submit | GM asks for delver name; creation active | [ ] |
| 3 | Type a short name (e.g. `HintTest`) and submit | Race table appears; still in creation | [ ] |
| 4 | Look at **right sidebar → MAP** panel | 3×3 grid with semi-transparent **muted/grey overlay**; center hub cell at **`32-C`** | [ ] |
| 5 | Read text **below** the grid (no hover) | Location label shows **`Breley Keep`** (canon `displayName` for `32-C`); scene-progress line visible if present | [ ] |
| 6 | Move mouse over the **MAP grid area** (hover) | Hint **`Finish Registry intake first`** appears **inside** the grey 3×3 grid — centered or multi-line within the overlay bounds | [ ] |
| 7 | While hovering, read footer below grid | **`Breley Keep`** remains **fully legible** — hint text does **not** sit on the same row or obscure the location name | [ ] |
| 8 | Move mouse off MAP panel | Hint disappears; **`Breley Keep`** still visible below grid | [ ] |

**Failure signals:** Hint blitted on or overlapping the **`Breley Keep`** row; location name unreadable during hover; hint drawn below the grid on the footer row (pre-APP-091 bug); crash on hover.

### TC-3: Hint copy unchanged (maps to ticket AC + spec R3)

**Goal:** Layout fix only — default hover string is exact.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Continuing from TC-2 (creation active, blocked overlay visible) | MAP panel ready | [ ] |
| 2 | Hover MAP grid | Hint text is exactly **`Finish Registry intake first`** (not paraphrased, not truncated to unreadable fragments) | [ ] |
| 3 | Hover stats panel above map | Hint does **not** appear on stats — only on map hover | [ ] |

**Failure signals:** Wrong/paraphrased copy; hint on non-map panels; hint visible without hovering.

### TC-4: Scene line legible during hover (maps to ticket AC + spec R1)

**Goal:** Footer **scene-progress** row (dots / `Scene n/m …`) is not covered by the hover hint.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Continuing from TC-2 at any creation step before finalize | MAP shows blocked overlay + footer labels | [ ] |
| 2 | Identify scene line below **`Breley Keep`** (if rendered) | Scene dots or `Scene …` text visible below location name | [ ] |
| 3 | Hover MAP grid | Hint stays **inside** grid overlay; scene line below **`Breley Keep`** remains legible (not overlapped by hint glyphs) | [ ] |

**Failure signals:** Scene line hidden or garbled during hover; hint extends below grid bottom into footer rows.

### TC-5: Narrow sidebar — hint wraps inside overlay (maps to ticket AC + APP-062 + spec R1)

**Goal:** On a tight sidebar column, hint word-wraps and stays inside the grid overlay without colliding with footer labels.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Continuing creation session from TC-2 **or** fresh `new game` → name submitted | Blocked overlay visible | [ ] |
| 2 | **Narrow the window** horizontally until sidebar map column is tight (minimum readable width; map panel still shows 3×3 grid) | Layout reflows; MAP panel still renders | [ ] |
| 3 | Hover MAP grid | Hint appears **inside** grey overlay; may wrap to **2+ lines**; still readable | [ ] |
| 4 | While hovering, read footer | **`Breley Keep`** (and scene line if shown) remain legible below grid — no overlap | [ ] |
| 5 | Widen window again | Hint still inside grid on hover; no layout crash | [ ] |

**Failure signals:** Hint clipped off-screen; hint spills onto footer row; **`Breley Keep`** obscured; crash on resize + hover.

### TC-6: APP-037 gate behavior unchanged (maps to spec R3 — regression)

**Goal:** APP-091 is draw-layout only — travel block, overlay, and click gate still work.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | During creation (TC-2 session) | Muted overlay on grid | [ ] |
| 2 | Click several cells on the 3×3 map grid | **No** `travel to …` in input box; narration does not advance travel from map click alone | [ ] |
| 3 | Complete creation through finalize (APP-057 path: `Dumpy` → `human` → `apprentice` → `Lore, Spellcasting, Arcana` → `pyromancy, ether` → `ember-touch, static-lash` → `yes`) | **Phase: preparation** / roster live | [ ] |
| 4 | Inspect MAP panel after finalize | **No** muted travel-block overlay | [ ] |
| 5 | Hover MAP after finalize | **`Finish Registry intake first`** hint does **not** appear | [ ] |

**Failure signals:** Map click submits travel during creation; overlay or hint persists after finalize; gate behavior regressed vs APP-037 baseline.

### TC-7: Layout holds across creation steps (maps to spec R1 — optional)

**Goal:** Hint placement stays correct after creation advances, not only on first step.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Fresh `new game` → name → pick `human` | MAP still blocked; **`Breley Keep`** below grid | [ ] |
| 2 | Hover map | Hint inside grey grid; footer labels legible | [ ] |
| 3 | Advance one step (e.g. pick `apprentice`) | Overlay + correct hint placement still hold | [ ] |

**Failure signals:** Hint reverts to footer-row placement mid-creation; overlap returns after first creation advance.

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket | Hover hint does not overlap `displayName` or scene line | TC-2, TC-4 | [ ] |
| Ticket | Hint readable on narrow sidebar (APP-062) | TC-5 | [ ] |
| Ticket | Default hint string unchanged | TC-3 | [ ] |
| Ticket | Unit test for hint placement | TC-1 | [ ] |
| Spec R1 | Hint inside grid overlay; footer reserved | TC-2, TC-4, TC-5 | [ ] |
| Spec R3 | APP-037 gate unchanged | TC-6 | [ ] |
| Spec R4 | Automated placement test green | TC-1 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **Minimum pass bar:** TC-2 + TC-3 + TC-5 required; TC-1 recommended preflight; TC-6 confirms APP-037 non-regression; TC-7 optional if time-constrained.
- **Contrast:** Hint is muted text on semi-transparent grey overlay — if hard to read in TC-5, note display/GPU; not a failure unless footer overlap returns.
- **APP-063:** Full map UX / cell hit-testing is out of scope; re-run TC-6 step 2 after APP-063 if map clicks should submit travel when unblocked.
- **Dungeon path:** Travel block during creation uses surface map at `32-C`; dungeon overlay hint layout is not manually exercised here (covered by pytest green only).
- **Resume mid-creation:** Use fresh `new game` for primary sign-off; resume may lag one turn on enriched status refresh (APP-037 known note).
