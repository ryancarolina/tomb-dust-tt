# Human Playtest Plan: APP-066-sync-engine-awaiting-with-creation-step

**backlog_ticket:** APP-066
**Commit:** `e9326f1` (update after Stage 7 APP-066 commit if different)
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

## Prerequisites

- [ ] OpenRouter API key configured in app config (live LLM narration) **or** documented offline/mock path if your build supports it
- [ ] **Fresh session:** start with `new game` (avoid Continue from a half-finished save)
- [ ] Log path for today: `app/logs/session-YYYY-MM-DD.jsonl` (replace `YYYY-MM-DD` with the session date)
- [ ] Optional baseline: note pre-fix sessions may show **one `creation_drift` per creation turn** with `"awaiting_mismatch"` — that pattern is the regression this ticket removes

## AC mapping

| Ticket / spec AC | Test case |
|------------------|-----------|
| Engine `awaiting` coarse `CHARACTER_CREATION` during desk creation; drift compares **label map**, not engine | TC-1, TC-3 |
| `creation_drift` does **not** fire on every healthy creation turn | TC-1, TC-4 |
| `creation_step` snapshots still emit (APP-003 regression) | TC-2 |
| No false `phase_mismatch` during desk creation (footers omit `Phase:`) | TC-1 |
| Post-finalize reception footer does not spam false `awaiting_mismatch` | TC-5 |
| Real drift still detectable when footer ≠ step label | TC-6 (optional) |

## JSONL grep hints (after play session)

Replace `<date>` with the session file date (e.g. `2026-05-20`). Run from repo root.

**PowerShell — count drift events**

```powershell
$log = "app/logs/session-<date>.jsonl"
(Select-String -Path $log -Pattern '"type"\s*:\s*"creation_drift"').Count
```

**PowerShell — list drift lines with `awaiting_mismatch`**

```powershell
Select-String -Path $log -Pattern 'creation_drift' | Select-String -Pattern 'awaiting_mismatch'
```

**PowerShell — golden-path health check (expect zero matches on desk creation)**

```powershell
Select-String -Path $log -Pattern '"type"\s*:\s*"creation_drift".*awaiting_mismatch'
```

**ripgrep (if installed)**

```bash
rg '"type":\s*"creation_drift"' app/logs/session-<date>.jsonl
rg 'awaiting_mismatch' app/logs/session-<date>.jsonl
rg '"type":\s*"creation_step"' app/logs/session-<date>.jsonl
```

**What to inspect on a drift line (if any)**

| Field | Healthy desk creation | Failure signal |
|-------|----------------------|----------------|
| `reasons` | Absent on golden path, or **not** `["awaiting_mismatch"]` alone because footer ≠ engine | Every turn: `awaiting_mismatch` while UI progressed normally |
| `awaiting` (engine) | `CHARACTER_CREATION` | N/A by itself — not a failure |
| `narrated_awaiting` | Matches step label (e.g. `SKILLS_INPUT` on `SKILLS` step) | Granular label present but drift still logged every turn |
| `expected_awaiting` (APP-066) | Present on real mismatch probes | Missing on `awaiting_mismatch` lines after fix (optional QA) |
| `creation.active` | `true` during desk steps | `true` but drift every narration line |

**Label map (footer should match `creation.step`)** — from domain spec / `CREATION_STATUS_LABELS`:

| Step | Expected `Awaiting:` in narration |
|------|-----------------------------------|
| `NAME` | `NAME_INPUT` |
| `RACE` | `RACE_INPUT` |
| `ROLL_STATS` | `STATS_REVIEW` |
| `CLASS` | `CLASS_INPUT` |
| `SKILLS` | `SKILLS_INPUT` |
| `SPELL_SCHOOLS` | `SPELL_SCHOOLS_INPUT` |
| `SPELLS` | `SPELLS_INPUT` |
| `EQUIPMENT_GOLD` | `EQUIPMENT_GOLD_CONFIRMATION` |
| `FINALIZE` | `FINALIZE` |

## Test cases

### TC-1: Golden path — no `creation_drift` spam (maps to AC: healthy turns silent)

**Goal:** Full desk creation produces `creation_step` each turn but **does not** emit `creation_drift` with `awaiting_mismatch` on every healthy narration line.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | PyGame window opens; no traceback in terminal | [ ] |
| 2 | Type `new game` and submit | Creation starts; GM asks for delver name (`NAME` step) | [ ] |
| 3 | Complete creation through equipment confirm / finalize (name → race → stats → class → skills → spells as prompted → equipment → reception) | UI advances through steps without stuck FSM; character reaches hub/reception | [ ] |
| 4 | Open `app/logs/session-<date>.jsonl` | Multiple `"type": "creation_step"` lines with `creation.active: true` and `awaiting: "CHARACTER_CREATION"` | [ ] |
| 5 | Grep/count `"type": "creation_drift"` during desk creation turns | **Zero** lines, **or** none whose only reason is granular footer vs engine `CHARACTER_CREATION` | [ ] |
| 6 | Grep `awaiting_mismatch` in the same file for the session segment | **No** per-turn `awaiting_mismatch` while footers match the step table above | [ ] |

