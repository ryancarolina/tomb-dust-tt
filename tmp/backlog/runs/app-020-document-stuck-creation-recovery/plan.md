# Dev Plan: APP-020 — Document stuck-creation recovery

**Status:** plan (Dev phase)  
**backlog_ticket:** APP-020  
**run-folder:** `tmp/backlog/runs/app-020-document-stuck-creation-recovery/`  
**domain_spec:** `tmp/app-session-persistence-spec.md` § Stuck creation recovery — player documentation (APP-020)  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Summary

Documentation-only chore. Update **`app/README.md`** only: correct stale Quick Start / Features persistence copy (APP-064), add a **Stuck during character creation?** subsection with **`new game`** recovery, and document the **`new game`** command (aliases, wipe warning, finished-save vs partial-creation contrast). No code, pytest, or domain-spec edits in impl phase — domain checklist + changelog on ticket close per ticket spec-sync.

---

## Scope

| In scope | Out of scope |
|----------|--------------|
| `app/README.md` prose (ticket Expected files) | `app/gm/orchestrator.py`, `app/ui/app.py`, tests |
| R-020a–g checklist (domain § APP-020) | Hand-edit / CLI recovery instructions |
| Align README with existing behavior | Implied behavior changes |

**QA non-blocking (plan):** Do **not** tell players they **must** type **`new game`** after every mid-creation quit. APP-018 G3a restores the creation desk on the first non–`new game` turn when autosave + gate pass. Scope here is **stuck** recovery; optional one-line “if the clerk desk resumes normally, keep playing” is acceptable (R-020 does not require it).

---

## Root cause (doc gap)

| Location | Current copy | Problem |
|----------|--------------|---------|
| `app/README.md` L15 | "The app auto-resumes if `session_state.json` or a workspace save exists" | Boot never reads `session_state.json` (APP-064). Partial creation → **`new game`** chip only. |
| `app/README.md` L59 | "auto-saves every 60s, restores on relaunch" | Autosave exists; **restore** requires **`load game`** + engine save (slotted living character), not implicit boot. |
| (missing) | No stuck-recovery section | Engineering path exists (`setup_new_game`) but players are not told. |

Behavior source (unchanged — reference only):

```128:146:app/ui/app.py
                has_save = self._orchestrator.bridge.has_save()
                ...
                if has_save:
                    ...
                    self._ui_queue.put(("suggestions", ["load game", "new game"]))
                else:
                    ...
                    self._ui_queue.put(("suggestions", ["new game"]))
```

```665:683:app/gm/orchestrator.py
    def setup_new_game(self, campaign_slug: str = "salt-road") -> dict:
        self._reset_creation_for_new_game()
        self._clear_creation_block_on_disk()
        ...
        self._delete_save_file()
        return session
```

---

## Deep code-path traces

### A. Application boot → startup prompt (APP-064)

| Step | Location | Action |
|------|----------|--------|
| A1 | `app/main.py` | `App(config).run()` |
| A2 | `app/ui/app.py:49` | `_init_orchestrator()` (daemon thread) |
| A3 | `app/ui/app.py:124-126` | `Orchestrator(config)` → `get_status()` |
| A4 | `app/ui/app.py:128` | `has_save = bridge.has_save()` |
| A5 | `app/gm/bridge.py:395-397` | `has_save_session(conn)` |
| A6 | `play/tomb_gm/domain/session.py:116-137` | `find_save_campaign` — slotted **alive** character required |
| A7 | `app/ui/app.py:137-146` | `has_save` true → "You have a saved game." + `load game` chip; else → **`new game`** only |

**Partial creation at relaunch:** open session + empty roster → A6 **false** → A7 else branch. Presence of `app/session_state.json` does **not** affect A4–A7. README must state this.

**Finished save at relaunch:** slotted living character → A6 true → load + new chips.

### B. Autosave write (context for “partial” vs “finished”)

| Step | Location | Action |
|------|----------|--------|
| B1 | `app/ui/app.py:216-220` | `_autosave` every 60s |
| B2 | `app/ui/app.py:387-428` | `_save_session()` writes `session_state.json`: narration, `creation_state`, `engine_status` |
| B3 | Escape quit | `_save_session()` on exit |

Autosave **does not** create an engine “finished save.” Engine resumability = `find_save_campaign` (roster with slotted alive character).

