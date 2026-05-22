# Human Playtest Plan: APP-036-creation-step-badge

**backlog_ticket:** APP-036  
**Commit:** pending (Stage 7 — use latest commit with APP-036 in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** Validates **Registry step badge** visibility in the right sidebar stats panel during new-game creation — engine-sourced human labels, not narration footer tokens. Automated pytest passed at impl QA (`test_ui_creation_badge.py`, 9 tests). This plan confirms live PyGame placement, step advance, post-finalize hide, and label policy in the running client.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=sk-or-v1-...`)
- [ ] Fresh session: type **`new game`** (do not Continue from a mid-creation save for TC-2–TC-5)
- [ ] Window wide enough to see **right sidebar stats panel** (above MAP panel)
- [ ] Optional log watch: `app/logs/session-YYYY-MM-DD.jsonl`
- [ ] Repo root cwd for pytest TC-1

## What to look for (all TCs)

| Bad (fail) | Good (pass) |
|------------|-------------|
| Badge shows `NAME_INPUT`, `RACE_INPUT`, `SKILLS_INPUT`, `EQUIPMENT_GOLD_CONFIRMATION`, or any `UPPER_SNAKE_CASE` footer token | Badge shows **`Registry: Name`**, **`Registry: Race`**, **`Registry: Skills`**, etc. — human labels only |
| No badge during creation; only narration `Awaiting:` footer | Green **Registry:** pill at **top of stats panel**, above character name |
| Badge still visible after finalize / at reception with live roster | Badge **gone**; stats show delver name, HP, phase badge |
| Badge stuck on `Registry: Name` after race/class commits | Badge updates on each creation advance without window resize |
| Badge disappears when resizing window mid-creation | Badge **persists** after resize until next status push (optional TC-6) |

**Expected display map** (badge text after `Registry:` prefix):

| FSM step | Badge label |
|----------|-------------|
| `NAME` | Name |
| `RACE` | Race |
| `ROLL_STATS` | Roll Stats |
| `CLASS` | Class |
| `SKILLS` | Skills |
| `SPELL_SCHOOLS` | Spell Schools |
| `SPELLS` | Spells |
| `EQUIPMENT_GOLD` | Equipment & Gold |
| `FINALIZE` | Finalize |
| `WORLD_INTRO` | Reception |

Narration footer may still show `Awaiting: RACE_INPUT` — badge must **not** mirror that token.

---

## Test cases

### TC-1: Automated regression gate (maps to spec R1–R6 — optional but recommended)

**Goal:** Confirm badge unit tests and creation finalize regression before manual play.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_ui_creation_badge.py -q` | Exit code **0**; **9 passed** | [ ] |
| 2 | From repo root: `python -m pytest app/tests/test_ui_map_creation_gate.py -q` | Exit code **0**; enrich mock regression passes | [ ] |
| 3 | From repo root: `python -m pytest app/tests/test_creation_flow.py -q` | Exit code **0**; full creation FSM passes | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

---

### TC-2: Badge visible at creation start (maps to ticket AC + spec R4)

**Goal:** After `new game`, sidebar shows `Registry: Name` before first name entry.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | Type `new game` and submit | GM prompts for delver name; creation active | [ ] |
| 3 | Look at **right sidebar → stats panel** (top, above character name) | Green rounded badge reads **`Registry: Name`** | [ ] |
| 4 | Compare to phase badge below name | Phase badge (e.g. `PREPARATION`) still visible **below** name — creation badge is **above** name | [ ] |
| 5 | Optional: read narration footer | Footer may show `Awaiting: NAME_INPUT` — badge must **not** show `NAME_INPUT` | [ ] |

**Failure signals:** No badge during creation; badge in wrong panel; badge shows internal token; crash on `new game`.

---

### TC-3: Human labels only — not footer tokens (maps to ticket AC + spec R1/R2)

**Goal:** Badge copy is player-facing; narration footer tokens never appear on the badge.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Continuing from TC-2 at NAME step | Badge reads **`Registry: Name`** | [ ] |
| 2 | Type a short name (e.g. `BadgeTest`) and submit | Race table appears in narration | [ ] |
| 3 | Read badge immediately after GM response | Updates to **`Registry: Race`** | [ ] |
| 4 | Read narration footer on same turn | Footer may show **`Awaiting: RACE_INPUT`** — badge must **not** contain `RACE_INPUT` | [ ] |
| 5 | Scan badge text at RACE step | **No** `_INPUT`, `_CONFIRMATION`, or all-caps enum substring in badge | [ ] |

**Failure signals:** Badge shows `RACE_INPUT` or any footer token; badge unchanged after name commit; badge text scraped from narration (matches footer exactly).

---

### TC-4: Badge advances through creation steps (maps to spec R3)

**Goal:** Badge tracks FSM step on each creation advance without relying on chip scrape or window resize.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Continuing from TC-3 at RACE, type `human` and submit | Stats + class tables appear | [ ] |
| 2 | Read badge after response | **`Registry: Class`** (ROLL_STATS is chained into class presentation — badge should show Class, not Roll Stats) | [ ] |
| 3 | Type `apprentice` and submit | Skills table appears | [ ] |
| 4 | Read badge | **`Registry: Skills`** | [ ] |
| 5 | Optional: advance through spell schools / spells if prompted | Badge shows **`Registry: Spell Schools`** then **`Registry: Spells`** when those steps are active | [ ] |
| 6 | Optional: reach equipment summary | Badge reads **`Registry: Equipment & Gold`** | [ ] |

**Failure signals:** Badge stuck on earlier step; badge shows wrong label for current desk; badge only updates after manual window resize.

**Note:** Exact steps after CLASS depend on class/skills (militia may skip spell steps). Focus on badge matching the **current** creation desk, not completing full intake in this TC.

---

### TC-5: Badge hidden after finalize (maps to ticket AC + spec R2/R4)

**Goal:** Post-finalize, Registry badge disappears while live roster stats appear.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | From TC-4 session **or** fresh `new game`, complete creation through finalize | APP-057 eight-input path: `Dumpy` → `human` → `apprentice` → `Lore, Spellcasting, Arcana` → `pyromancy, ether` → `ember-touch, static-lash` → `yes` | [ ] |
| 2 | Read final narration | **Phase: preparation** / **Awaiting: RECEPTION_CHOICE**; roster shows Dumpy | [ ] |
| 3 | Inspect stats panel top | **No** `Registry:` badge — row omitted entirely | [ ] |
| 4 | Inspect stats below former badge area | Character name **Dumpy**, phase badge, HP bar visible | [ ] |
| 5 | Optional: confirm APP-037 coexistence | MAP panel no longer travel-blocked (no grey overlay) | [ ] |

**Failure signals:** `Registry: Reception` or any Registry badge persists after finalize; badge visible with live roster HP; creation completed but badge still shows intake step.

---

### TC-6: Sidebar resize preserves badge (maps to spec R4 — optional)

**Goal:** Resizing the window mid-creation does not drop badge state until next status push.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Fresh `new game` → submit name → stop at RACE with badge **`Registry: Race`** | Badge visible | [ ] |
| 2 | Drag window edge to resize wider or narrower | Layout reflows; no crash | [ ] |
| 3 | Read badge immediately after resize | Still **`Registry: Race`** (not blank) | [ ] |
| 4 | Submit `human` to advance step | Badge updates to **`Registry: Class`** normally | [ ] |

**Failure signals:** Badge disappears on resize until next unrelated action; crash on resize during creation.

---

### TC-7: Mid-creation resume restores badge (maps to spec R3 session load — optional)

**Goal:** After quit/relaunch at a saved creation step, badge matches restored FSM without waiting for a player turn.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `new game` → name `ResumeBadge` → stop at RACE (race table visible) | Badge **`Registry: Race`** | [ ] |
| 2 | Press **Escape** (save and quit) | App closes; `app/session_state.json` has `creation_state.step` ≈ `"RACE"` | [ ] |
| 3 | `cd app && python main.py` | Window opens | [ ] |
| 4 | Type **`continue`** and submit **or** submit a race on first turn (APP-018 paths) | Creation resumes at race desk | [ ] |
| 5 | Read badge on first post-resume status refresh | **`Registry: Race`** — not `Registry: Name` | [ ] |

**Failure signals:** Badge missing after resume until manual turn; badge shows Name when disk step is Race; badge never appears on continue path.

**Note:** If badge lags one turn on resume, file as minor UX issue — primary sign-off uses fresh `new game` (TC-2–TC-5).

---

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket | Visible badge during `creation.active` with human step label | TC-2, TC-3, TC-4 | [ ] |
| Ticket | Badge hidden after creation / roster live | TC-5 | [ ] |
| Ticket | Data from orchestrator — never narration scrape | TC-3 steps 4–5 | [ ] |
| Ticket | Placement compatible with APP-062 layout (stats panel top) | TC-2 step 3–4 | [ ] |
| Spec R1 | Display labels ≠ footer tokens | TC-3 | [ ] |
| Spec R3 | Enriched status refresh on step advance | TC-4 | [ ] |
| Spec R4 | StatsPanel top placement; clear when inactive | TC-2, TC-5 | [ ] |
| Spec R4 | Sidebar resize cache | TC-6 (optional) | [ ] |
| Spec R3 | Session load badge | TC-7 (optional) | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **Minimum pass bar:** TC-2 + TC-3 + TC-5 required; TC-1 recommended preflight; TC-6/TC-7 optional if time-constrained.
- **APP-007 / APP-073:** Narration `Awaiting:` footer remains — badge is a **duplicate signal** for sidebar clarity, not a replacement.
- **APP-037:** Map travel block and Registry badge coexist during intake; both should clear after finalize (TC-5 step 5).
- **APP-065:** Suggestion chips and badge use separate code paths; empty chips at NAME/RACE do not affect badge visibility.
- **APP-062:** When left character panel lands, re-spot-check TC-2 step 3 — badge should remain at stats panel top.
- **Headless gap:** Pixel color/placement not automated; human TC-2 step 3 is authoritative for clerk-green badge rendering.
