---
name: dev-team
description: >-
  Multi-agent development pipeline for this codebase: research, PM spec,
  dev implementation plan, adversarial QA loops, parallel implementation,
  and spec drift checks. Use when doing non-trivial development, features,
  refactors, or when the user invokes @dev-team or asks for the dev-team
  workflow.
---

# Dev Team

Orchestrates four roles — **Research**, **PM**, **Dev**, **QA** — in sequence with adversarial QA gates. All task artifacts live under **`tmp/<task-name>/`** (gitignored). Read [agents.md](agents.md) for role behavior and [templates.md](templates.md) for file formats.

## When to use

- Non-trivial code changes (multi-file, new behavior, cross-tree `app/` / `play/` / `build/`)
- User says `@dev-team`, "dev team", or wants spec → plan → implement with QA

Skip for trivial one-line fixes unless the user explicitly requests the full pipeline.

## Task setup

1. Derive **`task-name`**: lowercase kebab-case from the user request (e.g. `combat-turn-enforcement`, `stash-vendor-gates`). Ask once if ambiguous.
2. Create **`tmp/<task-name>/`** and **`tmp/<task-name>/status.md`** (pipeline checklist — copy from [templates.md](templates.md)).
3. Record the user’s goal and constraints at the top of `status.md`.

**Do not** commit `tmp/` artifacts unless the user asks.

## Pipeline overview

```text
Research → PM (spec) ⇄ QA (≤3) → Dev (plan) ⇄ QA (≤3) → Dev (parallel impl) → QA (code) → QA (drift)
```

Stop and **ask for human input** when any QA loop exhausts 3 iterations without **PASS**, or when scope/blockers need a product decision.

## Stage 1 — Research agent

**Goal:** Ground the task in the real codebase.

