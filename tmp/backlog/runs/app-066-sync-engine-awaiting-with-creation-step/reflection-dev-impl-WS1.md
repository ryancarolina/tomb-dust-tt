# Reflection: Dev — APP-066 WS1

**backlog_ticket:** APP-066  
**workstream:** WS1 — Drift comparator fix  
**date:** 2026-05-20

## What shipped

- Imported `CREATION_STATUS_LABELS` from `gm.creation` in `app/gm/orchestrator.py`.
- Added `_expected_creation_awaiting_label()` mirroring `format_creation_status()` fallback (`CREATION_STATUS_LABELS.get(step, f"{step}_INPUT").upper()`).
- Rewrote `_check_creation_drift` awaiting branch:
  - When `creation.active` and narration has `Awaiting:`, compare to expected label from FSM step — not engine `CHARACTER_CREATION`.
  - When scope true but `creation.active` false (resume edge), skip awaiting compare (R4).
  - Phase guards unchanged: `phase_mismatch` only when both narrated and engine phase present and differ; `premature_exploration_phase` unchanged.
- Added optional `expected_awaiting` to `log_creation_drift` payload when computed (R5).
- Removed dead `engine_awaiting` local used only for the old compare.

## Design choices

- **Label source:** single map import from `creation.py` — no duplicated label table in orchestrator.
- **Engine value preserved:** payload still includes `"awaiting": status.get("awaiting")` for grep/QA.
- **Scope untouched:** `_creation_drift_scope` left as-is per plan Trace B.

## Verification

```bash
python -m pytest play/tomb_gm/tests/test_campaign_session.py -q
# 1 passed in 1.16s
```

## Handoff to WS2

- Optional: monkeypatch `log_creation_drift` in `test_full_creation_apprentice_caster` and assert `drift_events == []` on golden path.
- Optional unit probes for `_check_creation_drift` match/mismatch vs `CREATION_STATUS_LABELS`.
- Ticket release: domain/logging spec changelogs + `claim_ticket.py release APP-066 --done`.

## Risks / notes

- Resume edge with narrated awaiting but no restored `creation_state` will not flag awaiting drift until `import_creation_state` runs — intentional per R4.
- Real drift (wrong footer vs step) still logs `awaiting_mismatch` with `expected_awaiting` when `creation.active`.
