# Spec: APP-071-friendly-load-no-save

**Status:** draft (PM revision round 2)
**backlog_ticket:** APP-071
**ticket_path:** tmp/backlog/app-071-friendly-load-game-when-no-save.md
**domain_spec:** tmp/app-session-persistence-spec.md
**registry_gap:** false
**Domain specs touched:** tmp/app-session-persistence-spec.md

## Problem

When a player types `load game` (or `load` / `continue` / `resume`) and the engine has no resumable save (`has_save_session()` false), `Orchestrator.process_turn` logs a JSONL `error` with context `session_resume` but does **not** emit `gm_narration`. The return string is engine-centric (`no save session found`) and offers no creation-step context. Mid-creation players (open session, empty roster, `creation.active`) hit this branch **before** the creation FSM guard and get generic recovery copy. Session evidence (Supa, 2026-05-20) shows log-only failures with no actionable narration in the panel.

## Goals

- Every failed `session_resume` returns **player-facing** narration in the panel (not log-only).
- Copy distinguishes **no save on disk** vs **unsaved in-progress character creation**.
- JSONL retains `error` for QA; same text also appears as `gm_narration` via a **drift-safe** recovery emit (not raw `_emit_narration` on mid-creation paths).
- Suggestion chips offer obvious next actions without spurious `creation_drift` (`awaiting_mismatch`).

## Non-goals

- **APP-064:** Startup “You have a saved game” prompt gating (`has_save` only) — separate ticket.
- **APP-019:** Toast / dedicated UI error channel for `new game` failures — see § R4 and ticket scope note; APP-071 is narration + JSONL only.
- Reordering or skipping `App._load_session()` on failed resume (UI may still restore `session_state.json`; creation state preserved — document only).
- Changing engine `resume_session` / `find_save_campaign` eligibility rules.
- `log_player_message` helper (does not exist; use recovery emit + `log_gm_narration` per logging spec).

## Requirements

### R0: Message variant selection (order matters)

**When:** `session_resume` returns `ok: false`.

**Decision tree (evaluate in order; first match wins):**

1. **Variant B (mid-creation, R3)** if **any** of:
   - `self.creation.active` is true, or
   - `self.creation.step` is set beyond default and `SAVE_PATH` / exported creation state indicates in-progress desk work, or
   - `bridge.status()` reports `awaiting == CHARACTER_CREATION` with empty `roster`.
2. **Variant A (cold / no save, R2)** otherwise.

**Acceptance criteria**

- [ ] Implementation never chooses cold-path copy while any R3 signal is true (including engine-only `CHARACTER_CREATION` + empty roster when `creation.active` is false).
- [ ] Desync cases (engine mid-creation, app `creation.active` false) still get variant B when engine signal matches.

### R1: Failed resume always surfaces narration (drift-safe JSONL)

**Trigger:** `process_turn` input normalized to one of `continue`, `resume`, `load`, `load game`, and `bridge.session_resume()` returns `ok: false`.

**Emit pattern:** Add orchestrator helper **`_emit_recovery_narration(message)`** (name may vary) that:

- Appends to narration history and calls **`log_gm_narration(message)`** (same text as UI return).
- Does **not** call `_check_creation_drift` / `log_creation_drift` (recovery copy is out-of-band from desk FSM footers per [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) § `creation_drift` healthy path).

**Do not** use `_emit_narration` on resume-failure paths — it always runs `_check_creation_drift` and will log `awaiting_mismatch` when footers use human chip phrases during `_creation_drift_scope()`.

**Acceptance criteria**

- [ ] Return value is non-empty player-facing prose (not empty, not exception-only).
- [ ] Failure path calls `_emit_recovery_narration(message)` so JSONL includes `gm_narration` with the same text shown in the UI.
- [ ] Retain `log_error("session_resume", <engine error>)` unchanged for QA correlation.
- [ ] Do **not** expose raw engine error strings as the primary message; map `no save session found` (and unknown errors) to friendly copy with a retry hint.
- [ ] Mid-creation failure (T2): JSONL has **no** `creation_drift` event with `reasons` containing `awaiting_mismatch` solely from recovery footer wording.

### R2: Message variant A — no resumable save (cold / post-wipe)

**When:** R0 selects variant A.

**Copy (minimum):**

- State clearly that **no saved game** was found.
- Suggest **`new game`** to start fresh.
- Optional one line: autosave / `session_state.json` does not replace an engine roster save.

**Footer for chips:** append a line matching existing suggestion parsing, e.g. `[Awaiting: new game]`.

**Drift rule:** `[Awaiting: new game]` is allowed on variant A because `_creation_drift_scope()` is **false** (no active desk / no engine `CHARACTER_CREATION` + empty roster).

**Acceptance criteria**

- [ ] Narration panel shows the friendly message after `load game` on a workspace with no resumable engine save and no mid-creation signals.
- [ ] JSONL contains both `error` (`context: session_resume`) and `gm_narration` with the friendly text.

