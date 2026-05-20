# Human Playtest Plan: APP-015-clear-creation-block-on-new-game

**backlog_ticket:** APP-015  
**Commit:** `pending` (or latest containing `test_creation_block_on_new_game.py` + `_clear_creation_block_on_disk`)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../../app/README.md)  
**Save file:** `app/session_state.json` (inspect while app is running or after quit)

## Prerequisites

- [ ] OpenRouter / LLM config for live creation narration (or accept slower GM replies)
- [ ] **Backup** any personal `app/session_state.json` before TC-1 (tests mutate on-disk state)
- [ ] Optional second terminal: `Get-Content app\session_state.json` (PowerShell) or editor with reload-on-save
- [ ] Automated gate from repo root (sanity before manual):

```bash
python -m pytest app/tests/test_creation_block_on_new_game.py -q
python -m pytest app/tests -q -k "creation_block or new_game_creation"
```

## Test cases

### TC-0: Automated gate (maps to T-015a–d)

**Goal:** Pytest already green before human spends time in PyGame.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Run commands in **Prerequisites** | All selected tests pass; exit code 0 | [ ] |

**Failure signals:** Any T-015 test fails — fix before manual sign-off.

---

### TC-1: Stale SKILLS → new game → disk NAME (maps to AC, T-015a, C1–C2)

**Goal:** Mid-creation save on disk is surgically reset when player starts a new game; clerk returns to **NAME**, not SKILLS.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Launch `python main.py` from `app/` | Window opens; no traceback | [ ] |
| 2 | Type `new game` and submit | GM asks for delver name (`NAME` / name prompt) | [ ] |
| 3 | Enter delver name (e.g. `Flupps`) and submit | Race prompt | [ ] |
| 4 | Enter `human` and submit | Class / attributes table flow | [ ] |
| 5 | Enter `apprentice` and submit | Skills prompt; creation at **SKILLS** (footer or status shows `SKILLS` / skills input) | [ ] |
| 6 | **Quit app** (Escape) or wait ~60s for autosave | `app/session_state.json` exists | [ ] |
| 7 | Open `app/session_state.json` | `creation_state.step` is `SKILLS`; `name` populated (e.g. `Flupps`); `roll_result` non-empty; **not** `NAME` | [ ] |
| 8 | Relaunch app (or continue same session) | Still at skills step or resumes mid-creation UI | [ ] |
| 9 | Type `new game` and submit | GM asks for delver name again — **not** skills list for old character | [ ] |
| 10 | Re-open `app/session_state.json` | `creation_state.step` is `NAME`; `name` is `""` (empty); prior `chosen_skills` / stale `roll_result` **gone**; `narration_lines` / `input_history` may still exist (not wiped) | [ ] |

**Failure signals:** After step 9, GM still references old name/skills; disk still shows `SKILLS` or populated `name`/`roll_result`; UI stuck on skills table from prior run.

**Shortcut (optional):** Seed stale file manually (Dev-only) — write `creation_state` with `"step": "SKILLS"`, `"name": "Flupps"`, then steps 8–10 only.

---

### TC-2: load game after new game — no stale SKILLS copy (maps to T-015c, APP-071 variant B)

**Goal:** Recovery narration after failed resume uses **current** NAME memory, not pre–`new game` disk step/name.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Complete TC-1 through step 9 (stuck SKILLS cleared by `new game`) | At NAME desk in UI | [ ] |
| 2 | Type `load game` and submit | Friendly failure (no engine save / unsaved session) | [ ] |
| 3 | Read GM reply | Mentions mid-creation / unsaved; footer shows **`[Awaiting: NAME_INPUT]`** (or equivalent NAME awaiting) | [ ] |
| 4 | Scan reply text | Does **not** cite old delver name (`Flupps` or name from step 3); does **not** say you are on **SKILLS** or list prior skill picks | [ ] |

**Failure signals:** Variant B copy references SKILLS step or old name from disk that should have been cleared at step 9.

---

### TC-3: Stale engine_status cleared on new game (maps to T-015d, C2 vs APP-016)

**Goal:** Surgical clear removes mismatched `engine_status` so disk cannot pair fresh NAME creation with old delve/roster snapshot.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | After TC-1 step 7 (SKILLS on disk), note whether `engine_status` exists | If present, note `awaiting` / `roster` (may show `CHARACTER_CREATION` + empty roster after APP-016 autosave) | [ ] |
| 2 | **Optional seed:** If `engine_status` absent, stop app and add a fake block: `"engine_status": {"awaiting": "IN_DELVE", "roster": [{"display_name": "Flupps"}]}` then relaunch | File saved | [ ] |
| 3 | Run `new game` from mid-creation (TC-1 steps 8–9) | NAME desk in UI | [ ] |
| 4 | Inspect `app/session_state.json` immediately after step 3 (before long play) | `engine_status` key **absent** or `null`; `creation_state.step` is `NAME` | [ ] |
| 5 | Take one more turn or wait for autosave / quit | Fresh `engine_status` may reappear (APP-016) matching empty roster + `CHARACTER_CREATION` | [ ] |

**Failure signals:** After `new game`, disk still has pre-wipe `engine_status` with non-empty roster or `IN_DELVE` while creation is at NAME.

---

### TC-4: Non-regression — happy new game from clean boot (maps to domain non-regression)

**Goal:** Normal first-time `new game` still reaches NAME clerk when setup completes.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Rename away `app/session_state.json` (fresh boot) | No startup save prompt (APP-064) or only `new game` chip | [ ] |
| 2 | `new game` | NAME prompt; no **Could not start game** (unless env/DB broken) | [ ] |
| 3 | Enter a new name | Race step advances | [ ] |

**Failure signals:** Regression on APP-014 session start; crash; permanent error toast on first `new game`.

---

### TC-5: Failure path after new game (maps to T-015b, C3) — optional

**Goal:** If `new game` fails after engine wipe, disk/memory still NAME-fresh (not restored SKILLS).

**Note:** Hard to trigger without a broken DB or Dev mock. Skip if not reproducible; rely on TC-0 `test_t015b`.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Reproduce `Could not start game: …` after mid-creation `new game` (env-specific) | Error shown in narration/UI | [ ] |
| 2 | Inspect `app/session_state.json` | `creation_state.step` is `NAME`; stale SKILLS fields absent | [ ] |
| 3 | `load game` | Same as TC-2 — no SKILLS/old-name variant B | [ ] |

**Failure signals:** Error path leaves `step: SKILLS` on disk; autosave rewrites old block.

---

## AC sign-off

| Ticket AC | Covered by |
|-----------|------------|
| On **new game**, explicitly clear `session_state.json` **creation block** | TC-1 (disk + UI), TC-0 (automated) |

| Domain case | Covered by |
|-------------|------------|
| T-015a | TC-0, TC-1 |
| T-015b | TC-0, TC-5 (optional) |
| T-015c | TC-2 |
| T-015d | TC-0, TC-3 |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | TC-0–TC-4 pass / issues: … |

## Notes for adjacent tickets

- **APP-014:** Session end / wipe ordering — TC-4 catches gross `new game` breakage; not a full L1–L7 audit.
- **APP-016:** `engine_status` write on save — TC-3 step 5 confirms re-snapshot after clear.
- **APP-018:** Continue restore — out of scope; do not expect `load game` to resume SKILLS after intentional `new game`.
- **APP-019:** UI toast for `new game` failure — TC-5 error copy not required here.
