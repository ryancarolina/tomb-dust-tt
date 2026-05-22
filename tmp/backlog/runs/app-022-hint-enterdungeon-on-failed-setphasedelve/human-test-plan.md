# Human Playtest Plan: APP-022-hint-enterdungeon-on-failed-setphasedelve

**backlog_ticket:** APP-022  
**Commit:** pending (Stage 7 — use latest commit with APP-022 in message; impl may ship in batch commit APP-022/APP-026/APP-034)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope:** APP-022 adds a **code-owned hint** when the LLM calls **`set_phase(phase="delve")`** and the engine rejects it (typically **`preparation→delve`** on surface). The player and model should see **`compass_exits`** and **`enter_dungeon(site_address)`** guidance — not only a generic tool failure. Automated pytest (6 cases) passed at impl QA; manual play validates **live LLM tool choice + PyGame narration** (probabilistic trigger, APP-024 overlap, optional below-address suffix).

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=…`)
- [ ] **Surface exploration save:** either **`new game`** through creation to Registry hub at **Breley Keep (`32-C`)**, **or** **Continue** from a save already finalized on surface near the undercrypt entrance
- [ ] Optional log watch: `app/logs/session-YYYY-MM-DD.jsonl`
- [ ] Repo root cwd for TC-1 pytest gate

## What to look for (all TCs)

| Bad (fail) | Good (pass) |
|------------|-------------|
| Failed `set_phase(delve)` shows only **`[Mechanics failed — set_phase: …]`** with **no** mention of **`compass_exits`** or **`enter_dungeon`** | Player-visible text includes both tool names (case-insensitive) |
| Hint appears on **successful** site entry via **`enter_dungeon`** | Happy-path entry narrates normally; **no** "Do not use set_phase to enter a site" spam |
| Engine jumps to undercrypt / **`32-C-UG-1`** after failed `set_phase(delve)` alone | Sidebar **Location** stays **surface / `32-C`** until **`enter_dungeon`** succeeds |
| Hint on failed **`set_phase(ingress)`** or unrelated tool failures | Delve-entry hint **only** when wrong tool was **`set_phase(delve)`** |

**Code-owned hint (core copy — may include optional below-address suffix):**

> Do not use set_phase to enter a site. Call compass_exits to list below addresses, then enter_dungeon(site_address). enter_dungeon advances preparation→ingress→delve automatically.

**Optional suffix** when current cell has below exits (e.g. at Breley):

> Below from current cell: 32-C-UG-1, …

**Compose order with APP-024:** `[Mechanics failed — set_phase: …]` → **APP-022 hint** → APP-024-sanitized content (refusal / surface-safe text) → exploration footer (APP-077 when present). Seeing **both** refusal line and hint on the same turn is **acceptable**.

**Engine truth checks:** phase stays **preparation** (or hub surface phase) and map stays **surface layer** until successful **`enter_dungeon`**.

---

## Test cases

### TC-1: Automated regression gate (recommended before manual play)

**Goal:** Confirm APP-022 module and exploration regressions still green.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_exploration_set_phase_delve_hint.py -q` | Exit code **0**; **6** tests pass | [ ] |
| 2 | From repo root: `python -m pytest app/tests/test_exploration_site_entry_gate.py -q` | Exit code **0**; **7** tests pass (APP-024 regression) | [ ] |
| 3 | From repo root: `python -m pytest play/tomb_gm/tests/test_site_resolve.py::test_set_phase_rejects_preparation_to_delve play/tomb_gm/tests/test_site_resolve.py::test_advance_phase_for_dungeon_entry -q` | Exit code **0**; **2** tests pass | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

---

### TC-2: Setup — surface at Breley undercrypt entrance (maps to all manual TCs)

**Goal:** Reach **surface** exploration at **Breley Keep (`32-C`)** with a finalized character — primary repro site from domain spec § Manual verification.

