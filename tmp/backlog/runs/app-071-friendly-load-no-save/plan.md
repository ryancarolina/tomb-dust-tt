# Implementation Plan: APP-071-friendly-load-no-save

**Status:** draft (Dev plan phase)  
**backlog_ticket:** APP-071  
**ticket_path:** tmp/backlog/app-071-friendly-load-game-when-no-save.md  
**domain_spec:** tmp/app-session-persistence-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Summary

When `process_turn` handles `load game` / `load` / `continue` / `resume` and `bridge.session_resume()` fails, replace the terse engine error return with **variant-aware recovery copy**, emit **`gm_narration` via `_emit_recovery_narration`** (no drift check), and keep **`log_error("session_resume", …)`** for QA. Add pytest coverage in `test_session_resume_failure.py`. No required `app/ui/app.py` edits.

---

## Root cause (current)

```444:448:app/gm/orchestrator.py
        elif lower in ("continue", "resume", "load", "load game"):
            result = self.bridge.session_resume()
            if not result.get("ok"):
                log_error("session_resume", result.get("error", "unknown"))
                return f"Could not resume: {result.get('error', 'unknown')}. Try 'new game' instead."
```

| Gap | Effect |
|-----|--------|
| No `_emit_*` on failure | JSONL has `error` only — panel may show return text but no `gm_narration` |
| Raw engine error in copy | `no save session found` — not player-facing |
| Resume branch before `creation.active` guard | Mid-creation players get cold-path message |
| `_emit_narration` would drift | Recovery footers like `[Awaiting: new game]` trigger `awaiting_mismatch` when `_creation_drift_scope()` is true |

Success path (unchanged): `_restore_history`, `_sync_creation_from_status`, recap / `_creation_turn` resume.

---

## Code-path traces (planned)

### A. Failed resume — cold workspace (variant A)

| Step | Location | Action |
|------|----------|--------|
| A1 | `process_turn` | `lower in ("continue", "resume", "load", "load game")` |
| A2 | `bridge.session_resume()` | `{"ok": False, "error": "no save session found"}` |
| A3 | `log_error("session_resume", error)` | **Retain** (T3) |
| A4 | `_is_mid_creation_resume_failure()` | **False** — no `creation.active`, no engine `CHARACTER_CREATION`+empty roster, no app save signal |
| A5 | `_resume_failure_message(result)` | Build variant A prose + `[Awaiting: new game]` footer |
| A6 | `_emit_recovery_narration(message)` | `log_gm_narration` only — **no** `_check_creation_drift` |
| A7 | `return message` | UI `narration_text`; `_extract_suggestions` → `["new game"]` |

### B. Failed resume — mid-creation (variant B)

| Step | Location | Action |
|------|----------|--------|
| B1 | Prior turns | `new game` → `setup_new_game` → `_creation_turn` → `creation.active`, `step` e.g. `RACE` |
| B2 | `session_resume()` | Fails (empty roster, no `find_save_campaign`) |
| B3 | `_is_mid_creation_resume_failure()` | **True** if any R0 signal (see § Helpers) |
| B4 | `_resume_failure_message(result)` | Variant B: step label via `CREATION_STATUS_LABELS` / `format_creation_status`; prose mentions `new game` + continue desk — **not** in bracket `Awaiting:` |
| B5 | Footer | `[{format_creation_status(self.creation)}]` → e.g. `[Awaiting: RACE_INPUT]` |
| B6 | `_emit_recovery_narration(message)` | Same as A6 — **no** `creation_drift` / `awaiting_mismatch` (T2) |

### C. Successful resume (regression — no edit unless accidental)

| Step | Location | Action |
|------|----------|--------|
| C1 | `session_resume()` ok | Existing 466–492 flow |
| C2 | Death-on-resume | `_emit_narration(death_msg)` — unchanged |
| C3 | Creation resume | `_creation_turn("[SYSTEM: Resume…]")` — unchanged |

### D. Out of scope (document only)

| Step | Location | Note |
|------|----------|------|
| D1 | `app/ui/app.py` `_process_turn` | Still queues `load_session` before orchestrator; may replay `session_state.json` on failure — spec accepts; do not reorder in APP-071 |
| D2 | `setup_new_game` failure | Unchanged unless drive-by; mirror R1 only if touched |
| D3 | APP-064 startup prompt | Separate ticket |

---

## Helpers (new, colocated in `orchestrator.py`)

Place near `_emit_narration` (~286) so emit contract is obvious.

### `_emit_recovery_narration(self, message: str) -> None`

- Call `log_gm_narration(message)` from `gm.logger`.
- **Do not** call `_check_creation_drift` or `_emit_narration`.
- **Do not** add `log_player_message` (non-existent per spec).
- Optional: do **not** append `self.history` (matches `run_ended` death path — JSONL + return string is sufficient for APP-071).

### `_is_mid_creation_resume_failure(self) -> bool`

Evaluate **any** (R0 / spec variant B first):

1. `self.creation.active` is `True`.
2. App save signal: `session_state.json` exists under `app/` parent of `gm/` and `creation_state` in JSON has `active: true` OR `step` set beyond default in-progress desk (e.g. not only wiped NAME-only stub). Reuse path pattern from `_restore_history` (`Path(__file__).resolve().parents[1] / "session_state.json"`).
3. Engine signal: `bridge.status()` → `awaiting == "CHARACTER_CREATION"` and `not (roster)`.

Catch exceptions from `status()` / file read → treat signal as false for that branch.

### `_resume_failure_message(self, result: dict) -> str`

