# Human Playtest Plan: APP-019-surface-new-game-errors

**backlog_ticket:** APP-019  
**Commit:** pending (Stage 7 — use latest commit with APP-019 in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope:** When `setup_new_game()` fails, players must see **mapped cause + retry hint** in the narration panel (contexts **A** command, **B** death restart, **C** `run_ended` resume) — never silent success or raw `Could not start game: …`. Automated pytest passed at impl QA; this plan validates **PyGame visibility**, suggestion chips, and JSONL dual-log in the live client.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=…`)
- [ ] Known workspace: `play/workspace/` (`tomb_gm.db`, `active.json`); app autosave at `app/session_state.json`
- [ ] Log tail path: `app/logs/session-YYYY-MM-DD.jsonl` (today's date)
- [ ] Repo root cwd for TC-0 pytest gate
- [ ] **Dev inject (failure TCs only):** temporary stub at top of `Orchestrator.setup_new_game` — see [Dev inject block](#dev-inject-block-revert-after-failure-tcs) below; **revert before TC-D regression**

## What to look for (all failure TCs)

| Bad (fail) | Good (pass) |
|------------|-------------|
| Panel shows `Could not start game: campaign not found: …` or other raw engine error as primary copy | Friendly lead + mapped `{cause_line}` (e.g. “The save campaign could not be found…”) |
| “A **new game** has started” or NAME desk after setup failed | Failure tail: “registry could not open a fresh desk session” + “Type **new game** to try again” |
| JSONL has `error` (`context: setup_new_game`) but **no** matching `gm_narration` | **Both** events with identical body text |
| Two `gm_narration` lines for one failure (death path double-emit) | Exactly **one** `gm_narration` per failed attempt |
| Suggestion chips omit **`new game`** on failure | Chip row includes **`new game`** (from `[Awaiting: new game]` footer) |
| `[Error: …]` wrapper duplicating full message in panel | Single narration block only (R6 status bar **not** required) |

---

## Dev inject block (revert after failure TCs)

Failure paths are hard to hit organically. For TC-A / TC-B / TC-C, add this **first executable line** inside `Orchestrator.setup_new_game` (after the APP-015 disk-clear prelude, before L1 engine calls):

```python
# TEMP APP-019 manual QA — REMOVE before commit / TC-D
return {"ok": False, "error": "campaign not found: salt-road"}
```

**Alternative (no code edit):** lock `play/workspace/tomb_gm.db` from another process (e.g. open in DB Browser with a write transaction held) and type **`new game`** — expect DB-write `{cause_line}`. Mapped cause differs from stub; still valid if friendly copy + retry appear.

**Important:** Revert the stub (or release DB lock) before TC-D happy-path regression.

---

## JSONL verification (after each failure TC)

From repo root (PowerShell), tail today's log and grep:

```powershell
$log = "app/logs/session-$(Get-Date -Format yyyy-MM-dd).jsonl"
Select-String -Path $log -Pattern '"event":"error"' | Select-Object -Last 3
Select-String -Path $log -Pattern 'gm_narration' | Select-Object -Last 3
Select-String -Path $log -Pattern 'creation_drift' | Select-Object -Last 5
```

Or with ripgrep:

```bash
rg '"context":"setup_new_game"' app/logs/session-$(date +%Y-%m-%d).jsonl
rg 'gm_narration' app/logs/session-$(date +%Y-%m-%d).jsonl | tail -3
rg 'awaiting_mismatch' app/logs/session-$(date +%Y-%m-%d).jsonl
```

| Check | Pass |
|-------|------|
| Latest failure turn has `error` with `context: setup_new_game` and verbatim engine error in payload | [ ] |
| Matching `gm_narration` body equals panel text (no duplicate second narration for same turn) | [ ] |
| No `creation_drift` with `awaiting_mismatch` from recovery footer alone | [ ] |

---

## Test cases

### TC-0: Automated regression gate (recommended before manual play)

**Goal:** Confirm T-019a–f green before PyGame session; maps to spec automated plan.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `cd app && python -m pytest tests/test_setup_new_game_failure.py -v` | **6 passed** | [ ] |
| 2 | `cd app && python -m pytest tests -q -k "setup_new_game_failure or setup_new_game"` | All selected tests pass | [ ] |
| 3 | `cd app && python -m pytest tests/test_session_resume_failure.py -q` | APP-071 resume failure unchanged | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

---

### TC-A: Context A — explicit `new game` failure visibility (maps to R2 / T-019a–b)

**Goal:** Player types **`new game`** with setup stub active → R2 copy in panel, chips, dual JSONL.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Apply [dev inject block](#dev-inject-block-revert-after-failure-tcs); launch `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | Type **`new game`** and submit | Narration opens with **“Could not start a fresh session.”** (not `Could not start game:`) | [ ] |
| 3 | Read cause paragraph | Contains mapped line, e.g. **“The save campaign could not be found in the workspace database.”** — **not** `campaign not found: salt-road` | [ ] |
| 4 | Read retry paragraph | **“Type new game to try again”** and relaunch hint (command context only) | [ ] |
| 5 | Inspect suggestion chips | **`new game`** chip visible | [ ] |
| 6 | Click **`new game`** chip (stub still active) | Same failure copy re-shown; no crash; no NAME desk | [ ] |
| 7 | JSONL check | Dual-log per [JSONL verification](#jsonl-verification-after-each-failure-tc) | [ ] |

**Failure signals:** Blank panel after submit; raw engine string; NAME prompt; missing chips; duplicate narration lines.

---

### TC-B: Context B — death restart failure (maps to R3 / T-019c)

**Goal:** PC death with setup stub active → death/corpse line preserved + failure tail; **no** false “new game has started”.

**Setup options (pick one):**

- **Preferred if combat available:** Finalized delver → lethal encounter with inject active before death resolves.
- **Minimal if combat impractical:** Treat **T-019c pytest** as gate for context B; run TC-B only when death-in-combat is feasible in this build. Note “deferred to pytest” on sign-off if skipped.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Apply dev inject; play with a **living** slotted delver until PC death (combat or scripted lethal) | Death processed; narration appears | [ ] |
| 2 | Read death lead | `**{name}** is dead` and corpse location `**{where}**` (AV-GRID / room) preserved | [ ] |
| 3 | Read failure tail | **“registry could not open a fresh desk session”** + mapped cause + **“Type new game to try again”** | [ ] |
| 4 | Scan narration | **No** “new game has started”; **no** “What is your name?” / NAME desk | [ ] |
| 5 | Inspect chips | **`new game`** chip present | [ ] |
| 6 | JSONL check | One `gm_narration` + one `setup_new_game` error; no duplicate death narration | [ ] |

**Failure signals:** Success NAME prompt after failed setup; missing corpse line; double GM narration for one death.

---

### TC-C: Context C — `run_ended` resume failure (maps to R4 / T-019d)

**Goal:** **`load game`** after a ended run (0 HP) with setup stub → R4 copy; no NAME desk.

**Setup (without inject first):**

1. Finalized delver → die in play (or use existing save where last run ended at 0 HP).
2. Quit app (Escape) **without** typing **`new game`** after death.
3. Apply dev inject; relaunch.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Relaunch with inject active; startup shows saved-game path if engine still has campaign | App opens | [ ] |
| 2 | Type **`load game`** (or click chip) | Narration lead: **“Your previous delver did not survive (0 HP after the last fight).”** | [ ] |
| 3 | Read corpse line | Body location `{where}` from prior death | [ ] |
| 4 | Read failure tail | Same registry-failure + cause + retry as TC-B (no success NAME) | [ ] |
| 5 | Inspect chips / footer | **`new game`** chip; `[Awaiting: new game]` in narration | [ ] |
| 6 | Optional alias | Repeat with **`continue`** or **`resume`** if time — same R4 copy (shared branch) | [ ] |
| 7 | JSONL check | Dual-log; no `_creation_turn` / NAME step after failure | [ ] |

**Failure signals:** “new game has started” on failed setup; NAME desk; cold “No saved game” (wrong save state — recreate run_ended setup).

---

### TC-D: Success regression — happy paths unchanged (maps to R7 / T-019f)

**Goal:** With inject **reverted**, normal **`new game`**, death restart success, and `run_ended` success still reach NAME desk.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | **Revert dev inject** (or use fresh clone); launch app | No traceback | [ ] |
| 2 | Type **`new game`** | NAME desk; `[Awaiting: NAME_INPUT]` or equivalent; **no** setup failure copy | [ ] |
| 3 | Enter name → one creation step | Creation advances normally | [ ] |
| 4 | **Optional TC-D2 — death success:** finalized delver → PC death → restart narration | “new game has started” + NAME prompt for successor | [ ] |
| 5 | **Optional TC-D3 — run_ended success:** ended-run save, no inject → **`load game`** | Prior-delver death summary + “new game has started” + NAME prompt | [ ] |

**Failure signals:** `Could not start game:` on happy path; TC-D2/3 show failure copy without inject.

**Skip note:** TC-D steps 4–5 optional if time-boxed; step 2–3 are **required** minimum sign-off.

---

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket AC | Clear error with cause + retry on setup failure | TC-A (required); TC-B/C or TC-0 + pytest note | [ ] |
| R2 | Context A friendly copy + chips | TC-A | [ ] |
| R3 | Context B death + failure, no false success | TC-B or T-019c pytest | [ ] |
| R4 | Context C run_ended + failure, no NAME desk | TC-C or T-019d pytest | [ ] |
| R1 | Dual JSONL; single narration | TC-A/C JSONL section | [ ] |
| R7 | Happy **`new game`** → NAME | TC-D steps 2–3 | [ ] |
| R6 | No required UI status bar | N/A unless panel unreadable — document only | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **Minimum manual bar:** TC-0 + TC-A + TC-D (steps 2–3) closes APP-019 playtest if TC-B/C impractical; cite pytest T-019c/d on sign-off.
- **APP-071:** Resume failure when **no save** is separate — do not conflate with APP-019 setup failure copy.
- **R6 optional UI:** If TC-A failure copy is hard to notice after `clear_narration`, file follow-up for `_set_turn_idle("Error — try again")` — not a failure of this ticket if narration + chips are readable.
- **Inject hygiene:** Never commit the TEMP stub; grep `TEMP APP-019` before Stage 7 commit.
- **Batch context:** Death/`run_ended` success wording unchanged from APP-014 — TC-D4/5 validate non-regression only.
