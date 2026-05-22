# Human Playtest Plan: APP-025-registry-hub-loop-test

**backlog_ticket:** APP-025  
**Commit:** pending (Stage 7 — use latest commit containing `test_registry_hub_loop.py` / APP-025 in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** APP-025 adds a **bridge-direct** integration test (`app/tests/test_registry_hub_loop.py`, T1–T5) for the canonical Registry hub loop at **Breley Keep (`32-C`)**: **preparation → ingress → delve → extract**. **Pytest is the primary gate** — manual play is **optional** and validates orchestrator/LLM tool dispatch + PyGame HUD that bridge-only tests cannot cover. No production code changes expected; failures here usually indicate orchestrator wiring or UI status drift, not missing test coverage.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=…`)
- [ ] Post-creation save at **`32-C`** in **preparation** (see TC-2) — **`new game`** or **Continue**
- [ ] Optional log tail: `app/logs/session-YYYY-MM-DD.jsonl`
- [ ] Right sidebar visible: stats **phase pill**, MAP panel

## Pass / fail signals (global)

| Player-visible (good) | Player-visible (failure — file bug) |
|-----------------------|-------------------------------------|
| After **`enter_dungeon`**, narration footer **`Phase: delve`**; MAP switches to **dungeon room** view (not 3×3 surface grid) | GM narrates entering undercrypt but footer still **`Phase: preparation`** and MAP still surface **`32-C`** |
| Friendly **`undercrypt`** entry lands in dungeon mode (site **`32-C-UG-1`**) | **`[Mechanics failed — enter_dungeon:`** or party stays surface with entry fiction only (APP-024) |
| After **`exit_dungeon`**, back on surface **`32-C`**; footer **`Phase: delve`** (not extract) | Exit jumps straight to **`Phase: extract`** or **`Phase: preparation`** without explicit extract declaration |
| After declaring extract, footer **`Phase: extract`** while still on surface | **`set_phase(extract)`** fails from surface/delve; phase stuck **`delve`** after player declares extraction |
| **`exit_dungeon`** does **not** clear delve clock / phase prematurely | Confusing “already extracted” narration while still underground |

**Engine truth (matches pytest T1–T5):**

| Step | Expected party state |
|------|----------------------|
| Hub ready | `address=32-C`, `mode=surface`, `phase=preparation` |
| After entry | `mode=dungeon`, `site_id=32-C-UG-1`, `phase=delve` |
| After exit site | `mode=surface`, `site_id` cleared, **`phase=delve`** |
| After extract declare | `mode=surface`, **`phase=extract`** |

**Note:** **ingress** is synchronous inside **`enter_dungeon`** — UI may skip showing **`ingress`**; that is OK if final phase is **`delve`**.

## Acceptance criteria map

| Ticket AC / Test | Manual test case(s) |
|------------------|---------------------|
| Full loop preparation → delve → extract | TC-3 + TC-4 + TC-5 (or TC-6 full path) |
| T2 — `undercrypt` resolves from `32-C` | TC-3 variant inputs |
| T4 — `exit_dungeon` keeps `phase=delve` | TC-4 (**critical**) |
| T5 — `set_phase(extract)` from surface/delve | TC-5 |
| T3 — `phase.set` audit (preparation→ingress→delve) | TC-1 pytest (not manual) |
| R1 — no illegal `set_phase(delve)` from preparation | TC-7 regression (optional) |

## Test cases

### TC-1: Automated primary gate (maps to T1–T5 — **required**)

**Goal:** Confirm bridge-direct hub loop tests green before optional manual play.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_registry_hub_loop.py -v` | Exit code **0**; **5 passed** | [ ] |
| 2 | Optional regressions: `python -m pytest play/tomb_gm/tests/test_site_resolve.py::test_advance_phase_for_dungeon_entry play/tomb_gm/tests/test_site_resolve.py::test_set_phase_rejects_preparation_to_delve app/tests/test_exploration_set_phase_delve_hint.py -q` | All pass | [ ] |

**Failure signals:** Any pytest failure in TC-1 step 1 — **stop**; file engine/bridge bug (manual play will not substitute).

---

### TC-2: Setup — Breley hub at preparation (maps to S0 bootstrap)

**Goal:** Reach finalized character at Registry hub **`32-C`** with phase **preparation** and surface map travel unblocked.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | **`new game`** → complete creation (Dumpy path: name → `human` → `apprentice` → skills → schools → spells → equipment → `yes`) | Roster populated; not stuck in creation | [ ] |
| 3 | Complete reception (e.g. **`I take the Holt contract.`** or equivalent) | Party at **`32-C`**; phase **preparation** | [ ] |
| 4 | Inspect stats sidebar phase pill | Shows **`PREPARATION`** (or equivalent uppercase label) | [ ] |
| 5 | Inspect MAP | Center **`32-C`** / **Breley Keep**; surface 3×3 grid; no creation block overlay | [ ] |
| 6 | Read narration footer (last GM line) | **`Phase: preparation`**; **`Location:`** Breley / **`32-C`** | [ ] |

**Failure signals:** Stuck in creation; wrong address; phase already **`delve`** or **`extract`** before entry attempt.

**Shortcut:** **`load game`** from save already at **`32-C`** / preparation — skip steps 2–3.

---

### TC-3: Enter Breley undercrypt — ingress + delve (maps to T1 S1, T2)

**Goal:** Natural-language entry triggers **`enter_dungeon`**; party enters dungeon mode with **`phase=delve`**.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At TC-2 state, confirm baseline | Surface **`32-C`**, **`Phase: preparation`** | [ ] |
| 2 | Submit entry intent — try until success: **`enter the undercrypt`**, **`delve into Breley undercrypt`**, **`enter undercrypt`**, or **`go down into the crypt`** | GM turn completes; no traceback | [ ] |
| 3 | Read narration footer after response | **`Phase: delve`** (ingress may not appear — OK) | [ ] |
| 4 | Inspect MAP sidebar | **Dungeon room** view (room name + exits), **not** surface AV-GRID centered on **`32-C`** | [ ] |
| 5 | Optional JSONL (same turn) | Tool **`enter_dungeon`** with **`"ok": true`**; optional **`resolved_from": "undercrypt"`** when slug used | [ ] |
| 6 | Narration quality | Entry prose present; **not** blocked by APP-024 refusal (successful tool this turn) | [ ] |

**Failure signals:** Surface location unchanged with entry fiction; **`Phase: preparation`** after “successful” entry; APP-024 threshold refusal with no **`enter_dungeon`** success; crash.

**Variant (T2):** Explicit slug — **`enter dungeon undercrypt`** — same pass criteria; site resolves to **`32-C-UG-1`**.

---

### TC-4: Exit site keeps delve phase (maps to T4 — **critical manual check**)

**Goal:** **`exit_dungeon`** returns to surface but **does not** advance to **extract** — the core contract pytest pins and UI can regress on.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Continuing from TC-3 underground | In dungeon mode, **`Phase: delve`** | [ ] |
| 2 | Move to site exit if needed (e.g. **`go back to the entrance`**, **`return to the surface`**, **`leave the undercrypt`**) — LLM should call **`exit_dungeon`** when threshold reached | GM turn completes | [ ] |
| 3 | Read narration footer | **`Phase: delve`** — **not** **`extract`** or **`preparation`** | [ ] |
| 4 | Inspect MAP | Surface **`32-C`** / Breley Keep grid restored | [ ] |
| 5 | Stats phase pill | Still **`DELVE`** | [ ] |
| 6 | Optional JSONL | Tool **`exit_dungeon`** with **`"ok": true`**; subsequent status shows **`mode: surface`**, **`phase: delve`** | [ ] |

**Failure signals:** Phase jumps to **`extract`** on exit alone; phase resets to **`preparation`**; still shows dungeon room view on surface; **`exit_dungeon`** failure with no recovery path.

---

### TC-5: Declare extract phase (maps to T5 / S3)

**Goal:** While on surface with **`phase=delve`**, player/GM **`set_phase(extract)`** succeeds.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Continuing from TC-4 on surface at **`32-C`**, **`Phase: delve`** | Baseline post-exit state | [ ] |
| 2 | Submit extract intent: **`begin extraction`**, **`declare extract`**, **`I am extracting with my salvage`**, or **`set phase to extract`** | GM turn completes | [ ] |
| 3 | Read narration footer | **`Phase: extract`** | [ ] |
| 4 | Stats phase pill | **`EXTRACT`** | [ ] |
| 5 | MAP | Still surface **`32-C`** (extract is phase, not travel) | [ ] |
| 6 | Optional JSONL | Tool **`set_phase`** with **`phase: extract`**, **`"ok": true`** | [ ] |

**Failure signals:** **`[Mechanics failed — set_phase:`** from valid post-delve surface state; phase stuck **`delve`**; crash.

---

### TC-6: Full hub loop smoke (maps to T1 end-to-end — optional single session)

**Goal:** Run TC-2 → TC-3 → TC-4 → TC-5 in one session without reload; confirms no state corruption across the loop.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Execute TC-2 through TC-5 sequentially | All steps pass | [ ] |
| 2 | **`Escape`** save + quit; relaunch **`python main.py`** → **`load game`** | Session resumes | [ ] |
| 3 | After load, check footer + phase pill | **`Phase: extract`**, surface **`32-C`** preserved | [ ] |

**Failure signals:** Save/load drops phase to **`preparation`** or **`delve`** incorrectly; crash on resume.

**Skip if:** Time-boxed — TC-1 pytest already covers bridge loop; TC-6 is release-smoke overlap with APP-052.

---

### TC-7: Regression — failed `set_phase(delve)` hint still works (maps to APP-022 — optional)

**Goal:** Before TC-3, confirm illegal surface **`set_phase(delve)`** still shows **`enter_dungeon`** guidance (not a hub-loop failure, but same repro site).

| Step | Action (in the running game) | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Fresh **`32-C`** / **preparation** (reset or **`new game`**) | Surface hub | [ ] |
| 2 | Submit **`set phase to delve`** or **`I want to be in delve phase now`** | GM may fail **`set_phase(delve)`** | [ ] |
| 3 | Read narration | Contains **`compass_exits`** and **`enter_dungeon`** hint; phase stays **preparation** until TC-3-style entry | [ ] |

**Failure signals:** Hint missing; engine enters undercrypt without **`enter_dungeon`**.

**Skip if:** TC-3 already succeeded via correct **`enter_dungeon`** path and time is limited.

---

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | TC-1 pass + optional TC-3–5 pass / issues: … |

## Notes for next ticket

- **Primary gate:** TC-1 pytest — manual TC-3–5 are **optional** smoke for orchestrator/UI; impl QA already PASS on bridge-only scope.
- **T3 (`phase.set` audit):** Not practical in PyGame — stays pytest-owned via `test_enter_dungeon_logs_ingress_phase_transitions`.
- **Out of scope v1:** Holt quest turn-in (APP-085), registry stamp buy, King's Road travel beat (APP-023), mock-LLM golden path (APP-051), full release smoke (APP-052).
- **Phase pill colors:** `theme.py` may label **`extraction`** while engine phase is **`extract`** — text label **`EXTRACT`** is the pass signal; color mismatch alone is not a hub-loop failure.
- **Escalate human if:** TC-1 fails; TC-4 shows **`extract`** immediately after exit; TC-3 entry succeeds in prose but footer stays **`preparation`**.
