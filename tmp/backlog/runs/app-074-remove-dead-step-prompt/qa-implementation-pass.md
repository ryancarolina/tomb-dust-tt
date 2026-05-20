# QA PASS: implementation

**Task:** APP-074-remove-dead-step-prompt  
**backlog_ticket:** APP-074  
**ticket_path:** tmp/backlog/app-074-remove-dead-get-step-prompt.md  
**Round:** 1  
**domain_spec_creation:** synced (`tmp/app-character-creation-spec.md` changelog APP-074 done)

## Verdict

**PASS** — dead `get_step_prompt()` removed; `app/` grep clean; creation regression suite green; domain spec matches code.

## Automated tests

```text
python -m pytest app/tests/test_creation_flow.py app/tests/test_creation_tables.py play/tomb_gm/tests/test_creation_gating.py -q
...................                                                      [100%]
19 passed in 1.38s
```

| Module | Tests | Result |
|--------|-------|--------|
| `app/tests/test_creation_flow.py` | integration + APP-067/068/069 regressions | ✓ |
| `app/tests/test_creation_tables.py` | APP-072 table strip | ✓ |
| `play/tomb_gm/tests/test_creation_gating.py` | engine gating | ✓ |

## Grep / symbol checks

| Check | Command / trace | Result |
|-------|-----------------|--------|
| No `get_step_prompt` under `app/` | `rg "get_step_prompt" app/` | Zero matches |
| Function deleted | `creation.py` — no `def get_step_prompt`; `parse_player_race` at L742 (adjacent symbol intact) | ✓ |
| Orchestrator unchanged | `orchestrator.py` — no import or reference | ✓ |
| Live combat symbol preserved | Domain spec contrasts dead `get_step_prompt` vs live `get_combat_step_prompt` (different domain) | ✓ |

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| Remove `get_step_prompt()` (or docs-only hint) | `git diff --stat app/gm/creation.py`: **94 lines deleted**, no additions | ✓ |
| Grep `app/` confirms no references | `rg` zero hits under `app/` | ✓ |
| Domain spec: prompts in `_auto_present_*` / `format_*_table` only | § Step content sources (APP-074); § Removed patterns; file map “no `get_step_prompt`” | ✓ |

## Spec / run spec → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | Delete `get_step_prompt` (~742–833) | Entire function removed; next symbol `parse_player_race` | ✓ |
| **R1** | `rg "get_step_prompt" app/` zero post-delete | Independent QA grep | ✓ |
| **R2** | No orchestrator / bridge edits required | No diff outside `creation.py` + spec/ticket under reviewed scope | ✓ |
| **R3** | Domain § Step content sources + changelog | Changelog row: “APP-074: removed legacy `get_step_prompt()`…”; no present-tense “defines” for dead builder | ✓ |
| **R3** | Spec ↔ code drift | Target-state prose (“has no”) now matches deleted code | ✓ |

## Diff scope reviewed

| File | Change | In ticket Expected files? |
|------|--------|---------------------------|
| `app/gm/creation.py` | −94 lines (dead function only) | ✓ |
| `tmp/app-character-creation-spec.md` | +§ Step content sources, Removed patterns, file map, changelog | ✓ |
| `tmp/backlog/app-074-remove-dead-get-step-prompt.md` | AC checked; status `done`; Closed 2026-05-20 | ✓ |

No unauthorized edits under `app/` (orchestrator, bridge, tests unchanged — correct for deletion-only chore).

## Scope notes (non-blocking)

| Item | Note |
|------|------|
| **APP-059 backlog** | `tmp/backlog/app-059-standardize-creation-table-outputs.md` still cites `get_step_prompt` as RACE problem source — optional close hygiene per plan; not impl blocker |
| **Run `status.md`** | Pipeline checklist still shows pre-impl stages; update at Stage 6 drift / release |
| **Human playtest** | Not required for this chore (no behavior change on live path) |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-074 --done` (if not already released from batch).  
**Optional:** APP-059 ticket prose hygiene on APP-074 close.