### C. Mid-creation continue after relaunch (APP-018 — do not over-wipe in README)

| Step | Location | Action |
|------|----------|--------|
| C1 | Relaunch | Boot path A — **`new game`** chip; orchestrator not yet restored |
| C2 | Player types clerk input (not `new game`) | `process_turn` |
| C3 | `app/gm/orchestrator.py:833-834` | `_restore_creation_from_session_state()` before other branches |
| C4 | `orchestrator.py:547-571` | `_creation_restore_gate` (G1): saved/live `CHARACTER_CREATION`, empty roster, active `creation_state` with valid step |
| C5 | `orchestrator.py:590-594` | `import_creation_state` — desk resumes at saved step |
| C6 | `_creation_turn(...)` | Normal creation flow continues |

**Player doc implication:** Quit mid-desk → relaunch → type a normal clerk answer → desk may resume. **`new game`** is for **stuck** states (wrong step, blank GM, setup failure), not mandatory reset after every quit.

### D. Failed `load game` during partial creation (APP-071 variant B)

| Step | Location | Action |
|------|----------|--------|
| D1 | `process_turn("load game")` | `session_resume()` |
| D2 | `play/tomb_gm/domain/session.py:220-222` | No `find_save_campaign` → `ok: false` |
| D3 | `orchestrator.py:840-842` | `_restore_creation_from_session_state()` then `_resume_failure_message` |
| D4 | `orchestrator.py:645-656` | Variant B: no finished save; mentions current step; **continue desk OR `new game`** (wipe) |
| D5 | `app/ui/app.py:197-198` | UI may also `_load_session()` — replays narration only; FSM truth in orchestrator |

README: steer partial-creation players away from expecting **`load game`**; if they try it, in-app copy already explains — README should not contradict variant B “keep answering” path.

### E. Recovery: `new game` (canonical reset)

| Step | Location | Action |
|------|----------|--------|
| E1 | `app/ui/app.py:283+` | Submit `new game` / `start` / `new` |
| E2 | `orchestrator.py:824-831` | `setup_new_game()`; on failure → `_setup_new_game_failure_message` + retry hint (APP-019) |
| E3 | `orchestrator.py:667-668` | `_reset_creation_for_new_game()` + `_clear_creation_block_on_disk()` **before** wipe |
| E4 | `orchestrator.py:669-679` | `end_session` → `wipe_all_data` → `init` → `campaign_new` → `session_start` |
| E5 | `orchestrator.py:681-682` | Fresh `CreationState(step="NAME")`; `_delete_save_file()` |
| E6 | `orchestrator.py:831` | `_creation_turn` — NAME clerk prompt |
| E7 | `app/ui/app.py` `finally` | `_save_session()` — fresh autosave |

**In-session reset (no relaunch):** Same E1–E7; UI clears narration queue on submit. Prior partial progress lost.

**Data loss (document plainly):** in-progress creation fields + current campaign session tables wiped; world corpses persist per domain spec.

### F. Finished save resume (contrast for README)

| Step | Location | Action |
|------|----------|--------|
| F1 | Boot | A7 `has_save` true |
| F2 | `load game` | `session_resume()` ok |
| F3 | `orchestrator.py:868-879` | Restore history + creation sync; delve/combat/creation branches |

README **`load game`** = finished saves only (living character on roster).

### G. What is NOT player recovery (forbidden in README)

| Path | Why omit |
|------|----------|
| Edit `session_state.json` / `play/workspace/` | AGENTS.md / active rule |
| `python -m tomb_gm` / `@tomb-gm` | Obsolete for players (README L3 already) |
| Expect boot auto-restore from app autosave | Contradicts APP-064 |

---

## Implementation steps (README only)

**File:** `app/README.md` — sole Expected file.

### Step 1 — Fix Quick Start (R-020d)

**Replace** L15 sentence after the `python main.py` block.

**Remove:** "The app auto-resumes if `session_state.json` or a workspace save exists."

**Add (substance):**

- Type **`new game`** to start character creation.
- If you previously **finished** creation and have a living character saved, relaunch offers **`load game`** — use that to continue.
- If creation feels stuck, see **Stuck during character creation?** below.

Keep command in backticks. Do not claim boot reads `session_state.json`.

### Step 2 — New subsection: **Stuck during character creation?** (R-020a–c, R-020f)

