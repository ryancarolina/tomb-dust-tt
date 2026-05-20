# Human Playtest Plan: APP-014-setupnewgame-session-lifecycle

**backlog_ticket:** APP-014
**Commit:** `pending` (orchestrator + T-014 tests not yet committed; baseline `c8852f8`)
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

## Prerequisites

- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=…`)
- [ ] Known workspace: `play/workspace/` (engine SQLite + `active.json`); app autosave at `app/session_state.json`
- [ ] For **TC-1**, start from a **partial creation** state (see setup below) — empty engine roster, active session, optional app autosave
- [ ] Optional log tail: `app/logs/session-YYYY-MM-DD.jsonl` (today's date)
- [ ] Optional DB spot-check (technical): `play/workspace/tomb_gm.db` — `sessions` table, `ended_at IS NULL` count after **`new game`**

### Partial-creation setup (reuse for TC-1 / TC-2)

1. Launch app → type **`new game`** → submit a delver name → advance at least one clerk step (race/class prompt visible).
2. Press **Escape** to save and quit (writes `session_state.json` + keeps engine session).
3. Relaunch — startup should **not** say "You have a saved game"; suggestion chip **`new game`** only (APP-064 path).

## Test cases

### TC-1: Partial creation → `new game` reaches NAME (maps to AC / T-014a)

**Goal:** Prior session is ended before wipe; player can restart creation without **Could not start game**.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Complete **Partial-creation setup** above; relaunch if needed | Title narration; chip **`new game`** only; no "You have a saved game" | [ ] |
| 2 | Click **`new game`** chip or type `new game` and submit | GM asks for delver name (NAME desk); narration clears stale mid-creation text | [ ] |
| 3 | Check footer / stats badge | `[Awaiting: NAME_INPUT]` (or equivalent NAME label); **not** RACE/SKILLS/PRE_DELVE | [ ] |
| 4 | Inspect narration panel | **No** line containing `Could not start game` | [ ] |
| 5 | Optional: tail JSONL | `gm_narration` for new-game start; **no** `error` event with `setup_new_game` on success path | [ ] |

**Failure signals:** `Could not start game: …`; stuck on prior creation step; crash; blank panel after submit.

### TC-2: Mid-creation retry without relaunch (maps to L1–L2 / T-014a)

**Goal:** Typing **`new game`** again during an in-flight creation desk resets to NAME in the same session.

| Step | Action (in the running game) | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From cold or after TC-1, type **`new game`** | NAME prompt | [ ] |
| 2 | Enter a name; continue until race/class (or later) clerk step | Footer advances (e.g. `[Awaiting: RACE_INPUT]`) | [ ] |
| 3 | Type **`new game`** again (do **not** quit) | GM returns to NAME prompt; prior name not treated as current character | [ ] |
| 4 | Check footer | `[Awaiting: NAME_INPUT]` only | [ ] |
| 5 | Optional: open `app/session_state.json` after turn completes | `creation_state.step` is `NAME`; no stale `name` / `roll_result` from prior attempt (APP-015 C1–C2 batch) | [ ] |

**Failure signals:** Footer still shows old step; GM references previous name as finalized; setup error string.

### TC-3: Fresh workspace `new game` regression (maps to L2–L5 non-regression)

**Goal:** Cold start still reaches creation normally after lifecycle change.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Use a fresh workspace **or** complete TC-1/TC-2 successfully | App launches without traceback | [ ] |
| 2 | Type **`new game`** | NAME desk; active session implied by clerk flow | [ ] |
| 3 | Enter name → one more creation step | Creation advances; no setup failure | [ ] |

**Failure signals:** First **`new game`** fails on empty workspace; duplicate session errors in JSONL.

### TC-4: Resumable save unaffected (maps to non-regression / APP-064 T1b)

**Goal:** Engine save + **load game** path unchanged; APP-014 does not break finished saves.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Finish character creation through Registry / first surface beat (living slotted character) | Normal play state | [ ] |
| 2 | Escape quit → relaunch | "You have a saved game" + chips **`load game`** and **`new game`** | [ ] |
| 3 | Type **`load game`** | Run resumes; roster populated; not sent back to NAME-only desk | [ ] |

**Failure signals:** Load fails after finalize; startup wrongly hides saved-game prompt.

### TC-5: Death restart starts new game (maps to L5 corpses / T-014c — optional)

**Goal:** Death path uses same `setup_new_game` hub; player sees new-game narration (corpse persistence is engine invariant — spot-check if feasible).

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | With a finalized delver, enter combat or a lethal encounter (playtest build) | PC death processed | [ ] |
| 2 | Read death + restart narration | Message that a **new game** has started; prompt for new delver name | [ ] |
| 3 | Complete NAME for successor | Fresh creation desk; no **Could not start game** | [ ] |
| 4 | Optional (technical): note prior corpse AV-GRID from death narration; later visit or DB `world_corpses` | Corpse row still present after restart | [ ] |

**Failure signals:** Soft-lock after death; setup error instead of NAME; crash on restart.

**Skip note:** If lethal play is impractical in this session, rely on **T-014c** pytest and defer TC-5.

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **APP-019:** Failed `setup_new_game` still surfaces as narration only (`Could not start game: …`); no UI toast — do not fail TC-1–3 on missing toast.
- **APP-015:** Disk creation-block clear before engine wipe is batched in `setup_new_game` entry; TC-2 step 5 validates C1–C2 if APP-015 is merged.
- **APP-018:** Mid-creation **continue** without engine save remains out of scope; TC-1 expects **`new game`**, not **load game**, after partial creation boot.
- Pre-fix symptom (fixed by L1/L1b before L2): partial creation → **`new game`** → **Could not start game** — if this reappears, treat as **blocker** regression.