1. Explore relevant trees (`app/`, `play/tomb_gm/`, `build/`, `tmp/`, docs).
2. Trace code paths, tests, configs, and existing specs/plans.
3. Read [AGENTS.md](../../AGENTS.md) and any matching `tmp/app-*-spec.md` or `tmp/app-master-spec.md`.
4. Write **`tmp/<task-name>/research-brief.md`** using the template in [templates.md](templates.md).
5. Set **`registry_gap`** in the brief (required field) — see [Domain spec creation](#domain-spec-creation-registry_gap) below.

Update `status.md`: Research ✅ (note `registry_gap: true|false`).

## Domain spec creation (`registry_gap`)

Research **must** declare `registry_gap` in `research-brief.md`:

| Value | Meaning |
|-------|---------|
| **`false`** | At least one existing domain spec or doc clearly owns this work (`tmp/app-*-spec.md`, `build/docs/engine-integration.md`). |
| **`true`** | Long-lived behavior has **no** registry owner; task-only spec would violate drift policy ([AGENTS.md](../../AGENTS.md) — no orphan code). |

### PM rules

| `registry_gap` | PM action |
|----------------|-----------|
| **`false`** | Update matching domain spec(s). `tmp/<task-name>/spec.md` = summary + pointers only. **Do not** create `tmp/app-*-spec.md`. |
| **`true`** | Propose new domain spec path(s) in task `spec.md` (e.g. `tmp/app-<domain>-spec.md`). Create files **only after** spec QA confirms task-only spec is insufficient (see QA gate). |

**New `tmp/app-*-spec.md` requires all:**

1. `registry_gap: true` in research brief, with justification.
2. QA spec **PASS** explicitly records `domain_spec_creation: approved` (or `not_needed`).
3. PM adds a row to [tmp/app-master-spec.md](../../tmp/app-master-spec.md) spec registry and uses the [domain spec template](../../tmp/app-master-spec.md) (§ Domain spec template).
4. Task `spec.md` links to the new file; no duplicate long-form truth in the task folder.

**Canon (`build/systems/`, `build/docs/`):** extend `engine-integration.md` or systems markdown when behavior is durable; app work stays in `tmp/app-*-spec.md`.

**Human input** if Research and PM disagree on `registry_gap`, or QA rejects creation after 3 rounds.

## Stage 2 — PM agent + QA (spec)

### PM writes spec

1. Read `research-brief.md`, [AGENTS.md](../../AGENTS.md), and the codebase areas cited in the brief.
2. Honor **`registry_gap`** from the brief (PM may set `registry_gap: false` only with evidence in `spec.md` that an existing owner was missed; QA must agree).
3. **Spec target:**
   - **`registry_gap: false`** — update existing domain spec(s); `tmp/<task-name>/spec.md` = summary + pointers.
   - **`registry_gap: true`** — draft new domain spec content in task `spec.md` § Proposed domain spec; create `tmp/app-<domain>-spec.md` (and registry row) **after QA approval** on the same pass or immediately before spec PASS.
   - **One-off / thin task** — if work is truly ephemeral, Research should have set `registry_gap: false` and scoped to an existing owner; task-only `spec.md` is allowed only when QA records `domain_spec_creation: not_needed` and drift risk is none (no new long-lived `app/` behavior).
4. Spec must include: problem, scope in/out, acceptance criteria, test commands, affected paths, changelog stub, `registry_gap` echo.

Update `status.md`: PM spec draft ✅.

### QA reviews spec (adversarial)

Act as **QA agent** ([agents.md](agents.md#qa-agent)):

- Hunt defects, missing acceptance criteria, contradictions with AGENTS.md / canon, and **implementation gaps** (unspecified edge cases, migration, rollback, tests).
- **Registry / drift gate (required):**
  - If `registry_gap: true` and long-lived `app/` (or engine/canon) behavior is in scope → **FAIL** unless a domain spec (or `build/docs/` owner) exists or is approved in § Proposed domain spec with registry update planned.
  - If `registry_gap: false` but task `spec.md` duplicates domain truth → **FAIL** (move detail to domain spec).
  - If `registry_gap: true` but work fits an existing registry row → **FAIL** (wrong gap; use update-in-place).
  - Record verdict in pass report: `domain_spec_creation: approved | not_needed | rejected`.
- **PASS** → write `tmp/<task-name>/qa-spec-pass.md` (short sign-off + `domain_spec_creation`) → Stage 3.
- **FAIL** → write **`tmp/<task-name>/qa-spec-report-<n>.md`** (`n` = 1..3).

### PM fixes spec (loop ≤3)

1. PM reads the latest `qa-spec-report-*.md`.
2. PM updates the spec(s); append changelog notes in domain specs when touched.
3. QA re-reviews. Repeat until **PASS** or **3 failed rounds**.

If still failing after round 3: set `status.md` to **BLOCKED — spec QA**, summarize open issues, **stop for human input**.

## Stage 3 — Dev agent + QA (plan)

### Dev writes plan

1. Read `research-brief.md`, approved spec(s), and codebase.
2. **Deep code-path traces** for every change area (callers, callees, state, DB, tests).
3. Write **`tmp/<task-name>/plan.md`** — file-level steps, order of operations, test plan, risks ([templates.md](templates.md)).

For **`app/`** work: plan must reference which `tmp/app-*-spec.md` entries will be updated and which pytest targets prove done.

Update `status.md`: Dev plan draft ✅.

### QA reviews plan (adversarial, code-level)

- Re-trace code paths independently; verify plan matches repo reality.
- **PASS** → `tmp/<task-name>/qa-plan-pass.md` → Stage 4.
- **FAIL** → **`tmp/<task-name>/qa-plan-report-<n>.md`** (≤3 rounds), Dev revises `plan.md` each round.

If still failing after round 3: **BLOCKED — plan QA** → human input.

## Stage 4 — Parallel implementation

### Dev splits work streams

1. From `plan.md`, define **2+ disjoint streams** when possible (e.g. engine vs app vs tests).
2. Write **`tmp/<task-name>/workstreams.md`**: stream id, owner scope, files, dependencies, done definition.

### Run streams in parallel

Use the **Task** tool — **one message, multiple Task calls** — `subagent_type: generalPurpose` (or `explore` for read-only recon).

Each subagent prompt must include:

- Absolute paths to `research-brief.md`, `spec.md` / domain spec paths, `plan.md`, and their stream section
- [AGENTS.md](../../AGENTS.md) constraints for touched trees
- Explicit deliverables and tests to run before reporting done

Parent agent:

- Waits for all streams
- Resolves merge conflicts and cross-stream integration
- Runs tests from spec/plan

Update `status.md` per stream.

## Stage 5 — QA final implementation

QA (adversarial) reviews **actual diffs**:

- Correctness, edge cases, security, test gaps, spec/plan compliance
- **PASS** → `tmp/<task-name>/qa-implementation-pass.md`
- **FAIL** → **`tmp/<task-name>/qa-implementation-report.md`** → Dev fixes → QA re-review (≤3 rounds total for this stage)

Exhausted rounds → **BLOCKED — implementation QA** → human input.

## Stage 6 — Spec drift check

After implementation PASS:

1. QA compares codebase to all specs touched (task + domain).
2. If **drift** (code ≠ spec): QA **updates specs** to match intentional final behavior, with changelog entry — not silent drift.
3. Write **`tmp/<task-name>/drift-check.md`** (PASS or list of spec updates made).

Mark pipeline **COMPLETE** in `status.md`.

## Orchestration rules

| Rule | Detail |
|------|--------|
| Role separation | Do not skip Research before PM; do not implement before plan QA PASS |
| QA mindset | Assume defects exist; require evidence (file:line, trace) for findings |
| Evidence | Research/plan/QA reports cite repo paths and symbols |
| Tests | Run commands listed in spec/plan; report pass/fail in QA sign-offs |
| Scope | No drive-by refactors; no canon edits in `play/workspace/` for content tasks |
| App drift | Any `app/` change updates matching `tmp/app-*-spec.md` per master spec registry |
| New domain spec | Only when `registry_gap: true` + QA `domain_spec_creation: approved` + master registry updated |

## Quick artifact index

| File | Owner |
|------|--------|
| `research-brief.md` | Research |
| `spec.md` (+ domain specs) | PM |
| `qa-spec-report-*.md` / `qa-spec-pass.md` | QA / PM loop |
| `plan.md` | Dev |
| `qa-plan-report-*.md` / `qa-plan-pass.md` | QA / Dev loop |
| `workstreams.md` | Dev |
| `qa-implementation-report.md` / `qa-implementation-pass.md` | QA / Dev |
| `drift-check.md` | QA |
| `status.md` | Orchestrator |

## Tomb Dust pointers

| Area | Read first |
|------|------------|
| Project rules | [AGENTS.md](../../AGENTS.md) |
| App domains | [tmp/app-master-spec.md](../../tmp/app-master-spec.md) |
| Engine bridge | [tmp/app-gamebridge-spec.md](../../tmp/app-gamebridge-spec.md) · [build/docs/engine-integration.md](../../build/docs/engine-integration.md) |
| Canon / grid | `build/data/av-grid/`, `build/systems/` |
| Play entry | [app/README.md](../../app/README.md) |

## Additional resources

- Role definitions: [agents.md](agents.md)
- Document templates: [templates.md](templates.md)
