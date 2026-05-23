# Dev Team — Artifact Templates

Copy sections into **`tmp/backlog/runs/<APP-XXX>-<task-name>/`** files. Replace placeholders.

**Stage 0:** run `python tmp/backlog/claim_ticket.py APP-XXX --task <task-name>` before creating artifacts.

**Paths:** write only under `tmp/backlog/runs/<APP-XXX>-<task-name>/`. Never `.dev-team/` or out-of-tree pointers.

**Manifest:** every `@dev-team` claim uses `--dev-team` (or `pipeline-init`) so `pipeline-manifest.json` exists. Orchestrator runs `pipeline-set-stage` after each gate. `release --done` calls `pipeline-check` unless `--waive-pipeline`.

**Subagents:** reflect→retry loop (≤3 attempts per dispatch); **Reflection** block in return message only — no files.

---

## pipeline-manifest.json

Created at claim (`--dev-team`) or via `pipeline-init`. Linked from `status.md`.

```json
{
  "ticket_id": "APP-XXX",
  "task_name": "kebab-name",
  "dev_team": true,
  "stage": "claim",
  "gates": {
    "research_brief": { "done": false, "at": null },
    "spec_qa_pass": { "done": false, "at": null },
    "plan_qa_pass": { "done": false, "at": null },
    "implementation_qa_pass": { "done": false, "at": null },
    "drift_check": { "done": false, "at": null },
    "human_test_plan": { "done": false, "at": null },
    "commit": { "done": false, "at": null }
  },
  "waivers": { "pipeline": false, "playtest": false, "commit": false },
  "updated_at": "2026-05-22T00:00:00Z"
}
```

**Anti-patterns:** multi-ticket impl Task · silent ticket renumber · `release --done` without `pipeline-check` · skipping `pipeline-set-stage` after QA PASS · orchestrator backfill of gates/artifacts · chaining Stage 0 with `&&` on PowerShell · positional `APP-XXX=task-name` instead of `--task`.

**Bootstrap:** meta tickets building this system may use `pipeline-init --no-dev-team` until hooks land.

---

## batch-board

Orchestrator writes after `schedule` + `claim-batch` (one copy; link from each ticket `status.md`).

**Filename (required):** `tmp/backlog/runs/batch-board-<sorted-ticket-ids>.md`

- Include every ticket in the batch: `batch-board-APP-064-APP-071-APP-074.md`
- Sort IDs ascending (`APP-064` before `APP-071`)
- Single ticket: `batch-board-APP-066.md`
- Do **not** use dates or `-b` suffixes — ticket IDs are the batch identity
- After `claim-batch`, use the `batch_board` path from CLI JSON output

```markdown
# Batch board

**Updated:** <date>
**Max parallel:** 3

## Tickets

| ID | Priority | Run folder | Pipeline stage | Blocked by (impl) | Commit |
|----|----------|------------|----------------|-------------------|--------|
| APP-001 | P0 | tmp/backlog/runs/... | research | — | — |
| APP-002 | P0 | tmp/backlog/runs/... | spec | — | — |
| APP-004 | P0 | tmp/backlog/runs/... | claim | APP-002 | — |

_Update **Pipeline stage** as each lane advances. Set **Commit** to hash after Stage 7a (one commit per row). Mark **complete** only when commit + `human-test-plan.md` exist for that ID._

## Implementation waves (from schedule)

1. Parallel: APP-001, APP-002
2. Parallel: APP-004 (after APP-002 done)

## Commands

- `python tmp/backlog/claim_ticket.py batch-status`
- `python tmp/backlog/claim_ticket.py focus APP-XXX`
- `python tmp/backlog/claim_ticket.py impl-check APP-XXX`
```

---

## Subagent return (Reflection block — not a file)

After **reflect→retry loop** (≤3 attempts). Include in the Task return message:

```markdown
## Reflection

**Attempts:** 1 | 2 | 3
**Completed:** …
**Self-critique:** …
**Missed?:** …
**Handoff:** ready for next gate | needs human input
```

- **ready** — task complete after self-review
- **needs human input** — required if still incomplete after attempt 3 (list blockers)

Do **not** write this to disk.

## Drift check (Stage 6 only — not a file)

Include in the QA drift-gate Task return message (alongside **Reflection**):

```markdown
## Drift check

**Verdict:** PASS | UPDATED | FAIL
**Specs compared:** …
**Domain spec updates:** <paths + § or none>
**Ticket AC:** all checked / noted exceptions
**Release ready:** yes | no — <blockers if no>
```

