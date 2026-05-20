# Human Playtest Plan: APP-003-log-creation-step-snapshot

**backlog_ticket:** APP-003
**Commit:** pending
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

## Prerequisites

- [ ] OpenRouter API key configured (or mock if available)
- [ ] Fresh session: type `new game` at prompt
- [ ] Log path: `app/logs/session-YYYY-MM-DD.jsonl` (today's date)

## Test cases

### TC-1: creation_step on new game start (maps to AC)

**Goal:** First creation turn emits `creation_step` with NAME step.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Launch app (`python main.py`) | Window opens, no traceback | [ ] |
| 2 | Type `new game` and submit | GM asks for delver name | [ ] |
| 3 | Open `app/logs/session-<today>.jsonl` | At least one line with `"type": "creation_step"` | [ ] |
| 4 | Inspect latest `creation_step` entry | `data.step` is `NAME`, `roster_len` is 0, `awaiting` is `CHARACTER_CREATION`, `creation.active` is true | [ ] |

**Failure signals:** No `creation_step` lines; missing fields; crash on new game.

### TC-2: creation_step advances with player input

**Goal:** Each creation turn adds another snapshot.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | Enter a delver name and submit | GM responds with race/class prompt | [ ] |
| 2 | Tail JSONL log | New `creation_step` entry; `step` may advance (e.g. RACE) | [ ] |
| 3 | Count `creation_step` events | Count ≥ number of creation turns taken | [ ] |

**Failure signals:** Only one snapshot for multiple turns; `step` stuck while UI progressed.

### TC-3: No regression on APP-002 drift logging

**Goal:** Drift events still work when status line disagrees.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | During creation, note `creation_step` baseline in log | Regular snapshots present | [ ] |
| 2 | If GM narration includes wrong Phase/Awaiting (rare) | Optional `creation_drift` event may appear | [ ] |

**Failure signals:** `creation_drift` broken; duplicate errors in log.

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- APP-004 should add `advanced_to` on successful `_execute_creation_choice` — correlate with `creation_step` step changes in same JSONL file.
