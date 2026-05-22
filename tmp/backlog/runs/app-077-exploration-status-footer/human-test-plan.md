# Human Playtest Plan: APP-077-code-owned-exploration-status-footer

**backlog_ticket:** APP-077  
**Commit:** pending (Stage 7 — use latest commit containing APP-077 / `format_exploration_status` in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope note:** APP-077 makes exploration/combat status **code-owned**: LLM bracket lines and meta banners are stripped from prose; **one authoritative footer** is appended from `bridge.status()`. Primary manual repro: footer **GP matches stats sidebar**, **exactly one** `[Location:` line per turn, combat footer includes **`Turn:`**. Automated pytest (10 cases + APP-024 regression) passed at impl QA; manual play validates **live LLM variance**, **PyGame narration layout**, and **sidebar ↔ footer consistency** mocks do not cover.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=sk-or-v1-...`)
- [ ] Fresh or resumed save at surface **`32-C`** after creation finalize (see TC-2)
- [ ] Optional log tail: `app/logs/session-YYYY-MM-DD.jsonl` (recommended for TC-5 / TC-6)
- [ ] Right sidebar visible: **Stats** (Gold GP), **MAP**, phase badge
- [ ] Repo root cwd for TC-1 pytest gate

## Pass / fail signals (global)

| Player-visible (good) | Player-visible (failure — file bug) |
|-----------------------|-------------------------------------|
| Each exploration/combat GM turn ends with **exactly one** bracket line starting `[Location:` | **Two or more** `[Location:` blocks in the same narration turn |
| Footer **GP** number matches **Stats → Gold** sidebar for active PC | Footer shows a GP value **different** from sidebar (e.g. LLM `GP: 999` survived in footer region) |
| Narration **body** has scene prose only — **no** inline `[Location: … \| … \| GP: …]` mid-paragraph | Bracket status line appears **inside** body prose above the final footer |
| Body has **no** stray `Awaiting: PLAYER_ACTIONS` / `Awaiting: COMBAT_TURN` lines scraped from LLM | Standalone `Awaiting:` token line in narration body (not in single code footer) |
| Combat turns: footer includes `\| Turn: … \|` before `Awaiting:` | Combat turn missing `Turn:` segment while combat is active |
| No `**Campaign Memory Updated:**` or `---` memory banner after turns | Meta memory banner visible in narration panel |
| APP-024 refusal turns still show footer after code refusal line | Bracket-only turn (footer alone, no prose) on normal exploration turns |

**Footer shape reference (non-combat):**

```text
[Location: {address} | Phase: {phase} | HP: {hp}/{max} | Fortune: {f}/{max} | GP: {gold} | Awaiting: {awaiting}]
```

**Combat adds:** `| Turn: {turn_id} |` before `Awaiting:`.

## Acceptance criteria map

| Ticket AC / Req | Test case(s) |
|-----------------|--------------|
| Exploration footer contract (code-owned from engine) | TC-3, TC-4, TC-5 |
| Combat footer contract (`Turn:` when combat active) | TC-6 |
| Strip LLM wrong GP — engine GP only in footer | TC-3 step 5, TC-5, TC-6 step 4 |
| Strip meta narration leaks | TC-7 |
| Empty/strip body still append footer | TC-8 (refusal path) |
| Wire exploration + combat emit paths | TC-3–TC-6 |
| APP-024 regression (refusal + footer) | TC-8 |
| APP-073 creation regression (unchanged) | TC-1 step 3 |

## Test cases

### TC-1: Automated regression gate (maps to spec test matrix — optional but recommended)

**Goal:** Confirm APP-077 unit/integration tests and sibling regressions green before manual play.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_exploration_status_footer.py -q` | Exit code **0**; **10 passed** | [ ] |
| 2 | From repo root: `python -m pytest app/tests/test_exploration_site_entry_gate.py -q` | Exit code **0**; **7 passed** (in-dungeon bypass asserts code footer) | [ ] |
| 3 | From repo root: `python -m pytest app/tests/test_creation_flavor_sanitize.py -q -k status` | Exit code **0**; creation status strip regressions pass | [ ] |
| 4 | Optional: `python -m pytest app/tests/test_exploration_set_phase_delve_hint.py -q` | Exit code **0** | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

---

### TC-2: Setup — post-creation surface at Breley `32-C` (maps to exploration fixture)

**Goal:** Reach post-finalize Registry hub with map travel unblocked and readable stats sidebar.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | **`new game`** → complete creation (Dumpy path: name → `human` → class → skills → schools → spells → equipment → confirm) | Roster populated; creation completes | [ ] |
| 3 | Complete reception / contract if prompted | Phase **preparation** (or surface explore); party at **`32-C`** | [ ] |
| 4 | Inspect MAP sidebar | Center hub **`32-C`** / Breley Keep; no creation travel block overlay | [ ] |
| 5 | Read Stats sidebar **Gold** value (note number, e.g. `50 GP`) | Gold displayed for active PC | [ ] |
| 6 | Read first exploration turn footer (after neutral action, e.g. **`I look around.`**) | Single `[Location: 32-C | Phase: preparation | … | GP: {same as sidebar} | Awaiting: …]` | [ ] |

**Failure signals:** Stuck in creation; crash; no footer on exploration turn; GP mismatch at setup.

**Shortcut:** **`load game`** from save already at **`32-C`** with finished roster — skip steps 2–3; still run step 5–6.

---

### TC-3: Surface exploration — single code footer + GP authority (maps to ticket AC — **required**)

**Goal:** Every surface exploration turn shows **one** engine footer; GP in footer matches stats panel, not any gold mentioned in GM flavor.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At TC-2 state, note Stats **Gold** (sidebar) | Baseline GP recorded | [ ] |
| 2 | Submit **`I look around the Registry yard.`** | GM responds; no traceback | [ ] |
| 3 | Count `[Location:` occurrences in **entire** narration block for this turn | **Exactly 1** — at the **bottom** of the message | [ ] |
| 4 | Compare footer `GP: {n}` to Stats sidebar Gold | **Same integer** | [ ] |
| 5 | Scan narration **body** (above footer) | **No** bracket line containing `GP:`; prose may mention coins/flavor but not a second status bracket | [ ] |
| 6 | Footer `Location` / `Phase` / `Awaiting` | Match MAP address / phase pill / engine state (e.g. `PLAYER_ACTIONS`) | [ ] |
| 7 | Optional JSONL | Turn has composed narration; optional `exploration_drift` event if LLM had wrong bracket (telemetry only — not required for pass) | [ ] |

**Failure signals (pre-APP-077 regression):** Duplicate bracket lines; footer GP ≠ sidebar; LLM-authored `[Location: … | GP: 61 | …]` visible in body **or** wrong GP in footer region.

**Variant:** Repeat steps 2–5 after **`travel to kings road`** (APP-023) — footer `Location` updates to **`33-C`** (or display name) with GP still matching sidebar.

---

### TC-4: Delve — footer uses display address + delve phase (maps to F2 / golden delve fixture)

**Goal:** In-dungeon turns show site/room display in footer; phase reflects delve.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | From **`32-C`**, enter Breley undercrypt (e.g. **`enter breley undercrypt`** or **`enter dungeon`**) | Entry succeeds; party moves to dungeon layer | [ ] |
| 2 | Read MAP / status | Address **`32-C-UG-1`** (or deeper); phase **delve** or **ingress** | [ ] |
| 3 | Submit neutral action (e.g. **`I listen at the door.`**) | GM responds | [ ] |
| 4 | Read footer | `[Location: …UG-1…` with optional **`/` room label**; `Phase: delve` (or ingress); **one** bracket line | [ ] |
| 5 | Footer GP vs sidebar | Still matches Stats Gold | [ ] |

**Failure signals:** Missing footer in dungeon; surface address in footer after entry; duplicate brackets.

---

### TC-5: Wrong-GP strip defense — body clean, footer authoritative (maps to integration test intent)

**Goal:** Even when LLM embeds status tags (common pre-APP-077 failure), player sees **engine GP only** in the single footer. Human cannot force wrong GP every run — this TC validates **structural** guarantees observable without mocking.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Play **3–5** exploration turns (surface or delve): travel, look, talk to NPC, quest line | Each turn completes | [ ] |
| 2 | For **each** turn, count `[Location:` | Always **1** | [ ] |
| 3 | For **each** turn, footer GP vs sidebar | Always **match** | [ ] |
| 4 | For **each** turn, scan body for `\| GP:` inside `[`…`]` before final footer | **None** in body region | [ ] |
| 5 | If GM prose mentions a gold amount in flavor, compare to footer | Footer still shows **sheet gold** from engine (flavor may differ; footer wins) | [ ] |

**Failure signals:** Any turn with 2+ bracket lines; footer GP ≠ sidebar; visible LLM bracket with wrong GP **in footer region**.

**Note:** Session `2026-05-22` bug was LLM `GP: 61` while engine differed — TC-5 step 3 catches recurrence even when LLM omits brackets.

---

### TC-6: Combat — `Turn:` segment + stripped LLM bracket (maps to F3 / `test_combat_turn_compose_wrong_gp`)

**Goal:** Combat narration uses combat footer shape; wrong LLM GP in returned prose does not appear in footer.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | In dungeon (`32-C-UG-1` or deeper), provoke combat (explore until encounter, or **`I attack the nearest threat.`** if monsters present) | Combat starts; phase/combat HUD active | [ ] |
| 2 | Submit one combat action (e.g. **`attack with sword`**) | GM narrates action; no traceback | [ ] |
| 3 | Read footer | Includes **`Turn:`** segment before `Awaiting:`; `Awaiting: COMBAT_TURN` (or current engine awaiting) | [ ] |
| 4 | Footer GP vs sidebar | **Match**; no `GP: 999`-style invented value in footer | [ ] |
| 5 | Count `[Location:` in combat narration | **Exactly 1** | [ ] |
| 6 | Body prose | Combat flavor present; **no** duplicate bracket status block in body | [ ] |

**Failure signals:** Combat turn with no footer; missing `Turn:`; duplicate brackets; footer GP ≠ sidebar.

**Out of scope note:** Prefix-only `[Mechanics failed — …]` combat tool-fail paths may omit footer per spec — **not** a failure if combat HUD still shows turn state (IMPL-NOTE-004). This TC targets **successful LLM combat narration** path.

**Skip if:** Cannot reach combat in session — note skip; TC-3/TC-5 still required minimum.

---

### TC-7: Meta leak strip — no Campaign Memory banner (maps to F5)

**Goal:** LLM meta narration (`**Campaign Memory Updated:**`, `---` banners) never appears player-facing.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | During TC-3/TC-5 play, include a turn that may trigger memory (quest accept, NPC fact, **`I agree to the contract.`**) | GM responds | [ ] |
| 2 | Scan full narration text | **No** `Campaign Memory Updated` string | [ ] |
| 3 | Scan for trailing `---` followed by empty/meta-only lines | **None** after scene prose | [ ] |
| 4 | Footer still present | Single code footer at bottom | [ ] |

**Failure signals:** Visible memory-update banner; bracket-only meta turn.

---

### TC-8: APP-024 regression — refusal line + code footer (maps to `test_compose_app024_refusal_plus_footer`)

**Goal:** Surface site-entry gate still strips fiction but **appends** exploration footer (not bracket-only).

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Return party to surface **`32-C`** if in dungeon (exit dungeon / extract) | At Breley hub, not in site mode | [ ] |
| 2 | Without successful entry tool, type interior fiction (e.g. **`I step into the torchlit crypt and explore the corridors.`**) | GM responds | [ ] |
| 3 | Read narration body | Contains APP-024 **refusal** line (code-owned: cannot enter site without `enter_dungeon` / entry tool — exact copy may vary slightly) | [ ] |
| 4 | Read footer | **Single** `[Location: 32-C | …]` code footer present | [ ] |
| 5 | Confirm turn is **not** bracket-only | Refusal prose **plus** footer — not footer alone | [ ] |

**Failure signals:** Interior fiction passes gate; **no** footer on refusal turn; **two** bracket lines; footer-only turn with no refusal prose.

**Probabilistic:** LLM may call entry tool instead — retry step 2 with clearer no-entry phrasing, or skip if already verified by pytest TC-2.

---

### TC-9: Mechanics failed + content — footer still appended (maps to F7 / APP-028 sibling — optional)

**Goal:** `[Mechanics failed — …]` prefix turns with LLM content still get exploration footer on exploration path.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At surface **`32-C`**, attempt invalid travel (e.g. **`travel to silversea cove`**) | GM responds with failure | [ ] |
| 2 | Read narration | May include `[Mechanics failed — …]` prefix | [ ] |
| 3 | Read end of message | **Code footer present** with party still at **`32-C`** | [ ] |
| 4 | Footer GP vs sidebar | Match | [ ] |

**Failure signals:** Failure turn with no footer on exploration path (when some GM content returned).

**Skip if:** LLM handles failure entirely in code path with no content — pytest covers compose; note skip.

---

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket | Exploration footer code-owned from engine | TC-3, TC-5 | [ ] |
| Ticket | Combat footer with `Turn:` | TC-6 | [ ] |
| Ticket | Wrong GP in LLM prose stripped; engine GP in footer only | TC-3, TC-5, TC-6 | [ ] |
| Ticket | Meta leak strip | TC-7 | [ ] |
| Ticket | Empty/refusal still has footer | TC-8 | [ ] |
| APP-024 | Refusal + footer, not bracket-only | TC-8 | [ ] |
| APP-073 | Creation status strip unchanged | TC-1 step 3 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **Minimum manual bar:** TC-1 + TC-2 + **TC-3** + **TC-5** required before marking table-verified; TC-4, TC-6, TC-7 recommended; TC-8/TC-9 optional if pytest green.
- **APP-065:** Suggestion chips use engine `awaiting` — footer fix reduces stale tokens in narration but chip source is separate; chip labels should remain human phrases.
- **APP-041 / TTS:** Display footer is authoritative; TTS may strip brackets at speak time — not a failure if spoken text omits footer but panel shows it.
- **APP-083 Phase 2:** TurnTruth verify before compose not in scope; strip + footer remain defense-in-depth.
- **Gold in transit:** If `gold_in_transit > 0`, footer may show `GP: {n} (+{m} transit)` — compare base `{n}` to sidebar sheet gold; transit suffix is expected.
- **Creation path:** Creation footer (`format_creation_status`) unchanged — do not expect full exploration footer during Registry creation steps.
