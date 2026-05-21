# Human Playtest Plan: APP-017-reconcile-empty-roster

**backlog_ticket:** APP-017  
**Commit:** `pending` (Stage 7 — use latest commit with APP-017 in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../../app/README.md)  
**Inspect file:** `app/session_state.json` (written on Escape / autosave / post-turn)

**Scope:** On **load game**, when the engine has an **empty `roster`** and **`awaiting: CHARACTER_CREATION`** (live or saved `engine_status`), the orchestrator must flip **`creation.active`** back to **`true`** so the desk FSM and suggestion chips work. **Step/name/race restore** is **APP-018** — do not fail APP-017 if the desk step drifts after load; fail only if creation stays inactive (empty chips at equipment, free-form explore accepted mid-desk, or post-finalize forced back to NAME).

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=…`)
- [ ] APP-016 behavior present: mid-creation saves include top-level **`engine_status`** with `awaiting: CHARACTER_CREATION` and `roster: []` (run [APP-016 human-test-plan TC-1](../app-016-snapshot-engine-status-on-save/human-test-plan.md) first if unsure)
- [ ] Optional log watch: `app/logs/session-YYYY-MM-DD.jsonl`
- [ ] Text editor for JSON edits (TC-4, TC-5)
- [ ] Repo root cwd for TC-0 pytest gate

### Pre-017 failure signals (regression — any TC)

| Bad (fail APP-017) | Good (pass) |
|--------------------|-------------|
| After mid-creation **load game**, equipment step shows **no** chips (`Yes, confirm` / `I need different gear` missing) | Equipment chips present after load (TC-2) |
| Mid-creation **load game** then typed race/class is treated as **exploration/travel** (map fiction, site tools) | Typed creation choice advances desk (race table, stats, etc.) (TC-1) |
| Post-finalize **load game** dumps player back at **NAME** desk | Normal resume / recap; slotted delver unchanged (TC-3) |
| Legacy save (no `engine_status`) crashes or corrupts narration on load | TC-4 behavior unchanged |
| Traceback on **load game** when `engine_status` present | Clean load; friendly copy if engine resume fails (APP-071) |

---

## Test cases

### TC-0: Automated regression gate (recommended before manual play)

**Goal:** Confirm T-017a–f / T-017c2 still green (maps to ticket AC + spec test plan).

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `cd app && python -m pytest tests/test_reconcile_empty_roster_on_load.py -q` | Exit code **0**; 7 tests pass | [ ] |
| 2 | From repo root: `cd app && python -m pytest tests -q -k "reconcile or empty_roster or engine_status or load_session or app_017"` | Exit code **0** | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

---

### TC-1: Mid-creation load forces desk FSM (maps to ticket AC, R1, T-017a)

**Goal:** Save mid-creation (empty engine roster), relaunch, **load game** → creation is **active**; player can continue the desk with typed input (not exploration).

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Launch app (`python main.py`) | Window opens, no traceback | [ ] |
| 2 | Type **`new game`** and submit | GM asks for delver name | [ ] |
| 3 | Enter a name (e.g. `Dumpy`) and submit | Race table / creation advance (one `\| Race \| Adjustments \|` block) | [ ] |
| 4 | Press **Escape** to quit (save-on-exit) | App closes cleanly | [ ] |
| 5 | Open `app/session_state.json` | `engine_status.awaiting` is `CHARACTER_CREATION`; `engine_status.roster` is `[]`; `creation_state` present | [ ] |
| 6 | Relaunch app → type **`load game`** and submit | Saved narration/history restored; **no** traceback | [ ] |
| 7 | Read GM response to **load game** | Friendly mid-creation copy **or** resume creation narration (APP-071 variant B) — **not** raw `no save session found` alone | [ ] |
| 8 | Type a valid race (e.g. **`human`**) and submit | Stats / class chain advances — **not** travel/site/exploration fiction | [ ] |
| 9 | Optional: inspect footer in narration | May show `Awaiting: …` for current creation step — confirms desk, not hub explore | [ ] |

**Failure signals:** Race input ignored or answered as world travel; crash on load; player stuck with no creation progression after load.

---

### TC-2: Equipment chips after load (maps to R1 + T-017e — strongest UI signal)

**Goal:** Reconcile restores **`creation.active`** such that equipment-step suggestion chips return after **load game**.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | **`new game`** → advance through creation to **equipment summary** (kit / starting gold prompt; creation still active) | Narration at equipment step | [ ] |
| 2 | Confirm chips **before** quit: **`Yes, confirm`**, **`I need different gear`** | Two player-facing chips (APP-065) | [ ] |
| 3 | Press **Escape** to save and quit | `session_state.json` has `engine_status` with empty `roster` | [ ] |
| 4 | Relaunch → **`load game`** | UI restores; no traceback | [ ] |
| 5 | Inspect suggestion chip row | **Exactly** **`Yes, confirm`** and **`I need different gear`** — **not** empty | [ ] |
| 6 | Click **`Yes, confirm`** | Input submits that literal phrase; GM advances toward finalize / world intro | [ ] |

**Failure signals:** Empty chip row at equipment after load (pre-017 symptom); internal `EQUIPMENT_*` tokens as chips.

---

### TC-3: Post-finalize load does not reactivate creation (maps to R1 row 2, T-017c)

**Goal:** Slotted delver + non-empty live **`roster`** → **load game** must **not** force NAME desk.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | **`new game`** → complete full character creation through finalize | GM confirms delver ready / hub or travel prompt | [ ] |
| 2 | Press **Escape** (or wait ≥65s autosave) | Save written | [ ] |
| 3 | Open `app/session_state.json` | `engine_status.roster` length ≥ 1; `awaiting` ≠ `CHARACTER_CREATION` | [ ] |
| 4 | Relaunch → **`load game`** | Session resumes (recap or hub) — **not** "What is your delver's name?" | [ ] |
| 5 | Sidebar stats / phase badge | Shows slotted character stats; phase not stuck in creation-only prep with empty HP fiction | [ ] |
| 6 | Optional JSON check | `creation_state` may be absent or inactive — must **not** force active desk | [ ] |

**Failure signals:** Forced back to NAME; empty roster in live status after successful finalize load.

---

### TC-4: Legacy save without `engine_status` unchanged (maps to R2 / T-017d)

**Goal:** Pre-016 saves still load cleanly; reconcile does not introduce new errors.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Complete TC-1 steps 1–4 OR use any save with **`creation_state.active: true`** and narration lines | Baseline `session_state.json` | [ ] |
| 2 | Quit app; copy file to `session_state.backup.json` | Backup safe | [ ] |
| 3 | Edit `session_state.json`: delete entire **`engine_status`** key (keep `creation_state`, narration, history) | Valid JSON; no `engine_status` | [ ] |
| 4 | Relaunch → **`load game`** | Narration/history restore; **no** traceback | [ ] |
| 5 | Continue one creation turn if mid-creation | Desk still responds (same as pre-017 baseline per T-017d) | [ ] |
| 6 | Restore backup when done | — | [ ] |

**Failure signals:** Crash on load; narration wipe; new errors in terminal only after removing `engine_status`.

---

### TC-5: Disk mid-creation + null `creation_state` forces active (maps to R2, T-017b)

**Goal:** Saved snapshot says mid-creation with empty roster while live engine is cold **`SETUP`** — reconcile still forces **`creation.active`**.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Produce a mid-creation save (TC-1 steps 1–4) | File has `engine_status` with `CHARACTER_CREATION` + `roster: []` | [ ] |
| 2 | Quit; edit JSON: set **`creation_state`** to **`null`** (keep `engine_status`) | Valid JSON | [ ] |
| 3 | Relaunch → **`load game`** | No traceback | [ ] |
| 4 | Read GM / footer after load | Creation desk engaged — friendly mid-creation message **or** clerk prompt; **not** bare startup-only idle | [ ] |
| 5 | At equipment (advance if needed), re-save → reload | Equipment chips present (TC-2 check) **or** typed creation input accepted | [ ] |

**Note:** Exact step after load may be **`NAME`** until APP-018 — that is **not** an APP-017 failure.

**Failure signals:** Player treated as fresh startup with no desk; exploration commands accepted; empty equipment chips after advancing to equipment post-load.

---

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket AC | Empty roster + inactive creation + `CHARACTER_CREATION` → force creation mode | TC-1, TC-2, TC-5 | [ ] |
| R1 | Non-empty live roster → no reactivation | TC-3 | [ ] |
| R1b | Uses `roster` only (not orphan `characters`) | TC-0 T-017f (automated); manual N/A | [ ] |
| R2 | Saved `engine_status` used when live `SETUP`; live empty roster wins | TC-5; TC-0 T-017c2 | [ ] |
| R2 | Legacy / missing `engine_status` — no new errors | TC-4 | [ ] |
| T-017e | Non-empty creation chips after reconcile | TC-2 | [ ] |

---

## Out of scope (do not fail APP-017 on these)

- **APP-018:** Restoring saved **`creation.step`**, name, race, roll after load when `creation_state` was null (TC-5 step 5 note).
- **APP-064:** Boot does not auto-restore app-only mid-creation save — player must type **`load game`**.
- **APP-019:** **`new game`** setup failure surfacing.
- **T-017f (`ROSTER_SETUP` orphan rows):** pytest only — not practical manual repro.
- **T-017c2 stale saved roster:** Covered by TC-0; live empty roster is the normal mid-creation save shape in manual play.

---

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **APP-018:** After APP-017 pass, extend manual load cases to assert saved step/name/race restore (same TC-1/5 saves).
- **APP-071:** Mid-creation **load game** may still report no engine roster save — expect variant B copy **after** reconcile, not a hard failure.
- If TC-2 fails but TC-0 passes, suspect UI load ordering (`_load_session` vs `process_turn`) — file with JSON + log excerpt.