Do **not** write `drift-check.md` or `reflection-qa-drift.md`.

---

## status.md

```markdown
# Pipeline: <APP-XXX>-<task-name>

**Goal:** <one line>
**Backlog ticket:** [APP-XXX](../../app-xxx-slug.md)
**Domain spec:** [app-example-spec.md](../../app-example-spec.md)
**Run folder:** tmp/backlog/runs/<APP-XXX>-<task-name>/
**Manifest:** [pipeline-manifest.json](./pipeline-manifest.json)
**Batch board:** [batch-board-APP-XXX-APP-YYY.md](../batch-board-APP-XXX-APP-YYY.md)
**Started:** <date>
**Current stage:** claim | research | spec | plan | implement | impl-qa | drift | commit | playtest | complete | blocked

## Checklist

- [ ] Stage 0 — ticket claimed (`tmp/.active-ticket.json`, ticket `in_progress`)
- [ ] Research → research-brief.md (dispatched)
- [ ] PM spec draft (dispatched)
- [ ] QA spec PASS (round __/3, backlog_ticket verified)
- [ ] Dev plan (dispatched)
- [ ] QA plan PASS (round __/3, ticket scope verified)
- [ ] workstreams + parallel implementation
- [ ] QA implementation PASS (dispatched)
- [ ] Stage 6 — drift check (return **Drift check** block; domain spec + ticket AC synced) + release (`claim_ticket.py release APP-XXX --done`)
- [ ] Stage 7 — git commit **this APP-XXX only** (hash: ______)
- [ ] Stage 7 — human-test-plan.md (this run folder only)
- [ ] Batch board row updated (if multi-ticket)

## Blockers

_None._

## Links

- Ticket: ../../app-xxx-slug.md
- research-brief.md
- spec.md
- plan.md
- human-test-plan.md
```

---

## research-brief.md

```markdown
# Research Brief: <APP-XXX>-<task-name>

**Date:** <date>
**Question:** <what we need to answer>

**backlog_ticket:** APP-XXX
**ticket_path:** tmp/backlog/app-xxx-slug.md
**domain_spec:** tmp/app-example-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false | true

## Registry gap justification

<If false: cite ticket domain spec + app-master-spec registry row.>
<If true: why no row fits; proposed domain spec path.>

## Summary

<3–6 sentences>

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| | | |

## Code-path traces

### <flow name>

1. Entry: `path:symbol`
2. …
3. Exit / persistence: …

## Existing specs & docs

- Ticket domain spec: …
- …

## Tests & commands

```bash
# commands that exercise this area
```

## Risks & unknowns

- …

## Raw notes

<grep hits, edge cases, links>
```

---

## spec.md (run-local)

```markdown
# Spec: <APP-XXX>-<task-name>

**Status:** draft | qa-review | approved
**backlog_ticket:** APP-XXX
**ticket_path:** tmp/backlog/app-xxx-slug.md
**domain_spec:** tmp/app-example-spec.md
**registry_gap:** <echo from research-brief; PM may correct with note>
**Domain specs touched:** <paths or none>

## Proposed domain spec

_Fill only when `registry_gap: true`. Delete section when false._

| Field | Value |
|-------|--------|
| Proposed file | `tmp/app-<domain>-spec.md` or `build/docs/engine-integration.md` (canon only) |
| Registry row | <domain name — added to app-master-spec on create> |
| Owns | <code paths — must ⊆ ticket Expected files> |
| Why not existing owner | <which rows were ruled out> |

## Problem

…

## Goals

- …

## Non-goals

- …

## Requirements

### R1: …

**Acceptance criteria**

- [ ] …

## Test plan

```bash
pytest …
```

## Human playtest hints (for Stage 7)

_Bullet list of in-game scenarios QA will expand into `human-test-plan.md` (PyGame client, not headless only)._

- …

## Affected paths

_Must match or subset of ticket **Expected files**._

- …

## Changelog

| Date | Change |
|------|--------|
| | Initial draft |
```

---

## qa-spec-report-N.md / qa-plan-report-N.md

```markdown
# QA Report: <spec|plan> — round <N>

**Task:** <APP-XXX>-<task-name>
**backlog_ticket:** APP-XXX
**Verdict:** FAIL
**Reviewer role:** QA (adversarial)

## Findings

### SPEC-001 — blocker

- **Location:** …
- **Issue:** …
- **Implementation gap:** …
- **Suggested fix:** …

### TICKET-001 — blocker _(spec/plan stages)_

- **Issue:** Missing/invalid backlog ticket, wrong domain spec, or plan file not in ticket Expected files
- **Suggested fix:** …

## Summary

<what must change before PASS>

## Re-review focus

- …
```

