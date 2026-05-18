# Dev Team — Artifact Templates

Write all artifacts under `.dev-team/works/<slug>/artifacts/`.

## Research brief (`research.md`)

```markdown
## Research brief

### Request
[One sentence]

### Findings
- [File/path references]

### Risks & unknowns
- …

### Recommendation
[Proceed / clarify / blocked]
```

## Product spec (`spec.md`)

**Required:** `### Implementation allowlist` with at least one glob path before `approve spec`.

```markdown
## Product spec

### Problem
…

### Scope
**In:** … | **Out:** …

### Acceptance criteria
- [ ] AC-1: [testable]
- [ ] AC-2: [testable]

### Priority
**Must:** … | **Should:** … | **Could:** …

### Approach
…

### Implementation allowlist
- docs/design/**
- src/feature/**
```

Docs-only work example:

```markdown
### Implementation allowlist
- docs/**
- Tomb Dust Game System.md
```

## Dev handoff (`dev-handoff.md`)

```markdown
## Dev handoff

### Changes
- `path/to/file` — [what changed]

### AC mapping
| AC | How implemented |
|----|-----------------|
| AC-1 | … |

### Verify
[commands or steps]

### Known gaps
…
```

## QA spec feedback (`qa-spec-feedback.md`)

Written by QA on `qa-reject spec`. PM must resolve every **B-N** before `submit spec`.

```markdown
## QA spec review

### Verdict
Fail

### Blockers
- B-1: [spec standard violated — e.g. AC-2 not testable]

### Standards checklist
| Standard | Status | Notes |
|----------|--------|-------|
| Scope In/Out defined | Pass/Fail | … |
| AC-N testable | Pass/Fail | … |
| Must/Should/Could | Pass/Fail | … |
| Implementation allowlist present | Pass/Fail | … |
```

## QA dev feedback (`qa-dev-feedback.md`)

Written by QA on `qa-reject dev`. Developer must fix every blocker and spec mismatch.

```markdown
## QA dev review

### Verdict
Fail

### Blockers
- B-1: [implementation bug or missing AC]

### Spec mismatches
- AC-1: [expected per spec vs actual in code]
```

## QA report (`qa-report.md`)

```markdown
## QA report

### Summary
[Pass / Pass with notes / Fail]

### Acceptance criteria
| AC | Status | Evidence |
|----|--------|----------|
| AC-1 | Pass/Fail | … |

### Issues
| Severity | Issue | Action taken |
|----------|-------|--------------|

### Sign-off recommendation
[Ready for user ship gate / blocked on …]
```

## Human gate prompt (orchestrator)

When entering `RESEARCH_GATE`, `SPEC_GATE`, `DEV_GATE`, or `QA_GATE`:

```markdown
---
## Human gate — [Research brief | Product spec | Implementation | QA report]

**Current state:** `SPEC_GATE`
**Summary:** [2–4 sentences]

**Reply with one of:**
| Command | Effect |
|---------|--------|
| `approve spec` | → `DEV` |
| `revise spec: <feedback>` | → `SPEC` |
| `reject to research` | From `SPEC_GATE` only → `RESEARCH` |
| `abort` | → `ABORTED` |

_Aliases: "lgtm", "looks good" count as approve for the gate shown only._
---
```

Full approve/reject matrix: [state-machine.md](state-machine.md).
