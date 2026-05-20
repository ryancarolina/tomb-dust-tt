# Drift Check: APP-066-sync-engine-awaiting-with-creation-step

**backlog_ticket:** APP-066  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) | no | Changelog: added **APP-066 done** row (2026-05-20); § Awaiting contract (engine vs app) and `CREATION_STATUS_LABELS` table match `creation.py` + `orchestrator.py` |
| [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md) | no | Changelog: added **APP-066 done** row (2026-05-20); § `creation_drift` awaiting compare, reasons, payload fields match `_check_creation_drift` |
| Run `spec.md` R1–R6 | no | Verified against `orchestrator.py`, `creation.py`, `test_creation_flow.py` |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| **R1** Two-layer awaiting: engine `CHARACTER_CREATION` vs app `CREATION_STATUS_LABELS` | `creation.py` L69–80; `orchestrator.py` L174–178, L210–213; engine unchanged in `play/tomb_gm` | yes |
| **R2** Drift compares narrated `Awaiting:` to expected label when `creation.active` | `_expected_creation_awaiting_label()`; `awaiting_mismatch` only on label mismatch (L210–213) | yes |
| **R2** Resume edge: skip awaiting compare when not `creation.active` | Awaiting branch gated on `self.creation.active` (L210) | yes |
| **R3** No `phase_mismatch` when footer omits `Phase:` during desk creation | `phase_mismatch` only when both `narrated_phase` and `engine_phase` present (L214–215) | yes |
| **R3** `premature_exploration_phase` guard retained | L216–217 | yes |
| **R4** `_creation_drift_scope` unchanged | L180–190 | yes |
| **R5** Optional `expected_awaiting` in payload | L232–233 when compare runs | yes |
| **R6** Golden-path pytest + no drift assert | `test_creation_flow.py` L39–43, L81 | yes |

## Ticket AC ↔ code

| Acceptance criterion | Result |
|--------------------|--------|
| Label-based drift compare (not engine `CHARACTER_CREATION`) | **PASS** |
| No `creation_drift` on every healthy creation turn | **PASS** (code + `drift_events == []`) |
| Domain spec documents awaiting contract | **PASS** |
| Optional golden-path no-drift assert | **PASS** |

## Tests run

```bash
python -m pytest app/tests/test_creation_flow.py play/tomb_gm/tests/test_campaign_session.py -q
```

**Result:** 3 passed (1.76s)

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec changelogs — **APP-066 done** rows appended
- [ ] Ticket **Status** → `done` / **Closed** date — orchestrator at `release APP-066 --done`
- [ ] `python tmp/backlog/claim_ticket.py release APP-066 --done` — orchestrator (not QA drift agent)

## Ancillary notes (non-blocking)

- `tmp/app-logging-qa-spec.md` task checklist still lists APP-057 as open; APP-057 is closed in character-creation spec — pre-existing index drift, outside APP-066 scope.
- Manual JSONL replay (`grep creation_drift` on live session) not run in drift round; integration test + code read sufficient for PASS.
- Human PyGame playtest deferred to Stage 7 per run `spec.md` § Human playtest hints.