---

## qa-spec-pass.md / qa-plan-pass.md

```markdown
# QA PASS: <spec|plan>

**Task:** <APP-XXX>-<task-name>
**backlog_ticket:** APP-XXX
**ticket_path:** tmp/backlog/app-xxx-slug.md
**Round:** <N>
**domain_spec_creation:** approved | not_needed | rejected

**Verified:**

- [ ] Backlog ticket valid; status `open` or `in_progress`
- [ ] Ticket domain spec matches spec updates
- [ ] Acceptance criteria testable
- [ ] Code traces match repo (plan only)
- [ ] AGENTS.md / canon compliance
- [ ] Tests/commands listed
- [ ] Plan files ⊆ ticket Expected files (plan only)
- [ ] registry_gap matches reality (spec only)
- [ ] If registry_gap true: domain spec exists or approved § Proposed domain spec (spec only)

**Notes:** <optional>
```

---

## New domain spec (after QA approved)

Create `tmp/app-<domain>-spec.md` with sections from [app-master-spec.md](../../tmp/app-master-spec.md) § Domain spec template, then add registry row:

```markdown
| <Domain name> | [`app-<domain>-spec.md`](app-<domain>-spec.md) | `<owned app paths>` | `<engine/canon links>` |
```

Also create matching backlog ticket if ongoing work remains.

---

## plan.md

```markdown
# Implementation Plan: <APP-XXX>-<task-name>

**Status:** draft | qa-review | approved
**backlog_ticket:** APP-XXX
**ticket_path:** tmp/backlog/app-xxx-slug.md
**domain_spec:** tmp/app-example-spec.md
**Spec:** spec.md (+ links)

## Approach

<short architecture>

## Code-path traces (planned)

### Change: <title>

| Step | File:symbol | Action |
|------|-------------|--------|
| 1 | | |

## Task breakdown

1. …

## Files (must ⊆ ticket Expected files)

- …

## Tests

| Step | Command | Expected |
|------|---------|----------|
| | | |

## Rollback / flags

…

## Open questions

- …
```

---

## workstreams.md

```markdown
# Workstreams: <APP-XXX>-<task-name>

**backlog_ticket:** APP-XXX

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | | — | | tests green |
| WS2 | | WS1? | | |

## WS1 — <name>

**Scope:** …
**Prompt seed for Task subagent:** Must include `backlog_ticket: APP-XXX`, ticket path, run-folder paths, AGENTS.md constraints …
```

---

## qa-implementation-report.md

```markdown
# QA Report: Implementation

**Task:** <APP-XXX>-<task-name>
**backlog_ticket:** APP-XXX
**Verdict:** FAIL

## Findings

### IMPL-001 — blocker

- **Location:** `file:line`
- **Issue:** …
- **Spec/plan/ticket reference:** …
- **Suggested fix:** …

## Tests run

| Command | Result |
|---------|--------|
| | pass/fail |
```

---

## qa-implementation-pass.md

```markdown
# QA PASS: Implementation

**Task:** <APP-XXX>-<task-name>
**backlog_ticket:** APP-XXX
**Tests run:** …
**Diff scope reviewed:** …
**Ticket AC:** all checked / noted exceptions
```

---

## human-test-plan.md

_Manual playtest for the human after Stage 7 commit. Not a substitute for pytest — both matter._

```markdown
# Human Playtest Plan: <APP-XXX>-<task-name>

**backlog_ticket:** APP-XXX
**Commit:** `<git rev or "pending">`
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

## Prerequisites

- [ ] API keys / config the feature needs (or document "mock/offline OK")
- [ ] Fresh or known save state (e.g. `new game` vs Continue)
- [ ] Any log path to watch: `app/logs/session-YYYY-MM-DD.jsonl`

## Test cases

### TC-1: <short name> (maps to AC / R1)

**Goal:** <what behavior this proves>

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Launch app (`python main.py`) | Window opens, no traceback | [ ] |
| 2 | … | … | [ ] |

**Failure signals:** <wrong UI, silent no-op, wrong log event, crash>

### TC-2: <edge or regression case>

…

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

<flaky steps, known limitations>
```
