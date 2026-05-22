# Human Playtest Plan: APP-060-auto-scroll-narration

**backlog_ticket:** APP-060  
**Commit:** pending (Stage 7 — use latest commit with APP-060 in message)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope:** After player submit or GM reply, the narration panel must **pin to the bottom** so the latest line — including wrapped prose and markdown **tables** — is visible without manual wheel scroll. Fix is layout-correct: tail pin runs in `draw()` **after** `_rebuild()`. Automated pytest passed at impl QA (`test_narration_scroll.py`, 6 tests). This plan validates the bug repro (creation tables), long replies, wheel history, error tail, and startup batch lines in the live PyGame client.

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=…`) — valid for TC-2–TC-4, TC-6; invalid key optional for TC-5
- [ ] Fresh session for table repro: type **`new game`** (do not Continue from mid-creation save for TC-2)
- [ ] Window at default or typical size so narration panel height is unchanged mid-TC
- [ ] Mouse with wheel (or trackpad scroll) for TC-4
- [ ] Optional log watch: `app/logs/session-YYYY-MM-DD.jsonl`
- [ ] Repo root cwd for TC-1 pytest gate

## What to look for (all TCs)

| Bad (fail — pre-fix bug) | Good (pass — APP-060) |
|--------------------------|------------------------|
| After submit, **You** line or latest GM table rows sit **below** the visible area; must wheel down to read | Latest **You** / **GM** / error line visible immediately after turn completes — no wheel needed |
| Tall stats/skills table: viewport stuck mid-table; bottom rows (e.g. last attribute, LUC, footer) clipped | Table **footer rows** and any lines after the table visible at bottom of narration panel |
| Scrollbar thumb near **top** after fresh GM reply when history is long | Scrollbar thumb near **bottom** after player/GM/error append |
| `[Error: …]` appended but off-screen | Error line visible at bottom without scrolling |
| Wheel scroll broken or narration frozen | Wheel still scrolls history between turns; scrollbar thumb moves |

**Visual cues:** Player lines labeled **You** (distinct color); GM lines labeled **GM**. Scrollbar appears on the right when content exceeds panel height.

---

## Test cases

### TC-1: Automated regression gate (recommended before manual play)

**Goal:** Confirm narration scroll unit tests and map-creation regression still green.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_narration_scroll.py -q` | Exit code **0**; **6 passed** | [ ] |
| 2 | From repo root: `python -m pytest app/tests/test_ui_map_creation_gate.py -q` | Exit code **0**; **10 passed** | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

---

### TC-2: Creation tall table — submit pins player + GM tail (maps to ticket AC + spec R2)

**Goal:** Reproduce the primary bug: after name/race chain, code-owned **stats/class table** exceeds viewport; submit a choice and confirm **You** line plus GM table tail are visible without wheel.

**Reach table:** `new game` → name (e.g. `ScrollTest`) → race (`human`) → stop when narration shows a **markdown attribute table** (STR/DEX/… rows) and/or class table.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | Type `new game` and submit | GM prompts for name; creation active | [ ] |
| 3 | Submit name, then `human` for race | Stats roll table appears (multi-row `\| Stat \|` or attribute block); content taller than narration viewport | [ ] |
| 4 | **Before submitting next choice:** if table bottom rows are already clipped, note it — after next submit they must not stay clipped | Baseline: long table may fill panel (OK if TC-5 step 4 passes after submit) | [ ] |
| 5 | Submit a valid class choice (e.g. `apprentice` or option shown in table) | **You** line with your submit text appears in narration | [ ] |
| 6 | Immediately after GM response lands (processing indicator clears) | **Without using the wheel**, bottom of narration shows: your **You** line **and** the latest GM content (table footer / next-step prose / status) — not stuck mid-table | [ ] |
| 7 | Check scrollbar thumb position | Thumb at or near **bottom** of track (not stuck at top/middle) | [ ] |

**Failure signals:** Must wheel to see **You** line after submit; stats table bottom rows permanently below fold after GM reply; crash on creation submit.

---

### TC-3: Long multi-paragraph GM reply (maps to ticket AC + spec R2)

**Goal:** After delver play begins, a verbose GM reply still pins tail — wrapped prose, not only tables.

**Setup:** Complete creation through finalize **or** use an existing save at **Phase: preparation** / free exploration. Fast path: eight-input APP-057 chain if familiar (`Dumpy` → `human` → `apprentice` → skills/spells → `yes`).

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Arrive at post-finalize play (world intro done, not in creation) | Narration has prior history; chip row may be empty | [ ] |
| 2 | Submit a prompt likely to yield several sentences, e.g. `Describe the registry hall and everyone present in detail` | Turn processes | [ ] |
| 3 | When GM response completes | **Without wheel**, last paragraph(s) of GM reply visible at bottom of panel | [ ] |
| 4 | Submit a short follow-up (e.g. `thanks`) | **You** line visible at bottom; prior long reply still reachable via wheel up | [ ] |

