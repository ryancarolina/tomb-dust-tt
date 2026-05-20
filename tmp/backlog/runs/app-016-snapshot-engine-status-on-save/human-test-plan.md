# Human Playtest Plan: APP-016-snapshot-engine-status-on-save

**backlog_ticket:** APP-016  
**Commit:** `pending` (Stage 7 — include APP-016 in commit message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../../app/README.md)  
**Inspect file:** `app/session_state.json` (created/updated on save)

## What this ticket proves

On every app save, `_save_session()` writes a full engine snapshot under **`engine_status`** (same shape as `Orchestrator.get_status()` / JSONL `creation_finalize` logging). **Load/continue does not read this field yet** — APP-017/018 own reconcile. Manual play confirms disk truth matches what you see in-game.

## Prerequisites

- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=…`)
- [ ] Text editor for JSON (VS Code, Notepad++, etc.)
- [ ] Optional: back up or delete `app/session_state.json` before TC-1 for a clean run
- [ ] Automated-only (no manual repro): **T4d** — `get_status()` failure omits `engine_status` but still saves other fields (`test_save_omits_engine_status_on_get_status_failure`)

### Quick JSON checks

After each save trigger, open `app/session_state.json` and verify:

| Check | Mid-creation (T4a) | Post-finalize / in-delve (T4b) |
|-------|--------------------|--------------------------------|
| Top-level `engine_status` key present | Yes | Yes |
| `engine_status.ok` | `true` | `true` |
| `engine_status.awaiting` | `"CHARACTER_CREATION"` | Not `"CHARACTER_CREATION"` |
| `engine_status.roster` | `[]` (empty array) | At least one character object |
| `engine_status.active` | Non-null with `session_id` / `campaign_slug` when session exists | Same |
| `creation_state` also present | Yes — app-side FSM block | Yes |

**Failure signals (any TC):** No `session_state.json` after save; missing `engine_status` while game is running normally; `engine_status` contradicts desk (e.g. non-empty `roster` during creation); crash/traceback on save or quit; load game broken after adding `engine_status`.

---

## Test cases

### TC-1: Mid-creation save includes `engine_status` (T4a → AC)

**Goal:** First creation steps persist engine truth: `CHARACTER_CREATION` + empty roster.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Launch app (`python main.py`) | Window opens, no traceback | [ ] |
| 2 | Type `new game` and submit | GM asks for delver name | [ ] |
| 3 | Enter a name (e.g. `Dumpy`) and submit | GM advances creation (race/class prompt) | [ ] |
| 4 | Press **Escape** to quit (save-on-exit) | App closes cleanly | [ ] |
| 5 | Open `app/session_state.json` | File exists; valid JSON | [ ] |
| 6 | Inspect `engine_status` | `awaiting` is `CHARACTER_CREATION`; `roster` is `[]` | [ ] |
| 7 | Compare `creation_state.step` vs `engine_status.awaiting` | Both reflect creation (app step may be RACE or later while engine still `CHARACTER_CREATION` — that drift is why the snapshot exists) | [ ] |

### TC-2: Autosave writes `engine_status` (save trigger — 60s)

**Goal:** Autosave path includes snapshot without manual quit.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Delete or rename `app/session_state.json` | No stale file | [ ] |
| 2 | Launch app → `new game` → enter name only | Mid-creation session running | [ ] |
| 3 | Wait **≥ 65 seconds** without submitting another turn | No crash; UI idle | [ ] |
| 4 | Open `app/session_state.json` (while app still running, or after Escape) | `engine_status` present with `CHARACTER_CREATION` + empty `roster` | [ ] |
| 5 | Note `narration_lines` / `input_history` | Populated — save is not engine-only | [ ] |

### TC-3: Post-turn save updates `engine_status` (save trigger — `_process_turn` finally)

**Goal:** Each completed turn refreshes the snapshot.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Fresh `new game` → submit two creation turns (name + one choice) | Creation progressing | [ ] |
| 2 | After GM responds to second turn, open `session_state.json` | `engine_status` present | [ ] |
| 3 | Submit one more turn; re-open JSON | `engine_status` still present; `input_history` length increased vs step 2 | [ ] |

### TC-4: Post-finalize save — non-empty roster (T4b)

**Goal:** After character is slotted, snapshot shows live roster.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | `new game` → complete full character creation through finalize | GM confirms delver ready / hub or travel prompt | [ ] |
| 2 | Press **Escape** or wait for autosave | Save written | [ ] |
| 3 | Inspect `engine_status.roster` | Array length ≥ 1; character has name matching creation | [ ] |
| 4 | Inspect `engine_status.awaiting` | Not `CHARACTER_CREATION` | [ ] |
| 5 | Optional: compare to JSONL | `app/logs/session-<today>.jsonl` may contain `creation_finalize` with similar `engine_status.roster` (APP-005) — shapes should align | [ ] |

### TC-5: Legacy save without `engine_status` still loads (T4c)

**Goal:** Pre-016 saves do not break **load game** UI restore.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Complete TC-4 so engine has a resumable save | Startup offers **load game** on relaunch | [ ] |
| 2 | Quit app; copy `session_state.json` to `session_state.backup.json` | Backup safe | [ ] |
| 3 | Edit `session_state.json`: delete the entire `"engine_status"` key (keep other keys) | Valid JSON, no `engine_status` | [ ] |
| 4 | Relaunch → choose **load game** | No traceback; narration/history restore from file | [ ] |
| 5 | Gameplay | Continue works; no new errors from missing snapshot | [ ] |
| 6 | Restore backup if continuing other TCs | — | [ ] |

### TC-6: New game clears then refreshes `engine_status` (APP-015 batch — T-015d)

**Goal:** Stale snapshot from a prior session is not left on disk after **new game** entry; fresh snapshot appears after the new session saves.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Use TC-4 save (post-finalize) with populated `engine_status.roster` | Baseline file has non-empty roster in snapshot | [ ] |
| 2 | Relaunch app → type `new game` and complete through first GM prompt | New creation session started | [ ] |
| 3 | Immediately after `new game` processing (before Escape), inspect `session_state.json` if present | `engine_status` **absent** or **null** OR already refreshed to empty roster + `CHARACTER_CREATION` (APP-015 C2 clear, then APP-016 finally-save — either acceptable per spec) | [ ] |
| 4 | Enter a name → Escape | Save on exit | [ ] |
| 5 | Inspect `engine_status` | `awaiting` is `CHARACTER_CREATION`; `roster` is `[]` — must **not** retain prior character roster | [ ] |

---

## Out of scope (do not fail APP-016 on these)

- **Load/reconcile using `engine_status`** — APP-017/018; continue may still use live engine + `creation_state` only.
- **`get_status()` failure during save (T4d)** — covered by pytest; not practical to simulate in manual play.
- **Startup “saved game” prompt** — APP-064 uses engine `has_save()`, not `session_state.json` alone.

---

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **APP-017:** On **load game**, compare saved `engine_status.roster` vs live engine — manual plan should add empty-roster reconcile cases.
- **APP-018:** Continue mid-creation should prefer saved `engine_status.awaiting` when reconciling creation step.
- If TC-2 autosave feels flaky, confirm system clock and that no turn is in “thinking” state for the full 60s window.