### R3: Message variant B — mid-creation in memory

**When:** R0 selects variant B.

**Copy (minimum):**

- State that there is **no finished save** to load (engine needs a living slotted character).
- Name the **current creation step** using `CREATION_STATUS_LABELS[creation.step]` human label or prose derived from `format_creation_status(self.creation)` (e.g. race, stats, class).
- Tell the player to **keep answering prompts** to continue this character, or type **`new game`** to wipe and start over (warn that `new game` clears progress) — **`new game` / `continue creation` must appear in prose only**, not as the bracket `Awaiting:` token.

**Footer for chips:** use code-owned status inside brackets, e.g. `[{format_creation_status(self.creation)}]` → `[Awaiting: RACE_INPUT]` style. **Forbidden:** `[Awaiting: new game]`, `[Awaiting: new game | continue creation]`, or any human phrase that is not `CREATION_STATUS_LABELS[step]` (or step fallback `*_INPUT`).

**Acceptance criteria**

- [ ] After `new game` → name entered → `load game`, message mentions in-progress creation (not only “no save session found”).
- [ ] Message is distinct from R2 variant A copy (creation step or “unsaved creation” called out).
- [ ] Footer `Awaiting:` token matches `format_creation_status(self.creation)` so chips align with desk step without drift telemetry.

### R4: APP-019 alignment (narration-only; ticket traceability)

**Scope split (closes TICKET-001):**

| Ticket | Channel | APP-071 delivers? |
|--------|---------|-------------------|
| **APP-071** | Narration panel + JSONL `gm_narration` + `error` | Yes — resume failure paths |
| **APP-019** | UI toast / dedicated error surface for **`new game`** failures | **No** — remains open; copy tone may align later |

**Acceptance criteria**

- [ ] `setup_new_game` failure path is **unchanged** in APP-071 unless Dev adds recovery emit in the same PR as a drive-by — if so, mirror R1 logging pattern and note in changelog.
- [ ] Ticket AC “extend APP-019 or close together” is satisfied by **narration parity for `load game`**, not by shipping APP-019 toast in APP-071.

### R5: UI scope

**Default:** Orchestrator-only; narration return + footer satisfies chips via `_extract_suggestions`.

**Fallback (only if bracket footers insufficient in manual QA):** queue `("suggestions", ["new game", …])` from UI on resume-failure — requires ticket Expected files update **before** impl; suggestions must not embed conflicting `Awaiting:` tokens in narration body.

**Acceptance criteria**

- [ ] No **required** edits to `app/ui/app.py` for APP-071 close.
- [ ] If chips do not appear in manual QA, Dev may add minimal UI queue per fallback above.

## Test plan

### Automated (add `app/tests/test_session_resume_failure.py` to ticket Expected files before impl)

```bash
# Repo root; isolated workspace per app/tests/conftest.py
python -m pytest app/tests -q -k "session_resume or load_game"
```

| Case | Setup | Action | Assert |
|------|--------|--------|--------|
| T1 | Isolated workspace, no campaign save | `process_turn("load game")` | Variant A copy; `new game` in prose/footer; `log_gm_narration` called |
| T2 | `new game` → name step, no roster | `process_turn("load game")` | Variant B copy; step named; **no** `creation_drift` with `awaiting_mismatch` from recovery emit |
| T3 | T1 | Inspect logger | `log_error` with `session_resume` still invoked |

Use `isolated_workspace` + `mock_openrouter_client`; lazy-import `Orchestrator` inside tests per logging spec import discipline. Monkeypatch `log_creation_drift` in T2 to assert empty drift list.

### Manual smoke

```bash
cd app && python main.py
```

1. Fresh workspace: type `load game` → friendly narration in panel; tail `app/logs/session-*.jsonl` for `error` + `gm_narration` (no spurious `creation_drift` on cold path).
2. `new game` → enter name → `load game` → creation-aware message + step-aligned chips; grep JSONL — no `awaiting_mismatch` drift on recovery line alone.

## Human playtest hints (for Stage 7)

- **TC-A:** Launch with no engine save; submit `load game` — panel shows recovery text, chips include `new game`.
- **TC-B:** Mid-creation (e.g. at race step); `load game` — copy references current step; chips use step label (e.g. `RACE_INPUT`), not generic “continue creation”; player can continue without typing `load` again.
- **TC-C:** Regression — successful resume with real roster still works (`load game` after finalized character).

## Affected paths

- `app/gm/orchestrator.py` — `process_turn` resume failure branch; `_resume_failure_message(...)` + `_emit_recovery_narration(...)` colocated
- `tmp/app-session-persistence-spec.md` — behavior + tests (this change)
- `app/tests/test_session_resume_failure.py` — recommended (extend ticket Expected files before impl)

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial PM draft (APP-071) |
| 2026-05-20 | PM r2: R0 ordered variant selection; `_emit_recovery_narration` (no drift); R3 `format_creation_status` footer; APP-019 scope split |