**Placement:** Immediately after Quick Start (before Requirements). Pin heading **`## Stuck during character creation?`** for T-020a consistency.

**Suggested structure:**

1. **When to use this** — creation feels broken, not a normal quit-and-continue.
2. **Symptoms** (≥2, R-020b):
   - Relaunch after mid-creation quit shows only **`new game`**, but you expected autosave to restore a finished character.
   - Repeated clerk prompts, blank GM text, or footer stuck on the wrong step.
   - Setup error or `[Awaiting: new game]` after a failed reset.
   - **`load game`** says there is no finished save yet (partial creation).
3. **Try once first (R-020 domain § When to retry first):** transient LLM glitch on one desk input — retry that answer once before wiping.
4. **Recovery:** type **`new game`** in the input box (also accepts **`start`** or **`new`**).
5. **Wipe warning (R-020c):** resets in-progress creation (name, race, rolls, choices) and the current campaign session; cannot be undone. Account stash / world corpses behavior: keep brief — “starts a fresh campaign session.”
6. **Partial vs finished (R-020f):**
   - **Partial creation** (no living character on roster yet): boot shows **`new game`** only; reset with **`new game`** when stuck. After relaunch, if the clerk desk resumes when you keep answering, continue — you do **not** need **`new game`** unless stuck (APP-018; QA non-blocking nuance).
   - **Finished save:** relaunch shows **`load game`**; use that to resume exploration.
7. **Do not:** edit save files by hand; use developer CLI tools.

Cross-link from Quick Start (Step 1).

### Step 3 — Document **`new game`** command (ticket AC + D3)

Add under Stuck subsection or a short **`### Commands`** bullet under Quick Start:

| Command | When | Effect |
|---------|------|--------|
| **`new game`** (`start`, `new`) | New campaign or stuck creation reset | Fresh NAME desk; wipes in-progress creation + session data on success |
| **`load game`** (`continue`, `load`, `resume`) | Relaunch with finished save | Restores slotted living character run |

If setup fails, retry **`new game`** once; persistent failure → quit and relaunch (APP-019 — one line, no error catalog).

### Step 4 — Fix Features persistence bullet (R-020e)

**Replace** L59:

- **From:** `Session persistence — auto-saves every 60s, restores on relaunch`
- **To (substance):** `Session persistence — auto-saves every 60s and on quit; **finished** saves resume when you type **load game** at relaunch (not automatic from app autosave alone)`

Keep “60s” and Escape quit alignment with Controls table L71.

### Step 5 — Self-review against R-020a–g

| ID | Verify |
|----|--------|
| R-020a | Subsection + **`new game`** recovery |
| R-020b | ≥2 symptoms |
| R-020c | Wipe warning |
| R-020d | Quick Start fixed |
| R-020e | Features bullet qualified |
| R-020f | **`load game`** = finished saves only |
| R-020g | No hand-edit / CLI recovery |

---

## Test plan

| ID | Action | Expected |
|----|--------|----------|
| T-020a | Checklist grep/review `app/README.md` vs R-020a–g | All pass |
| T-020b | Manual APP-014 TC-1: partial creation → Escape quit → relaunch → follow README | Types **`new game`** → NAME desk |

No pytest. Optional cross-check commands (behavior already covered elsewhere):

```bash
python -m pytest app/tests -q -k "setup_new_game or creation_block or session_resume or creation_restore"
```

---

## Close checklist (not impl — ticket release)

- [ ] `app/README.md` merged per steps 1–4
- [ ] T-020a pass
- [ ] Domain spec: mark APP-020 checklist `[x]` + changelog entry
- [ ] Ticket `release APP-020 --done`
- [ ] `app-master-spec.md` priority table unchanged (doc-only)

---

## Files touched (impl)

| File | Action |
|------|--------|
| `app/README.md` | Edit Quick Start, add Stuck section, fix Features |

**Must ⊆ ticket Expected files.** Domain spec sync on close only.

---

## Risk notes

| Risk | Mitigation |
|------|------------|
| Overstate “always `new game` after quit” | Include APP-018 continue path (Step 2 §6) |
| Understate wipe | Plain data-loss sentence in Stuck section |
| Contradict APP-071 variant B | Allow “keep answering clerk” when not stuck |
| Duplicate APP-019 error table | One-line retry hint only |