| Step | Action (in the running game) | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | **`new game`** → complete creation (name → race → stats → class → skills → spells → equipment → reception), **or** **Continue** from a save already at hub | Character finalized; not stuck in creation | [ ] |
| 3 | If not already at Breley, travel to **`32-C`** (map click on Breley Keep cell, or type e.g. `travel to Breley Keep` / `go to 32-C`) | Sidebar **Location** shows Breley / **`32-C`**; phase **preparation** (or hub-appropriate surface phase) | [ ] |
| 4 | Confirm you are **not** inside the undercrypt yet | Map shows surface layer; current location is not `UG-1` | [ ] |

**Failure signals:** Cannot reach surface hub; crash during creation/travel; already inside undercrypt before TC-3 (reset save or `new game`).

---

### TC-3: Failed `set_phase(delve)` shows enter_dungeon hint (maps to ticket AC / R3)

**Goal:** Provoke the LLM to call **`set_phase(delve)`** from surface **preparation**; player-visible narration must include the code-owned hint naming **`compass_exits`** and **`enter_dungeon`**.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At Breley surface (`32-C`), submit an entry intent that may skip **`enter_dungeon`** — try **one at a time** until hint appears: **`enter the undercrypt now`**, **`delve into Breley undercrypt`**, **`set phase to delve`**, or **`I want to be in delve phase now`** | GM turn completes (may take thinking time) | [ ] |
| 2 | Read narration | Contains **`[Mechanics failed`** mentioning **`set_phase`** (may include error text like *Cannot transition from preparation to delve*) | [ ] |
| 3 | Read text **after** the failure banner | Includes **`compass_exits`** and **`enter_dungeon`** (substring match OK); ideally includes core phrase **"Do not use set_phase to enter a site"** | [ ] |
| 4 | Optional: if at Breley with below exits | Hint may also include **`Below from current cell:`** and an AV-GRID address such as **`32-C-UG-1`** — absence is **not** a failure if core hint present | [ ] |
| 5 | Check sidebar **Location** / map | Still **surface / `32-C`** — failed `set_phase` did **not** commit entry | [ ] |
| 6 | Optional JSONL tail | Log may show `tool_call` for `set_phase` with `ok: false`; not required for pass | [ ] |

**Failure signals:** Generic failure only with no tool-name hint; crash; location jumps to undercrypt without successful **`enter_dungeon`**.

**Note:** Live LLM may call **`enter_dungeon`** correctly on first try (TC-5 path) — retry TC-3 with more explicit **`set phase delve`** / **`switch to delve phase`** phrasing, or start a fresh surface turn. Up to **3 attempts** before escalating.

---

### TC-4: Recovery — compass_exits then enter_dungeon (maps to spec Human playtest hints)

**Goal:** After TC-3 hint, the model should recover using the correct tool chain; engine commits entry.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | On the **next turn** after TC-3 (same session at `32-C`), type **`what exits go down from here?`** or **`enter the undercrypt`** / **`go down into Breley undercrypt`** | GM responds without persistent `[Mechanics failed — set_phase]` for this turn | [ ] |
| 2 | Read narration | Entry / descent allowed; **no** repeat of the full APP-022 hint block unless another failed `set_phase(delve)` occurs | [ ] |
| 3 | Check sidebar **Location** and/or map | Shows **undercrypt / `32-C-UG-1`** (or dungeon/site layer) — **not** still surface-only | [ ] |
| 4 | Phase badge | May show **delve** or site-appropriate phase after successful entry | [ ] |

**Failure signals:** Model retries `set_phase(delve)` indefinitely with hint every turn; entry never commits after clear follow-up; crash.

**Note:** If TC-3 never triggered (model entered correctly first), TC-4 collapses into TC-5 — still pass if location commits via **`enter_dungeon`**.

---

### TC-5: Happy path — successful enter_dungeon without hint spam (regression)

