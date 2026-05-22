# Human Playtest Plan: APP-002-log-creation-drift-events

**backlog_ticket:** APP-002
**Commit:** `b19ec73` (or latest on `main` containing APP-002)
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

## Prerequisites

- [ ] OpenRouter / LLM config if testing full creation narration (or use steps that trigger deterministic narration)
- [ ] Start **new game** (empty roster)
- [ ] Optional: tail `app/logs/session-YYYY-MM-DD.jsonl` in another terminal

## Test cases

### TC-1: No drift during normal creation (happy path)

**Goal:** Wrong-phase narration does not appear; no spurious `creation_drift` events during valid creation.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Launch `python main.py` | App window opens | [ ] |
| 2 | Type `new game`, complete name/race/class through at least one LLM-narrated step | GM replies; creation advances | [ ] |
| 3 | Inspect today's JSONL log | `gm_narration` lines present; **no** `creation_drift` while steps match engine | [ ] |

**Failure signals:** UI phase badge shows delve/extract before roster exists; `creation_drift` with `awaiting_mismatch` during normal clerk flow.

### TC-2: Drift logged when narration lies (if reproducible)

**Goal:** Structured `creation_drift` event fires when status line disagrees with engine during creation.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | During active creation (no roster), provoke GM text with status line `Phase: delve` or `Awaiting: PLAYER_ACTIONS` (may require LLM non-compliance) | — | [ ] |
| 2 | Check JSONL after that narration | One `creation_drift` entry with `step`, `roster_len`, `awaiting`, `creation.active`, and `reasons` | [ ] |

**Failure signals:** Obvious phase/awaiting lie in narration but no `creation_drift` line.

### TC-3: Post-finalize exploration

**Goal:** After character exists, creation drift scope off; normal `Phase: preparation` OK.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Finish creation through finalize | Non-empty roster; surface at Registry | [ ] |
| 2 | One exploration command (`look around` or travel) | Narration with `Phase: preparation` (or valid phase); no creation_drift spam | [ ] |

**Failure signals:** `creation_drift` after roster populated for ordinary play.

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

APP-003 will add per-turn `creation_step` logging — combine with this plan when that lands.
