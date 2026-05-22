# Human Playtest Plan: app-065-suggestion-chips-no-stale-tokens

**backlog_ticket:** APP-065  
**Commit:** `83ee79e` (or latest commit that includes `app/ui/suggestions.py` + unconditional turn refresh)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope:** Suggestion chips above the input row must be **player-facing phrases only**, sourced from code maps — never scraped `Awaiting:` tokens. Chips must **clear** when the builder returns `[]` (especially after equipment finalize). Automated pytest passed at impl QA; this plan validates the **Bumpy repro** and startup UX in the live PyGame client.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=…`)
- [ ] **Fresh path:** type **`new game`** and advance through creation to equipment (see TC-3 setup steps), **or** **Continue** from a save already at equipment summary (`creation.step` = `EQUIPMENT_GOLD`, creation active)
- [ ] **Startup path (TC-2):** know whether `play/workspace/` has a resumable save (`has_save`) — use a second run with no save folder moved aside if both variants are needed
- [ ] Optional log watch: `app/logs/session-YYYY-MM-DD.jsonl` — confirm submitted text is player phrases, not `EQUIPMENT_*` enums
- [ ] Repo root cwd for TC-1 pytest gate

## What to look for (all TCs)

| Bad (fail) | Good (pass) |
|------------|-------------|
| Chip label `EQUIPMENT_CONFIRMATION`, `EQUIPMENT_GOLD_CONFIRMATION`, `PLAYER_ACTIONS`, `SKILLS_INPUT`, or any `UPPER_SNAKE_CASE` token | `Yes, confirm`, `I need different gear`, `load game`, `new game` only |
| Equipment chip still visible after finalize / world intro | Chip row **empty** (no buttons) when not on equipment step |
| Click sends internal token to GM | Input field / log shows the **same text as the chip label** |
| GM rejects chip click as invalid creation input | Confirm chip advances; objection re-presents kit |

---

## Test cases

### TC-1: Automated regression gate (recommended before manual play)

**Goal:** Confirm unit + creation regression suites still green for APP-065.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `cd app && python -m pytest tests/test_ui_suggestions.py -q` | Exit code **0**; 17 tests pass | [ ] |
| 2 | From repo root: `cd app && python -m pytest tests/test_creation_flow.py tests/test_session_resume_failure.py -q` | Exit code **0** | [ ] |
| 3 | `rg "_extract_suggestions" app/ui/app.py` | Zero matches | [ ] |

**Failure signals:** Any pytest failure; narration scrape reintroduced — stop manual play and file bug.

---

### TC-2: Startup chips — no internal tokens (maps to AC: startup preserved)

**Goal:** At `SETUP`, chips show only curated startup phrases; never `SETUP` or `CHARACTER_CREATION` as clickable chips.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2a | **With save:** ensure `play/workspace/` has active campaign; launch app | Chips include **`load game`** and **`new game`** (order may be load then new) | [ ] |
| 2b | **Without save:** move/rename workspace save aside; launch app | Only **`new game`** chip (no `load game`) | [ ] |
| 3 | Inspect every visible chip label | **No** `UPPER_SNAKE_CASE` token (`SETUP`, `PLAYER_ACTIONS`, etc.) | [ ] |
| 4 | Click **`new game`** | Game starts creation flow; chips update on next turn (not stuck on startup set) | [ ] |

**Failure signals:** Internal enum as chip; missing `new game`; `load game` shown with no save.

---

### TC-3: Equipment step — player-facing chips only (maps to AC + R3)

**Goal:** At equipment summary, chips are **`Yes, confirm`** and **`I need different gear`**, never `EQUIPMENT_*` footer labels.

**Reach equipment:** `new game` → name → race → stats/class/skills/spells as prompted (typed input OK) → stop when narration presents **starting kit / equipment summary** and creation is still active.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Arrive at equipment summary (kit table or gold/equipment narrative) | Exactly **two** chips: **`Yes, confirm`**, **`I need different gear`** | [ ] |
| 2 | Read chip labels | **Neither** label contains `EQUIPMENT`, `_CONFIRMATION`, `_INPUT`, or all-caps enum style | [ ] |
| 3 | Optional: read GM narration footer | Footer may still say `Awaiting: EQUIPMENT_GOLD_CONFIRMATION` (or similar) — **chip row must ignore it** | [ ] |
| 4 | Advance through NAME / RACE / … steps before equipment | At those steps, chip row is **empty** (no `RACE_INPUT`, `NAME_INPUT`, etc.) | [ ] |

**Failure signals:** Any `EQUIPMENT_CONFIRMATION`-style chip; chips at NAME/RACE showing internal tokens.

---

### TC-4: Confirm chip submits player text (maps to AC: click submits label)

**Goal:** Clicking **`Yes, confirm`** sends that literal string; orchestrator treats it as equipment confirm.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At equipment step (TC-3), click **`Yes, confirm`** | Turn processes; narration advances toward finalize / world intro (no “invalid input” for token) | [ ] |
| 2 | Optional JSONL | Player line or tool input uses **`Yes, confirm`**, not `EQUIPMENT_GOLD_CONFIRMATION` | [ ] |

**Failure signals:** GM error rejecting chip; log shows internal enum as player text.

---

### TC-5: Objection chip — different gear (maps to R3 non-confirm path)

**Goal:** **`I need different gear`** is accepted and re-presents equipment (not treated as confirm).

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Reload or use a second character at equipment step | Two equipment chips visible | [ ] |
| 2 | Click **`I need different gear`** | GM re-presents kit / equipment choices; still on equipment step | [ ] |
| 3 | Chips after objection turn | Still **`Yes, confirm`** / **`I need different gear`** (or empty if step advanced) — never internal token | [ ] |

**Failure signals:** Crash; silent no-op; chip disappears permanently while still on equipment.

---

### TC-6: Stale chip cleared after finalize — Bumpy repro (maps to AC + R1)

**Goal:** Ticket repro fixed: typed confirm → post-finalize narration without equipment chip; clicking old chip impossible.

**Setup:** Reach equipment (TC-3). Prefer character name **`Bumpy`** to mirror session log, not required.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At equipment, **do not** click chips; type **`I am ready`** or **`ready`** and submit | Creation finalizes; narration moves to world intro / delver play | [ ] |
| 2 | After GM response completes, inspect chip row | **No** equipment chips; **no** `EQUIPMENT_CONFIRMATION` or similar | [ ] |
| 3 | Read latest narration | May omit `Awaiting:` line entirely — chip row must still be **empty** | [ ] |
| 4 | Try clicking where chips were | Nothing to click, or only unrelated chips (not equipment) | [ ] |
| 5 | Type a normal action (e.g. `look around`) and submit | GM responds; no error about invalid `EQUIPMENT_*` token | [ ] |

**Failure signals:** Stale **`EQUIPMENT_CONFIRMATION`** (or any equipment enum) chip remains; click sends enum and GM rejects.

---

### TC-7: Post-creation exploration — chips stay empty (maps to R2 inactive creation)

**Goal:** After finalize, `PLAYER_ACTIONS` / exploration does not resurrect equipment or creation chips.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Continuing from TC-6 in delver play | Chip row empty during free exploration (v1: no travel/combat chips) | [ ] |
| 2 | Send 2–3 turns of player text | Chips remain empty unless back at `SETUP` / `SESSION_ENDED` | [ ] |

**Failure signals:** Equipment or `PLAYER_ACTIONS` chip appears mid-delve.

---

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket | Empty builder clears stale chips every turn | TC-6 | [ ] |
| Ticket | Never show raw internal tokens | TC-2, TC-3, TC-4, TC-7 | [ ] |
| Ticket | Player-facing actions only | TC-3, TC-4, TC-5 | [ ] |
| Ticket | Equipment → `Yes, confirm` / `I need different gear` | TC-3, TC-4, TC-5 | [ ] |
| Ticket | Startup `load game` / `new game` | TC-2 | [ ] |
| Ticket | Click submits display label | TC-4 | [ ] |
| R1 | Bumpy repro: no stale chip after typed finalize | TC-6 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **Long setup:** TC-3–TC-6 need full creation to equipment (~5–10 min with LLM). Consider saving mid-creation once for repeat runs (APP-018 resume is separate scope).
- **APP-073:** Narration may still show internal `Awaiting:` in footer — **not** a failure if chips ignore it (TC-3 step 3).
- **APP-063:** No map-travel chips at `WORLD_INTRO` — empty chip row is expected.
- **Batch bleed:** `orchestrator.py` may include APP-073/075 hunks in same commit; chip behavior is isolated to `get_player_suggestions` + `suggestions.py`.
- If TC-6 fails only with **chip** confirm but passes with typed confirm, file bug against turn refresh / `creation.active` guard.
