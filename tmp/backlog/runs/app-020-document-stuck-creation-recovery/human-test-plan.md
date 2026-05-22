# Human Playtest Plan: APP-020-document-stuck-creation-recovery

**backlog_ticket:** APP-020  
**Commit:** `1b45332`  
**Play entry:** `cd app && python main.py` — **optional** for this doc-only ticket; see [app/README.md](../../../app/README.md)

**Scope note:** APP-020 adds player-facing stuck-creation recovery documentation in `app/README.md` only — no orchestrator or UI code changes. **Primary gate:** read and verify README prose against domain spec § APP-020 (R-020a–g). **Optional gate:** reproduce partial-creation stuck state and confirm README-only recovery steps work (T-020b / cross-check APP-014 TC-1).

## Prerequisites

### Doc verification (required — no app launch)

- [ ] Open [app/README.md](../../../app/README.md) at commit `1b45332` (or later if README unchanged)
- [ ] Optional cross-check: [tmp/app-session-persistence-spec.md](../../../app-session-persistence-spec.md) § **Stuck creation recovery — player documentation (APP-020)**

### Optional PyGame repro (T-020b)

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=sk-or-v1-...`)
- [ ] Known workspace: `play/workspace/` (engine SQLite); app autosave at `app/session_state.json`
- [ ] For optional TC-3: start from **partial creation** (see setup below) — empty engine roster, active session, optional app autosave
- [ ] Optional log tail: `app/logs/session-YYYY-MM-DD.jsonl`

### Partial-creation setup (reuse for optional TC-3)

1. Launch app → type **`new game`** → submit a delver name → advance at least one clerk step (race/class prompt visible).
2. Press **Escape** to save and quit.
3. Relaunch — startup should **not** say "You have a saved game"; suggestion chip **`new game`** only (APP-064 path).

## Test cases

### TC-1: README stuck-recovery section (maps to ticket AC / R-020a–c / D1–D3)

**Goal:** A player reading only the README can identify when creation is stuck and that **`new game`** is the recovery action, with a clear data-loss warning.

| Step | Action (read `app/README.md`) | Expected result | Pass |
|------|-------------------------------|-----------------|------|
| 1 | Find **Quick Start** (≈ L15) | Mentions **`load game`** for **finished** saves; links or points to stuck section when creation feels stuck | [ ] |
| 2 | Open **`## Stuck during character creation?`** (≈ L17) | Dedicated subsection exists | [ ] |
| 3 | Read **Common symptoms** (≈ L21–26) | At least **two** recognizable stuck cases (e.g. relaunch shows only **`new game`**, repeated/blank/wrong-step prompts, setup error footer, partial **`load game`** failure) | [ ] |
| 4 | Read **Try once first** (≈ L28) | Suggests retrying one clerk input before wipe (transient LLM glitch) | [ ] |
| 5 | Read **Recovery** (≈ L30) | **`new game`** is the canonical recovery; aliases **`start`** / **`new`** mentioned; **wipe warning** — in-progress creation + campaign session lost, **cannot be undone** | [ ] |
| 6 | Read **Do not** (≈ L46) | Forbids hand-editing saves and developer CLI / `@tomb-gm` — does **not** instruct players to use them | [ ] |

**Failure signals:** No stuck subsection; recovery command missing or buried; no wipe warning; README tells players to edit `session_state.json` or run `python -m tomb_gm`.

### TC-2: Partial vs finished save + command table (maps to R-020d–f / D4–D6)

**Goal:** README distinguishes boot behavior for partial creation vs finished saves and does not claim boot auto-restore from app autosave alone.

| Step | Action (read `app/README.md`) | Expected result | Pass |
|------|-------------------------------|-----------------|------|
| 1 | Read **Partial vs finished saves** (≈ L32–35) | **Partial:** relaunch → **`new game`** only; use **`new game`** when stuck; desk may resume if clerk continues normally. **Finished:** relaunch → **`load game`** | [ ] |
| 2 | Read **Commands** table (≈ L37–42) | **`new game`** row: fresh NAME desk, wipes in-progress creation. **`load game`** row: only when relaunch with **finished** save | [ ] |
| 3 | Grep README for `auto-resumes` | **Zero** matches | [ ] |
| 4 | Grep README for `session_state.json` | **Zero** matches (no implied boot restore from app file alone) | [ ] |
| 5 | Read **Features → Session persistence** (≈ L90) | Autosave on interval/quit qualified; **finished** saves resume when player types **`load game`** at relaunch — **not** implicit boot restore | [ ] |
| 6 | Read **Quick Start** again (≈ L15) | No claim that relaunch auto-restores from autosave alone | [ ] |