- Map engine errors: `no save session found` and unknown → friendly prose; **never** primary-display raw `result["error"]`.
- If `_is_mid_creation_resume_failure()` → **variant B**:
  - Explain no **finished** engine save (living slotted character required).
  - Include human step: `CREATION_STATUS_LABELS.get(self.creation.step, …)` or short phrase from step.
  - Prose: keep answering prompts; type **`new game`** to wipe (warn progress loss). **`new game`** / continue creation **only in prose**, not bracket token.
  - Footer: newline + `[{format_creation_status(self.creation)}]` (brackets per UI `_extract_suggestions` regex).
- Else → **variant A**:
  - No saved game found; suggest **`new game`**; optional one line that app autosave ≠ engine roster save.
  - Footer: `[Awaiting: new game]` (allowed — `_creation_drift_scope()` false on cold path).

---

## Task breakdown

### 1. Add recovery helpers — `app/gm/orchestrator.py`

1. Implement `_emit_recovery_narration`, `_is_mid_creation_resume_failure`, `_resume_failure_message` after `_emit_narration`.
2. Import already has `format_creation_status`, `CREATION_STATUS_LABELS` — use for variant B copy/footer.
3. Keep helpers private; no bridge/engine changes.

### 2. Wire failure branch — `app/gm/orchestrator.py` `process_turn`

Replace lines 446–448 with:

```python
if not result.get("ok"):
    log_error("session_resume", result.get("error", "unknown"))
    message = self._resume_failure_message(result)
    self._emit_recovery_narration(message)
    return message
```

- All four load synonyms share this branch (existing `elif`).
- Do **not** call `_emit_narration` on this path.

### 3. Add tests — `app/tests/test_session_resume_failure.py`

Follow `conftest.py` `orchestrator` fixture + lazy-import discipline (module-level constants OK; import `Orchestrator` only inside tests if mirroring `test_creation_flow.py` pattern).

| Case | Setup | Action | Assert |
|------|--------|--------|--------|
| **T1** | `orchestrator` on isolated workspace, no prior `new game` | `process_turn("load game")` | Variant A keywords (`no saved`, `new game`); `[Awaiting: new game]` in text; monkeypatch `log_gm_narration` called once |
| **T2** | `process_turn("new game")` then `process_turn("Dumpy")` (NAME → RACE) | `process_turn("load game")` | Variant B: mentions creation / step (e.g. race); `[Awaiting: RACE_INPUT]`; **not** only `no save session found`; `log_creation_drift` monkeypatch → no event with `awaiting_mismatch` in `reasons` |
| **T3** | Same as T1 | `process_turn("load game")` | `log_error` called with context `session_resume` |

Implementation notes:

- Monkeypatch `gm.orchestrator.log_gm_narration` and `log_error` to lists; assert call args.
- T2: monkeypatch `log_creation_drift` to `drift_events.append` (pattern from `test_creation_flow.py`).
- Markers: `-k "session_resume or load_game"` per domain spec.

### 4. Domain spec sync — `tmp/app-session-persistence-spec.md` (on close)

- Check APP-071 task checkbox; changelog already has 2026-05-20 row — confirm behavior matches impl.
- `release APP-071 --done` after pytest green + manual smoke optional.

---

## Files (must ⊆ ticket Expected files)

| File | Change |
|------|--------|
| `app/gm/orchestrator.py` | `_emit_recovery_narration`, `_is_mid_creation_resume_failure`, `_resume_failure_message`; failure branch in `process_turn` |
| `app/tests/test_session_resume_failure.py` | **New** — T1–T3 |
| `tmp/app-session-persistence-spec.md` | Changelog / checklist on close only |

**Out of scope (explicit):**

- `app/ui/app.py` — no required edit; fallback `("suggestions", …)` only if manual QA shows missing chips
- `play/tomb_gm/domain/session.py` — eligibility unchanged
- `setup_new_game` failure path — unchanged
- `tmp/app-logging-qa-spec.md` — optional drift exempt note (non-blocking per qa-spec-pass)
- APP-064, APP-019

---

## Tests

```bash
# From repo root
python -m pytest app/tests/test_session_resume_failure.py -q
python -m pytest app/tests -q -k "session_resume or load_game"
```

| Step | Command | Expected |
|------|---------|----------|
| New module | `pytest app/tests/test_session_resume_failure.py -q` | T1–T3 pass |
| Filter | `pytest app/tests -q -k "session_resume or load_game"` | Same tests collected |
| Regression | `pytest app/tests/test_creation_flow.py -q` | Green (no resume-path regression) |

**Manual smoke (Stage 7):** `cd app && python main.py` — TC-A/B/C in spec.md; tail `app/logs/session-*.jsonl` for `error` + `gm_narration`, no spurious `creation_drift` on T2 path.

---

## Rollback / risks

| Risk | Mitigation |
|------|------------|
| Spurious `creation_drift` | Use `_emit_recovery_narration` only; variant B footer = `format_creation_status` only |
| Fuzzy R0 signal #2 (app save) | T2 covers primary path (`creation.active`); file signal is fallback for desync |
| UI `_load_session` on failed resume | Documented; do not reorder in APP-071 |
| Copy drift vs APP-019 | Narration-only; toast remains APP-019 |

**Rollback:** Revert `orchestrator.py` failure branch + delete test file.

---

## Acceptance mapping

| Ticket AC | Plan task |
|-----------|-----------|
| Player-facing narration | §2 failure branch + `_resume_failure_message` |
| JSONL `error` + player-visible log | `log_error` retained + `_emit_recovery_narration` |
| Distinguish no save vs mid-creation | `_is_mid_creation_resume_failure` + A/B variants |
| APP-019 not bundled | No toast; `setup_new_game` unchanged |