**Goal:** Correct entry path does **not** surface the delve-entry hint.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | **`new game`** or reload surface save at **`32-C`** (exit undercrypt first if continuing from TC-4 — e.g. travel to surface if supported) | Back on Breley surface, phase **preparation** | [ ] |
| 2 | Type a clear entry intent — e.g. **`I enter Breley undercrypt`** or **`enter_dungeon 32-C-UG-1`** (natural language OK) | GM narrates entry; **no** `[Mechanics failed — set_phase]` for this turn | [ ] |
| 3 | Read narration | **No** "Do not use set_phase to enter a site" block | [ ] |
| 4 | Check sidebar **Location** | **Undercrypt / `32-C-UG-1`** or dungeon layer | [ ] |

**Failure signals:** Hint appears on successful entry; tools succeed but location stays surface; crash.

---

### TC-6: APP-024 coexistence — hint + fiction gate (maps to spec compose order)

**Goal:** When failed `set_phase(delve)` coincides with LLM entry prose, hint appears **and** APP-024 still strips interior success fiction.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Surface at `32-C`, prompt vivid entry — e.g. **`I plunge into the torchlit vault beneath Breley now — set delve phase`** | May show `[Mechanics failed — set_phase]` + APP-022 hint | [ ] |
| 2 | Read full narration body | Hint present; **no** sustained interior success prose ("You step into…", "torchlit corridor", "you are now inside") beneath the banner unless tools also succeeded | [ ] |
| 3 | Refusal line may appear | APP-024 threshold refusal **with** hint is OK | [ ] |
| 4 | Sidebar **Location** | Still **surface / `32-C`** if entry did not commit | [ ] |

**Failure signals:** Interior crossing prose while still on surface; hint missing when `set_phase` failed; only generic failure with no tool guidance.

**Note:** Overlaps TC-3 — if TC-3 already observed hint + refusal together, mark TC-6 pass without duplicate run.

---

### TC-7: Negative hint scope — optional / pytest-primary

**Goal:** Failed **`set_phase`** for **non-delve** phases does **not** emit the delve-entry helper. **Primarily covered by pytest** (`test_failed_set_phase_ingress_no_hint`); manual repro is optional.

| Step | Action (in the running game) | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | *(Optional)* Surface at hub, try phrasing that might fail **`set_phase(ingress)`** or other phase — e.g. **`set phase to ingress from here`** if model attempts it | If `set_phase` fails for a phase **other than delve**, narration **lacks** the full APP-022 core hint | [ ] |

**Failure signals:** Delve-entry hint on non-delve `set_phase` failure.

**Note:** Skip sign-off dependency on TC-7 if not observed — TC-1 covers this path.

---

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket AC | On failed `set_phase(delve)`, orchestrator hints **`enter_dungeon` + `compass_exits`** | TC-3 (primary), TC-1 (auto) | [ ] |
| R3 | Player-visible hint between failure banner and sanitized content | TC-3, TC-6 | [ ] |
| Recovery | Model can enter via correct tools after hint | TC-4 or TC-5 | [ ] |
| R5 regression | No hint on successful `enter_dungeon` | TC-5 | [ ] |
| APP-024 regression | Fiction gate still strips premature entry prose | TC-1 (auto), TC-6 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **LLM variance:** TC-3 is **probabilistic** — the model may call **`enter_dungeon`** immediately (skip to TC-5). Use explicit **`set phase delve`** phrasing; allow up to 3 surface turns before filing a bug.
- **APP-024:** Refusal line + hint on the same turn is **by design**; do not fail TC-6 for seeing both.
- **APP-077:** Exploration footer runs after compose — re-run TC-3 if APP-077 lands in the same save.
- **Partial success (T5):** If model batches fail `set_phase(delve)` + ok `enter_dungeon`, player should **not** see R3 hint banner — covered by pytest; no dedicated manual TC required.
- **Combat batch:** Hint R3 suppressed when combat tools fail in same batch — out of scope for this plan.
- **Commit:** Stage APP-022 test module (`app/tests/test_exploration_set_phase_delve_hint.py`) must be in the release commit before sign-off.
