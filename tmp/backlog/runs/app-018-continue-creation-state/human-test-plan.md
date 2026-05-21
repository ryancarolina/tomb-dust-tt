# Human Playtest Plan: APP-018-continue-creation-state

**backlog_ticket:** APP-018  
**Commit:** pending (Stage 7 — use working tree with `_restore_creation_from_session_state` in `app/gm/orchestrator.py` and `app/tests/test_creation_restore.py`)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope:** Mid-creation **continue**, **load game**, and **relaunch** must restore the creation FSM from `app/session_state.json` — same `creation.step` (e.g. `RACE`, `SKILLS`), not a fabricated `NAME` reset. Orchestrator-owned restore runs on first post-relaunch turn (G3a) and on resume fail/success (G3b/G3c). Automated pytest passed at impl QA; this plan validates the live PyGame client.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=…`)
- [ ] **Clean mid-creation path:** no living engine roster save in `play/workspace/` (move aside `tomb_gm.db` / campaign save if needed so startup shows **new game** only — APP-064)
- [ ] Know save location: `app/session_state.json` (written on Escape quit and 60s autosave)
- [ ] Optional log watch: `app/logs/session-YYYY-MM-DD.jsonl`
- [ ] Repo root cwd for TC-1 pytest gate

## What to look for (all TCs)

| Bad (fail) | Good (pass) |
|------------|-------------|
| After relaunch/continue at saved **RACE**, GM asks for **name** again or footer `[Awaiting: NAME_INPUT]` | Footer matches saved step: `[Awaiting: RACE_INPUT]`, `[Awaiting: SKILLS_INPUT]`, etc. |
| Variant B resume failure cites wrong step (e.g. **name** when disk was **race**) | Prose mentions correct step phrase (`race`, `skills`, …) matching pre-quit desk |
| Relaunch auto-resumes creation at boot without player input | Boot shows APP-064 startup only; restore happens on **first** submitted turn |
| **`new game`** after partial creation still restores old **SKILLS** on **`continue`** | Fresh **NAME** desk only; prior character name/step absent from narration |
| Post-finalize **`load game`** reopens creation desk at **SKILLS** | Engine roster save loads; exploration/delve play, not creation |

**Quick disk check (optional):** before relaunch, open `app/session_state.json` and confirm `creation_state.active` is true, `creation_state.step` matches where you quit, and `engine_status.awaiting` is `CHARACTER_CREATION` (when present).

---

## Test cases

### TC-1: Automated regression gate (recommended before manual play)

**Goal:** Confirm APP-018 pytest suite and related persistence tests still green.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `cd app && python -m pytest tests/test_creation_restore.py -q` | Exit code **0**; 7 tests pass (T-018a–f) | [ ] |
| 2 | `cd app && python -m pytest tests/test_engine_status_on_save.py tests/test_session_resume_failure.py tests/test_creation_block_on_new_game.py -q` | Exit code **0** | [ ] |
| 3 | `cd app && python -m pytest tests -q -k "creation_restore or continue_creation or app018"` | Exit code **0** | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

---

### TC-2: RACE mid-creation — quit, relaunch, **`continue`** (maps to T-018a / G3b)

**Goal:** Resume failure path restores **RACE** from disk; variant B mentions race, not name.

**Reach RACE:** `new game` → submit name **`Dumpy`** → stop when race table appears and footer shows **`Awaiting: RACE_INPUT`**.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At **RACE** step | Race table visible; `[Awaiting: RACE_INPUT]` in narration | [ ] |
| 2 | Press **Escape** (save and quit) | App closes; `app/session_state.json` exists with `creation_state.step` ≈ `"RACE"` | [ ] |
| 3 | `cd app && python main.py` | Window opens; startup per APP-064 (**no** engine save → prompt to type **new game**; chips show **new game** only) | [ ] |
| 4 | Type **`continue`** and submit | Variant B prose: no finished save; mentions **race** step (not name-only desk) | [ ] |
| 5 | Read footer | `[Awaiting: RACE_INPUT]` — **not** `[Awaiting: NAME_INPUT]` | [ ] |
| 6 | Submit a race (e.g. **`Human`**) | Creation advances normally (stats/class path); no “invalid name” or full restart | [ ] |

**Failure signals:** NAME desk after continue; variant B says **name** step; crash; `[Awaiting: NAME_INPUT]` at RACE save.

---

### TC-3: RACE mid-creation — quit, relaunch, desk input (maps to T-018b / G3a)

**Goal:** First post-relaunch turn restores FSM **before** routing desk input — saved `engine_status` wins over live `SETUP`.

**Setup:** Repeat TC-2 steps 1–3 (fresh **`new game` → Dumpy → RACE**, Escape, relaunch).

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | After relaunch, **do not** type `continue` | Startup narration only; creation not visibly resumed yet | [ ] |
| 2 | Type **`Human`** (or another valid race) and submit | GM treats input as **race** choice, not exploration/free text | [ ] |
| 3 | Inspect latest narration footer | Was or becomes creation-appropriate (`CLASS_INPUT`, `RACE_INPUT` on error, etc.) — **not** stuck at cold **SETUP** with empty creation | [ ] |
| 4 | Optional: read `session_state.json` before step 2 | `engine_status.awaiting` = `CHARACTER_CREATION`, `creation_state.step` = `RACE` | [ ] |

**Failure signals:** Input ignored or routed to exploration; GM asks for name again; step reset to NAME before race commit.

---

### TC-4: SKILLS mid-creation — quit, relaunch, **`continue`** (maps to T-018d / deeper step)

**Goal:** Restore works beyond RACE — **SKILLS** step and prior fields (name, class) survive relaunch.

**Reach SKILLS:** `new game` → **`Dumpy`** → pick race → complete roll/class (e.g. **`apprentice`**) → stop at skills table / `[Awaiting: SKILLS_INPUT]`.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At **SKILLS** step | Skills table or pick prompt; `[Awaiting: SKILLS_INPUT]` | [ ] |
| 2 | Escape → relaunch → **`continue`** | Variant B mentions **skills** step; footer `[Awaiting: SKILLS_INPUT]` | [ ] |
| 3 | Narration references prior choices | Name **Dumpy** / class context still coherent (not blank NAME desk) | [ ] |
| 4 | Submit valid skills (e.g. **`lore, spellcasting, arcana`**) | Skills step accepts input; creation continues | [ ] |

**Failure signals:** Drop to NAME or RACE; variant B cites wrong step; skills table missing with “start over” tone.

---

### TC-5: Same session — **`load game`** mid-creation (maps to T-018a + APP-071 variant B)

**Goal:** Without closing the app, **`load game`** during mid-creation uses restored step for variant B (no engine roster save).

**Reach RACE** (or SKILLS) as in TC-2 / TC-4; **do not quit**.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At mid-creation desk | Current step footer matches desk (e.g. `RACE_INPUT`) | [ ] |
| 2 | Type **`load game`** and submit | Friendly failure (not raw `no save session found`); variant B copy | [ ] |
| 3 | Read failure narration | Cites **current** step (**race** / **skills**), distinct from cold-start variant A | [ ] |
| 4 | Footer after failure | `[Awaiting: RACE_INPUT]` or `[Awaiting: SKILLS_INPUT]` — matches step before load | [ ] |
| 5 | Answer clerk (e.g. race or skill pick) | Desk continues; no full wipe | [ ] |

**Failure signals:** Variant A “no saved game” only; footer jumps to `NAME_INPUT`; step phrase wrong.

---

### TC-6: Post-finalize — relaunch + **`load game`** regression (maps to T-018e)

**Goal:** Finished character with engine save must **not** import stale mid-creation block from disk.

**Setup:** Complete creation through equipment/world intro into free play (or use existing living save). Ensure `bridge.has_save()` true at startup.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Play until character is registered / in world | Not on creation desk | [ ] |
| 2 | Escape → relaunch | Startup: **“You have a saved game.”** + **load game** chip | [ ] |
| 3 | **`load game`** | Resume **succeeds** — delver/roster restored, exploration narration | [ ] |
| 4 | Inspect UI | No creation step badge at NAME/RACE/SKILLS; not asked to re-enter Dumpy unless intentional new run | [ ] |

**Failure signals:** Load succeeds but opens creation at old SKILLS/RACE; variant B instead of real resume.

---

### TC-7: **`new game`** after partial creation — no stale restore (maps to T-018f / APP-015)

**Goal:** Intentional wipe clears disk; subsequent **`continue`** must not resurrect old SKILLS/RACE.

**Reach SKILLS** (TC-4 setup), then:

| Step | Action (in the running game) | Expected result | Pass |
|------|--------------|-----------------|------|
| 1 | Type **`new game`** and submit | Fresh NAME desk; `[Awaiting: NAME_INPUT]` | [ ] |
| 2 | Optional: read `session_state.json` | `creation_state.step` = `"NAME"`; no stale skills/name from prior run | [ ] |
| 3 | Type **`continue`** (do not enter a name yet) | Variant B at **name** step only — **no** mention of prior **Flupps**/skills from wiped run | [ ] |
| 4 | Footer | `[Awaiting: NAME_INPUT]` | [ ] |

**Failure signals:** Continue restores old character name or SKILLS table from pre-wipe disk.

---

### TC-8: Boot non-regression — APP-064 (maps to spec non-goals)

**Goal:** Relaunch does **not** auto-import creation at startup; player action triggers G3a restore.

**Setup:** Mid-creation app save, **no** engine save (TC-2 after Escape, before step 4).

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Relaunch after mid-creation quit | Narration: type **new game** prompt; **not** “continue where you left off” auto-resume | [ ] |
| 2 | Chips at boot | **new game** only (no **load game** when `has_save()` false) | [ ] |
| 3 | Before any input | No race/skills table until player submits first turn | [ ] |
| 4 | Then run TC-2 step 4 (`continue`) | Restore works on first turn (proves G3a, not boot load) | [ ] |

**Failure signals:** Boot shows race table without input; `_load_session` alone resumes step (orchestrator restore missing).

---

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket | `awaiting == CHARACTER_CREATION` → restore creation from save | TC-2, TC-3, TC-4, TC-5 | [ ] |
| R2 / G3a | Relaunch first non–`new game` turn restores step | TC-3, TC-8 | [ ] |
| R3 / G3b | Resume fail before variant B uses restored step | TC-2, TC-5 | [ ] |
| R4 / G3c | Resume success preserves step (not NAME clobber) | TC-6 (success path); pytest T-018c | [ ] |
| R6 | Post-finalize / stale gate no-op | TC-6 | [ ] |
| APP-015 | Post–`new game` disk wipe blocks restore | TC-7 | [ ] |
| APP-064 | Boot unchanged | TC-8 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **Long setup:** TC-4 needs ~5–10 min of creation with live LLM; TC-2/TC-3 are faster (stop at RACE).
- **Engine save rare mid-creation:** TC-6 covers post-finalize; resume-**success** during creation (T-018c) is primarily pytest — manual only if you have a slotted save still in `CHARACTER_CREATION`.
- **APP-017 batch:** Force-active reconcile may run after restore; watch for step **downgrade to NAME** when disk had RACE/SKILLS — that is a P1 regression.
- **UI `_load_session`:** May import creation in parallel with worker; if footer and desk disagree, file orchestrator vs UI race (APP-018 scope is orchestrator-owned FSM).
- **APP-036:** Step badge (if present) should match restored `creation.step` after continue — nice-to-check, not AC.
- If TC-2 passes but TC-3 fails, suspect G3a ordering (desk input before restore) rather than disk gate.