**Failure signals:**

- One or more `creation_drift` events **per** player creation input while play felt normal (pre-APP-066 noise pattern).
- `reasons` contains `awaiting_mismatch` when `narrated_awaiting` is `SKILLS_INPUT` (etc.) and engine `awaiting` is `CHARACTER_CREATION` — comparator still using engine awaiting.
- `phase_mismatch` on every desk turn although narration had no `Phase:` line.
- Crash, frozen creation step, or GM stuck repeating the same step.

---

### TC-2: `creation_step` regression (maps to APP-003 / observability)

**Goal:** Drift fix does not remove per-turn creation snapshots.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | During TC-1, after 3+ creation inputs | JSONL has ≥3 `creation_step` events | [ ] |
| 2 | Inspect latest `creation_step` before finalize | `data.step` advances with UI (e.g. `NAME` → `RACE` → …); `roster_len` stays `0` until finalize | [ ] |

**Failure signals:** No `creation_step` lines; `step` stuck while narration moved on.

---

### TC-3: Engine awaiting stays coarse (maps to AC / R1)

**Goal:** Engine layer remains `CHARACTER_CREATION` for entire desk creation; app layer carries granular labels.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Pick any `creation_step` line mid-creation (e.g. `step: "SKILLS"`) | `awaiting` field is `CHARACTER_CREATION` | [ ] |
| 2 | Read matching GM narration footer in UI or `gm_narration` log line | `Awaiting:` is granular (e.g. `SKILLS_INPUT`), **not** `CHARACTER_CREATION` | [ ] |
| 3 | Confirm no drift solely from (2) vs (1) | No `creation_drift` for that turn | [ ] |

**Failure signals:** Engine `awaiting` jumps per step (out of scope / unexpected); drift logged despite footer matching `SKILLS_INPUT` on `SKILLS` step.

---

### TC-4: Footer ↔ step alignment on sample steps (maps to R2)

**Goal:** Narration `Awaiting:` matches `CREATION_STATUS_LABELS` for the current step on sampled turns.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | After submitting delver **name** | Footer / narration includes `Awaiting: NAME_INPUT` or advances to `RACE_INPUT` same turn per APP-068; drift silent | [ ] |
| 2 | On **skills** step (when prompted) | Footer shows `Awaiting: SKILLS_INPUT`; grep shows no `awaiting_mismatch` for that turn | [ ] |
| 3 | On **spell schools** or **spells** step if shown | `SPELL_SCHOOLS_INPUT` / `SPELLS_INPUT` respectively; no drift | [ ] |

**Failure signals:** Footer shows wrong label (e.g. `CLASS_INPUT` while on `SKILLS`) **without** a corresponding real bug — should log `creation_drift` with `awaiting_mismatch` (TC-6). Footer wrong **and** no drift — detector broken.

---

### TC-5: Post-finalize — no false awaiting spam (maps to R3 / spec § Post-finalize)

**Goal:** After character exists, reception / `WORLD_INTRO` footers do not recreate per-turn `awaiting_mismatch` noise.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Finish creation; take 1–2 hub/reception turns (travel prompt, reception choice, etc.) | Play continues; no traceback | [ ] |
| 2 | Grep `creation_drift` after last `creation_step` with `creation.active: false` | No burst of `awaiting_mismatch` solely because footer says `RECEPTION_CHOICE` and engine says `PLAYER_ACTIONS` | [ ] |

**Failure signals:** Continuous `creation_drift` after finalize during normal reception copy; game soft-locks at hub.

---

### TC-6: Real drift still logged (optional — maps to R2 negative / spec hint)

**Goal:** Comparator still flags **true** footer vs step desync (not required for sign-off if impractical without debug).

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | *(Optional)* If you can force wrong footer (debug hook, corrupted narration, or known flaky LLM tag) | At least one `creation_drift` with `awaiting_mismatch` and `narrated_awaiting` ≠ expected label for `step` | [ ] |
| 2 | Inspect that line | `reasons` includes `awaiting_mismatch`; optional `expected_awaiting` matches label map | [ ] |

**Failure signals:** Obvious wrong footer in UI but **no** drift event (detector disabled); or drift on every healthy turn (TC-1 failure).

---

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- If TC-1 fails but pytest `test_creation_flow.py` passes locally, compare **mock** golden path vs **live LLM** footers (APP-073 tag leak, APP-069 narration/step mismatch).
- APP-036 (UI badge from engine `awaiting`) remains separate — engine will still show coarse awaiting in engine status; use `creation.step` / footer for step truth.
- Correlate `creation_advanced` (APP-004) with `creation_step` step changes in the same JSONL file when debugging ordering issues.