**Failure signals:** GM reply tail below viewport; only first paragraph visible while later paragraphs require scroll down.

---

### TC-4: Wheel history + always-follow on new submit (maps to ticket AC + spec R3)

**Goal:** Manual scroll up works between turns; **next** player submit returns view to bottom (always-follow policy).

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Continuing from TC-2 or TC-3 with **long narration history** | Scrollbar visible | [ ] |
| 2 | Hover mouse over **narration panel** (left/main text area) | Panel has focus for wheel | [ ] |
| 3 | Scroll **up** several wheel notches | Older lines (welcome, early creation) visible; scrollbar thumb moves **up** | [ ] |
| 4 | Read mid-history content | View stays where you scrolled — no auto-jump yet | [ ] |
| 5 | Type any valid command and submit (e.g. `look around` or next creation choice) | View **jumps to bottom**; new **You** line visible without wheel | [ ] |
| 6 | Wait for GM reply | Latest GM text visible at bottom without wheel | [ ] |

**Failure signals:** Cannot scroll up; wheel does nothing; after submit view stays mid-history; thumb does not move on wheel.

---

### TC-5: Error line pinned at bottom (maps to ticket AC + spec R2 error path)

**Goal:** `[Error: …]` narrator line follows tail — previously missing scroll on `error` queue handler.

**Option A — invalid API key (no code edit):**

1. Stop the app.
2. Temporarily set `OPENROUTER_API_KEY=invalid` in `app/.env` (note original value).
3. Relaunch `cd app && python main.py`, type `new game`, submit a name.
4. Expect turn/init failure with `[Error: …]` in narration.

**Option B — dev inject (revert after test):** First line of `Orchestrator.process_turn` (TEMP):

```python
raise RuntimeError("APP-060 scroll QA inject")
```

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Provoke failure via Option A or B | Turn fails; narration shows line starting with **`[Error:`** (GM voice) | [ ] |
| 2 | Without using wheel | Full error line visible at bottom of narration panel | [ ] |
| 3 | Scrollbar thumb | Near **bottom** of track | [ ] |
| 4 | Restore valid API key / remove inject; relaunch if needed | App usable again | [ ] |

**Failure signals:** Error only in terminal, not narration; error line off-screen; must wheel to read `[Error: …]`.

---

### TC-6: Startup batch narration ends at bottom (maps to spec R2 batch / welcome copy)

**Goal:** Initial `narration` batch lines (welcome + setup hints) pin to tail on first `draw()` — no manual scroll on fresh launch.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Ensure no stale session confusion: fresh launch `cd app && python main.py` | Welcome / setup copy appears in narration | [ ] |
| 2 | Without scrolling | Latest welcome line (or bottom of startup text) visible at panel bottom | [ ] |
| 3 | Optional: resize window wider/taller once | Content reflows — **no re-pin required** on resize alone (out of scope); note behavior only, not a failure unless crash | [ ] |

**Failure signals:** Startup text clipped with thumb at top; must wheel to read “type new game” hint at bottom.

---

## Out of scope (not failures here)

| Item | Expected behavior |
|------|-------------------|
| **Session Continue / load** | Resumed narration may not auto-pin to bottom (`_load_session` sets `_dirty` only) |
| **Window resize alone** | No automatic re-pin when only geometry changes |
| **Animated smooth scroll** | Instant pin — no scroll animation |
| **Near-bottom-only policy** | v1 **always** follows tail on new player/GM/error — scrolling up then submitting **will** jump to bottom (TC-4 step 5) |

---

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket | Player submit pins **You** line visible | TC-2 step 6, TC-4 step 5 | [ ] |
| Ticket | GM response shows full new content (tables, paragraphs) | TC-2, TC-3 | [ ] |
| Ticket | Layout-correct pin after rebuild | TC-2, TC-3 (visual) + TC-1 (unit) | [ ] |
| Ticket | Long creation tables without manual wheel | TC-2 | [ ] |
| Ticket | Manual scroll up works; new content returns bottom | TC-4 | [ ] |
| Ticket | Error path pinned | TC-5 | [ ] |
| R2 | Startup `narration` batch at bottom | TC-6 | [ ] |
| R3 | Always-follow policy on queue append | TC-4 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **APP-059:** Table column layout may differ; pass/fail is **scroll position**, not exact column count.
- **APP-036:** Creation step badge in stats panel is unrelated — ignore for scroll TCs.
- **APP-073:** Internal `Awaiting:` footer in GM text does not affect scroll pin.
- **Batch board:** APP-032/APP-036 may share commits with APP-060 — verify `request_follow_tail()` in `app/ui/app.py` if TC-2 fails after merge.
- If TC-2 fails but TC-1 passes: likely frame-order or missing `request_follow_tail()` on a queue path — compare `player`, `narration`, `narration_text`, `error` handlers.
- If only **error** fails (TC-5): check `error` handler calls `_smooth_scroll_to_bottom()` after `add_line`.
