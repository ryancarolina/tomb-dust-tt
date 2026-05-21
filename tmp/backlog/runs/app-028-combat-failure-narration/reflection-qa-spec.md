# Reflection: QA spec — round 1 (APP-028)

## Completed

- Read `research-brief.md`, `spec.md`, ticket APP-028, `tmp/app-combat-play-spec.md`, dev-team templates, and live `app/gm/orchestrator.py` / `tools.py` traces cited in research.
- Wrote `qa-spec-report-1.md` with **FAIL** (4 blockers, 1 major, 1 minor).
- Confirmed `registry_gap: false` and domain spec § Combat tool failure narration aligns with run spec on R1–R8 **intent**.

## Self-critique

- Did not read full `bridge.py` failure payloads for `cast_spell` / `fortune_spend` — assumed R2 generic strip covers them if `all_failed`; adversarial gap is **missing tests**, not unknown bridge behavior.
- Did not cross-check `tmp/app-llm-orchestrator-spec.md` for conflicting “all_failed” language — coordination pointer only; low risk.
- Session log `app/logs/session-2026-05-20.jsonl` absent (gitignored); grave-ghoul repro relies on architecture trace, not log replay.

## Missed?

| Area | Checked? | Note |
|------|----------|------|
| Ticket Expected files vs tests | Yes | TICKET-001 blocker |
| All combat tools in AC | Partial | SPEC-002 — 3/5 exploration tools untested |
| Grave-ghoul / beat-trigger | Yes | SPEC-001, SPEC-004 |
| orchestrator.py scope only | Yes | Tests out of ticket |
| R4 combat inner injection | Yes | SPEC-003 |
| R8 logging | Yes | SPEC-005 minor only |
| APP-026/027 overlap | Yes | Correctly non-goals |
| `combat_fsm.py` edits | Yes | R7 optional; not required in Expected files |

## Handoff

- **Needs PM revision** — address `qa-spec-report-1.md` blockers before spec QA round 2.
- Orchestrator should **not** dispatch Dev (plan) until spec PASS.
- Re-review: ticket Expected files, R1 observable contract + E2E beat test, parametrized exploration tool failures, R4 partial-failure test.
