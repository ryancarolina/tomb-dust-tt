# Dev Team — Artifact Templates

Copy sections into `tmp/<task-name>/` files. Replace placeholders.

---

## status.md

```markdown
# Pipeline: <task-name>

**Goal:** <one line>
**Started:** <date>
**Current stage:** research | spec | plan | implement | impl-qa | drift | complete | blocked

## Checklist

- [ ] Research → research-brief.md (registry_gap set)
- [ ] PM spec draft (domain spec created if approved)
- [ ] QA spec PASS (round __/3)
- [ ] Dev plan draft
- [ ] QA plan PASS (round __/3)
- [ ] workstreams.md + parallel implementation
- [ ] QA implementation PASS (round __/3)
- [ ] Drift check

## Blockers

_None._

## Links

- research-brief.md
- spec.md
- plan.md
```

---

## research-brief.md

```markdown
# Research Brief: <task-name>

**Date:** <date>
**Question:** <what we need to answer>

**registry_gap:** false | true

## Registry gap justification

<If false: cite owning spec/doc paths from tmp/app-master-spec.md registry or build/docs/engine-integration.md.>
<If true: why no row fits; proposed domain spec or doc path, e.g. tmp/app-my-feature-spec.md.>

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

## spec.md (task-local)

```markdown
# Spec: <task-name>

**Status:** draft | qa-review | approved
**registry_gap:** <echo from research-brief; PM may correct with note>
**Domain specs touched:** <paths or none>

## Proposed domain spec

_Fill only when `registry_gap: true`. Delete section when false._

| Field | Value |
|-------|--------|
| Proposed file | `tmp/app-<domain>-spec.md` or `build/docs/engine-integration.md` (canon only) |
| Registry row | <domain name — added to app-master-spec on create> |
| Owns | <code paths> |
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

## Affected paths

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

**Task:** <task-name>
**Verdict:** FAIL
**Reviewer role:** QA (adversarial)

## Findings

### SPEC-001 — blocker

- **Location:** …
- **Issue:** …
- **Implementation gap:** …
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

**Task:** <task-name>
**Round:** <N>
**domain_spec_creation:** approved | not_needed | rejected

**Verified:**

- [ ] Acceptance criteria testable
- [ ] Code traces match repo (plan only)
- [ ] AGENTS.md / canon compliance
- [ ] Tests/commands listed
- [ ] registry_gap matches reality (spec only)
- [ ] If registry_gap true: domain spec exists or approved § Proposed domain spec + master registry update planned (spec only)
- [ ] If registry_gap false: no orphan long-lived app/ behavior in task-only spec (spec only)

**Notes:** <optional>
```

---

## New domain spec (after QA approved)

Create `tmp/app-<domain>-spec.md` with sections from [app-master-spec.md](../../tmp/app-master-spec.md) § Domain spec template, then add registry row:

```markdown
| <Domain name> | [`app-<domain>-spec.md`](app-<domain>-spec.md) | `<owned app paths>` | `<engine/canon links>` |
```

---

## plan.md

```markdown
# Implementation Plan: <task-name>

**Status:** draft | qa-review | approved
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
2. …

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
# Workstreams: <task-name>

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | | — | | tests green |
| WS2 | | WS1? | | |

## WS1 — <name>

**Scope:** …
**Prompt seed for Task subagent:** …
```

---

## qa-implementation-report.md

```markdown
# QA Report: Implementation

**Task:** <task-name>
**Verdict:** FAIL

## Findings

### IMPL-001 — blocker

- **Location:** `file:line`
- **Issue:** …
- **Spec/plan reference:** …
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

**Task:** <task-name>
**Tests run:** …
**Diff scope reviewed:** …
```

---

## drift-check.md

```markdown
# Drift Check: <task-name>

**Verdict:** PASS | UPDATED

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| | no | — |
| | yes | updated §… changelog entry |

## Notes

…
```