**Failure signals:** Unqualified "restores on relaunch"; **`load game`** described as restoring partial creation; Quick Start still says auto-resume when only app save exists.

### TC-3: Optional — player follows README only through stuck reset (maps to T-020b / APP-014 TC-1)

**Goal:** Partial creation after quit/relaunch matches README expectations; typing **`new game`** per README reaches a clean NAME desk.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Complete **Partial-creation setup**; relaunch if needed | Title narration; chip **`new game`** only; **no** "You have a saved game" | [ ] |
| 2 | **Without** reading specs — follow README stuck section only | Tester confirms README led them to type **`new game`** (not **`load game`**, not hand-editing files) | [ ] |
| 3 | Click **`new game`** chip or type `new game` and submit | GM asks for delver name (NAME desk); stale mid-creation narration cleared | [ ] |
| 4 | Check footer / status | `[Awaiting: NAME_INPUT]` (or equivalent NAME label); **not** stuck on prior RACE/SKILLS step | [ ] |
| 5 | Inspect narration | **No** `Could not start game` on success path (APP-019 retry hint in README applies only on failure) | [ ] |

**Failure signals:** README misleads player to **`load game`** or file edits; **`new game`** fails with setup error; footer stuck on old creation step.

**Skip note:** Doc-only sign-off may pass on TC-1 + TC-2 alone; run TC-3 when validating T-020b or before closing a batch that depends on player recovery UX.

### TC-4: Optional — finished-save path still correct (maps to non-regression / R-020f)

**Goal:** README still correctly describes **`load game`** for living slotted characters after APP-020 edits.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Read README **Partial vs finished saves** + command table | **`load game`** scoped to finished save only | [ ] |
| 2 | Optional in-game: finish creation → Escape quit → relaunch | "You have a saved game" + chips **`load game`** and **`new game`** | [ ] |
| 3 | Optional: type **`load game`** | Run resumes with roster populated; not sent to NAME-only desk | [ ] |

**Failure signals:** README says partial creation can **`load game`**; in-game startup hides saved-game prompt after finalize.

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket AC | `app/README.md` documents stuck creation → type **`new game`** | TC-1 steps 2–5 | [ ] |
| R-020a | Dedicated stuck subsection | TC-1 step 2 | [ ] |
| R-020b | ≥2 stuck symptoms | TC-1 step 3 | [ ] |
| R-020c | Wipe warning | TC-1 step 5 | [ ] |
| R-020d | Quick Start corrected | TC-2 steps 1, 6 | [ ] |
| R-020e | Features persistence qualified | TC-2 step 5 | [ ] |
| R-020f | **`load game`** for finished saves only | TC-2 steps 1–2; TC-4 | [ ] |
| R-020g | No hand-edit / CLI recovery | TC-1 step 6 | [ ] |
| T-020b | Manual README-only recovery (optional) | TC-3 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all required TC pass / issues: … |

**Minimum pass:** TC-1 + TC-2 all steps checked. Optional TC-3/TC-4 recommended before batch close if any APP-064/014/071 behavior was recently touched.

## Notes for next ticket

- **APP-018:** Mid-creation desk may resume on relaunch when the clerk continues normally — README L19/L34 says **`new game`** is **not** required unless something is wrong; do not fail TC-3 if resume works and README "when not stuck" guidance matches.
- **APP-019:** If **`new game`** fails, README L44 says retry once then relaunch — separate from TC-3 success path.
- **APP-071:** Partial creation → **`load game`** should show no finished save (variant A/B in-app); README symptom bullet covers this — optional repro if TC-3 passes but load failure copy feels inconsistent.
- **Out of scope:** Full Dumpy golden path (APP-057); pytest (no automated README tests per spec).
