# Reflection: Dev — APP-066 WS2

**backlog_ticket:** APP-066  
**workstream:** WS2 — Golden-path drift assert (optional)  
**date:** 2026-05-20

## What shipped

- Added `app/tests/test_creation_flow.py` to ticket **Expected files** before editing the test module (qa-plan-pass gate).
- In `test_full_creation_apprentice_caster`:
  - Monkeypatched `gm.orchestrator.log_creation_drift` to collect drift payloads in `drift_events`.
  - After the full `INPUTS` golden-path loop, asserted `drift_events == []` with a helpful failure message.
- Did **not** add optional unit probes (`test_check_creation_drift_healthy_skills_step` / negative probe) — plan §7 marks them optional; integration assert satisfies spec R6 and ticket AC optional item.

## Design choices

- **Collection point:** patch at module path `gm.orchestrator.log_creation_drift` (same pattern as plan §7) so all drift emissions during creation turns are captured without importing `Orchestrator` at module level (APP-049).
- **Assert placement:** after INPUTS loop, before post-finalize roster/status asserts — confirms zero drift during active creation FSM, including steps where engine `awaiting` stays coarse `CHARACTER_CREATION` but footer labels are granular.
- **WS2-only scope:** no orchestrator edits; WS1 label compare already green.

## Verification

```bash
python -m pytest app/tests/test_creation_flow.py -q
# 2 passed in 0.80s

python -m pytest play/tomb_gm/tests/test_campaign_session.py -q
# 1 passed in 1.18s
```

## Handoff (ticket release — not WS2)

- Append changelogs in `tmp/app-character-creation-spec.md` and `tmp/app-logging-qa-spec.md`.
- Mark ticket AC checkboxes; `python tmp/backlog/claim_ticket.py release APP-066 --done`.

## Risks / notes

- Assert locks golden-path silence only; real drift (wrong footer vs step) still covered by WS1 orchestrator logic — optional negative unit probe could be added later if regression risk grows.
- `test_name_advance_presents_race_table` (APP-068) runs in same file but does not collect drift; acceptable — single-turn probe, not full creation path.
