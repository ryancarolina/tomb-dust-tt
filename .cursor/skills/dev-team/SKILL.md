---
name: dev-team
description: >-
  Multi-agent development pipeline: orchestrator dispatches real Task subagents
  for Research, PM, Dev, and QA with adversarial gates, backlog tickets, and
  tmp/backlog/runs artifacts. Use when the user invokes @dev-team or structured
  dev-team delivery on this codebase.
---

# Dev Team

The agent that invokes `@dev-team` is the **Orchestrator**. It **does not** perform Research, PM, Dev, or QA work inline — it **dispatches** each role as a **Task subagent**, announces every dispatch to the user, waits for results, and updates `status.md`.

Specialist behavior: [agents.md](agents.md) · Artifact formats: [templates.md](templates.md)

All pipeline artifacts live under **`tmp/backlog/runs/<APP-XXX>-<task-name>/`**. Every run **must** claim a backlog ticket first (Stage 0).

## Orchestrator model (mandatory)

| Who | Does what |
|-----|-----------|
| **Orchestrator** (you, parent) | Stage 0 claim, `status.md`, **announce + dispatch** subagents, merge outcomes, Stage 7 commit, user updates |
| **Research / PM / Dev / QA** | Task subagents only — explore, write artifacts, code, review |

### Dispatch rules

1. **Announce before every dispatch** — user-visible message, then call the Task tool in the **same** turn:

   ```text
   **Dispatching <Role> agent** — APP-XXX · <task-name>
   Stage: <e.g. spec QA round 2>
   Deliverable: <file(s)>
   ```

2. **One role per Task** — Research, PM, Dev (plan), QA (spec), QA (plan), etc. are separate dispatches unless Stage 4 parallel impl (multiple Dev Tasks in one message).

3. **Do not impersonate roles** — no “Role: Research” prose without a Task; no writing `research-brief.md` yourself while skipping dispatch.

4. **Subagent prompt must include** (see [agents.md § Dispatch prompts](agents.md#dispatch-prompts)):
   - Role name, `backlog_ticket`, absolute `run-folder` path, ticket path, domain spec path
   - Deliverables + [AGENTS.md](../../AGENTS.md) constraints
   - **Reflection** (internal before return — no file; see below)
   - Stage 6 drift: **Drift check** block in return (no file; see below)
5. **Subagent return** — after reflect→retry loop (≤3 attempts): deliverable paths + **Reflection** block (`Attempts`, `Handoff`); Stage 6 drift adds **Drift check** block (no file).
6. **After subagent returns** — read deliverables + **Reflection** block (+ **Drift check** at Stage 6). If `Handoff: needs human input`, stop lane and ask user. Else update `status.md`, next dispatch.

7. **Subagent type:** `generalPurpose` (default). Use `explore` only for read-only recon with no file writes.

### Reflection (internal — no artifact, retry up to 3)

Before returning, each subagent **reflects privately** — confirm the job is done and nothing was missed. **Do not** write `reflection-*.md` or any reflection file.

**Reflect → retry loop (max 3 attempts per dispatch):**

1. Do the work for this dispatch’s deliverable(s).
2. **Reflect** — did I complete the task correctly? Anything missed?
3. If **yes, complete** → return to orchestrator with **Reflection** block (`Handoff: ready`).
4. If **gaps remain** and **attempt < 3** → fix the gaps, go to step 2.
5. If **gaps remain** after **attempt 3** → return with **Reflection** block (`Handoff: needs human input`) — list blockers; do not pretend done.

Count attempts **within this dispatch only** (one PM spec dispatch = up to 3 self-retries before escalating).

Include in the return message:

- **Attempts:** 1 | 2 | 3
- **Completed** — deliverables written
- **Self-critique** — what might be thin or wrong
- **Missed?** — checklist (scope, AC, ticket, canon)
- **Handoff** — `ready for next gate` | `needs human input` (required if attempt 3 and incomplete)

The orchestrator uses this block when planning the next gate. If **Handoff: needs human input**, orchestrator stops the lane and asks the user — do not advance to the next stage.

### Drift check (Stage 6 only — no artifact)

Stage 6 QA still **syncs domain specs and ticket AC in the repo**, but **does not** write `drift-check.md` or `reflection-qa-drift.md`.

Return message includes a **Drift check** block (see [templates.md](templates.md)): **Verdict** (`PASS` | `UPDATED` | `FAIL`), specs compared, domain spec updates, **Release ready**. Orchestrator runs `release --done` only when **Release ready: yes** and drift **Verdict** is not `FAIL`.

## When to use

- Non-trivial code changes (multi-file, new behavior, cross-tree `app/` / `play/` / `build/`)
- User says `@dev-team`, "dev team", or wants spec → plan → implement with QA
- Any work that needs a backlog ticket under [tmp/backlog/README.md](../../tmp/backlog/README.md)

**Always search, schedule, and claim backlog tickets before Stage 1.** Skip the full pipeline only for trivial fixes with an explicit ticket or documented exception ([tomb-dust-backlog.mdc](../../.cursor/rules/tomb-dust-backlog.mdc)).

## Stage 0 — Backlog search, schedule, claim (required)

**Goal:** Pick up to **3 tickets**, respect **priority** (P0 → P1 → P2) and **dependencies**, authorize edits via batch session.

### Shell (Windows / PowerShell)

This repo is often edited on **PowerShell 5.x**. **Do not** chain CLI steps with `&&` — it fails with `InvalidEndOfLine`. Run **one command per Shell invocation** (or use `;` only when both must run in one line).

If any Stage 0 command exits non-zero or prints `error:` → **STOP**. Report to the user. **Do not** dispatch Research/Dev or hand-create run folders.

### “Build them” ≠ skip the pipeline

User verbs like **build**, **implement**, or **ship** still mean the **full** dev-team pipeline (Stages 1–7). They do **not** authorize jumping to Stage 4 Dev, skipping Research/PM/plan QA, or orchestrator-written artifacts.

### 0a — Search backlog (orchestrator)

**Pickable tickets only:** status **`open`**. When auto-selecting work, **never** pick `in_progress`, `done`, or `cancelled`.

```bash
python tmp/backlog/claim_ticket.py search --open-only
python tmp/backlog/claim_ticket.py search --open-only --priority P0 --q creation
```

`--open-only` (alias `--pickable-only`) returns **only `open`** tickets — not `in_progress` (already claimed elsewhere) and not closed (`done` / `cancelled`).

Read JSON `tickets[]`: `id`, `priority`, `status`, `blocked_by`, `title`, `path`. Select up to 3 from this list by priority then dependencies.

| Status | Auto-pick for new batch? |
|--------|---------------------------|
| `open` | **Yes** |
| `in_progress` | **No** — finish or resume that lane separately (`claim APP-XXX --resume` / `claim-batch --resume`) |
| `done` / `cancelled` | **No** — closed |

To **inspect** in-flight or closed tickets (not to claim new work): `search --status in_progress` or `--status done` without `--open-only`.

### 0b — Schedule batch (orchestrator)

Pick **≤3** ticket IDs from the **open-only** search results (do not add `in_progress` or closed IDs unless the user explicitly asked to **resume** one lane with `claim-batch --resume`). Preview dependency order **before** claiming:

```bash
python tmp/backlog/claim_ticket.py schedule APP-001 APP-002 APP-004
```

Use output:

| Field | Meaning |
|-------|---------|
| `impl_waves` | Implementation order layers. Tickets in the same `parallel` array may implement together. |
| `blocked_by` | Hard deps within the batch (from ticket ## Dependencies). |
| `warnings` | External deps not done — finish or add those tickets to the batch. |

**Example:** If `APP-004` has `APP-002 | blocks this ticket`, schedule yields wave 1 `[APP-001, APP-002]` and wave 2 `[APP-004]`. Stages 1–3 (research/spec/plan) may run on all three in parallel; **Stage 4 implementation** for `APP-004` starts only after `APP-002` pipeline **COMPLETE** (ticket `done`).

Record schedule in the **batch board** file (required naming — see below) and link it from each ticket `status.md` (see [templates.md](templates.md#batch-board)).

**Batch board filename (required):** `tmp/backlog/runs/batch-board-<APP-XXX>[-<APP-YYY>[-<APP-ZZZ]].md` — ticket IDs **sorted**, e.g. `batch-board-APP-069-APP-070-APP-072.md`. Never use date-only names like `batch-board-2026-05-20.md`. `claim-batch` prints the path in JSON as `batch_board`.

### 0c — Claim batch (orchestrator)

Task names use **repeated `--task` flags** — never positional `APP-XXX=kebab-name` after ticket IDs (argparse error or “at most 3 tickets”).

**PowerShell (one line, no `&&`):**

```powershell
python tmp/backlog/claim_ticket.py claim-batch APP-110 APP-111 APP-085 --dev-team --task APP-110=breley-sewers-av-grid --task APP-111=tutorial-hazard-monsters --task APP-085=quest-system
```

**Bash:**

```bash
python tmp/backlog/claim_ticket.py claim-batch APP-001 APP-002 APP-004 \
  --dev-team \
  --task APP-001=fix-site-edges --task APP-002=creation-drift --task APP-004=advancedto-log
```

Wrong (will fail):

```text
claim-batch APP-110 APP-111 APP-085 APP-111=tutorial-hazard-monsters
schedule APP-110 APP-111 APP-085 && python tmp/backlog/claim_ticket.py claim-batch ...
```

Creates **`tmp/.active-batch.json`** (≤3 tickets), **`tmp/.active-ticket.json`** (focus), one **`tmp/backlog/runs/APP-XXX-<task>/`** per ticket, and **`pipeline-manifest.json`** when `--dev-team` is set.

After each gate:

```bash
python tmp/backlog/claim_ticket.py pipeline-set-stage APP-XXX spec_qa --gate spec_qa_pass
python tmp/backlog/claim_ticket.py pipeline-check APP-XXX
```

```bash
python tmp/backlog/claim_ticket.py batch-status   # inspect batch + schedule
python tmp/backlog/claim_ticket.py focus APP-002  # before editing that ticket's files
python tmp/backlog/claim_ticket.py impl-check APP-004  # before Stage 4 on APP-004
```

Single-ticket work still works: `python tmp/backlog/claim_ticket.py APP-XXX --task <name>` (batch of 1).

### 0d — Per-ticket setup

For **each** claimed ticket: copy [`templates.md`](templates.md) **`status.md`** into that ticket's run folder (replace empty touch file); fill ticket + domain spec fields.

**Do not** dispatch Research until claim-batch succeeds, `pipeline-check` shows manifests exist, and every `status.md` is initialized.

### Parallel batch orchestration (≤3 tickets)

A **batch** is up to **3 independent lanes**. Each lane is a full pipeline (Stages 1–7) for one **APP-XXX**. The batch board tracks all lanes; **never** merge lanes into one spec, one commit, or one playtest doc.

| Rule | Detail |
|------|--------|
| Max in flight | **3** tickets in `tmp/.active-batch.json` |
| Pickable | Auto-select **`open`** only — not `in_progress` / `done` / `cancelled` |
| Priority | Among `open` tickets, prefer P0 → P1 → P2 when filling the batch |
| Dependencies | `\| APP-002 \| blocks this ticket \|` → ticket **cannot enter Stage 4** until APP-002 is **`done`** (`impl-check`) |
| Lane isolation | One `run-folder/`, one `status.md`, one `human-test-plan.md`, **one git commit** per ticket |
| Batch board | Update `batch-board-APP-…-APP-….md` when any lane advances stage or gets a commit hash |

#### What may run in parallel

| Stages | Parallel across tickets? | How |
|--------|---------------------------|-----|
| **1–3** (research, spec, plan + QA gates) | **Yes** | Up to **3 Task dispatches in one message** (one per ticket), each prompt names **one APP-XXX** and one `run-folder` |
| **4** (implementation) | **Only within the same `impl_waves` row** | Wave 1 tickets may impl together; wave 2 waits until blockers are **`done`** (Stages 6–7 finished for blocker) |
| **5–7** (impl QA, drift, release, commit, playtest) | **Per ticket, in order** | Finish close-out for lane A before starting Stage 6 on lane B **if they touch the same files**; otherwise may overlap **after** each lane’s Stage 5 PASS |

**Same-file guard:** If two open lanes list overlapping **Expected files**, do **not** implement or commit them in parallel — complete one lane through **Stage 7a** first, then the next.

#### Parallel dispatch pattern (Stages 1–3)

```text
**Dispatching Research agent ×3** — APP-069, APP-070, APP-072
→ one message, three Task calls (each prompt: single ticket + run-folder)
```

Do **not** combine two tickets in one subagent prompt. Do **not** skip `focus APP-XXX` before edits for that ticket.

#### Per-lane close-out (Stages 6–7) — required order

For **each** ticket that reached Stage 5 PASS, close the lane **before** claiming the batch is fully done:

1. **Dispatching QA agent** — drift check (this ticket only)
2. `python tmp/backlog/claim_ticket.py release APP-XXX --done`
3. **Orchestrator** — **one git commit for this ticket only** (Stage 7a) — see below
4. **Dispatching QA agent** — `human-test-plan.md` in **this** `run-folder`
5. Update this ticket’s `status.md` + batch board row (stage **complete**, commit hash)
6. Repeat for the next lane in the batch

**Never** one commit referencing multiple APP-XXX IDs. **Never** one `human-test-plan.md` covering multiple tickets.

**Batch COMPLETE** when every lane in the batch board is **complete** (or explicitly **blocked** / deferred with user approval).

**On pipeline COMPLETE per ticket:** drift → release → **git commit (that ticket only)** → human playtest plan. Mandatory unless the user opted out of commit for the whole session.

## Task setup

1. Derive **`task-name`**: lowercase kebab-case from the user request (e.g. `deterministic-creation-tables`). Ask once if ambiguous.
2. **`run-folder`** = `tmp/backlog/runs/<APP-XXX>-<task-name>/` (created by `claim_ticket.py`).
3. Create **`run-folder/status.md`** (pipeline checklist — copy from [templates.md](templates.md)).
4. Record the user’s goal, **backlog ticket ID**, and constraints at the top of `status.md`.

**Do not** commit `tmp/.active-ticket.json` (session-local). Run artifacts may stay in git unless the user prefers otherwise.

### Forbidden artifact paths

**Never** create or write pipeline artifacts under:

- `.dev-team/` (any path, e.g. `.dev-team/artifacts/`, `.dev-team/session.json`)
- Loose files directly under `tmp/` (outside `backlog/runs/…` and domain specs)
- Pointers from the run folder to out-of-tree copies (“see `.dev-team/…`”)

All Research / PM / Dev / QA outputs go **only** in **`tmp/backlog/runs/<APP-XXX>-<task-name>/`**. Session state belongs in `run-folder/status.md`, not a separate `.dev-team/session.json`.

## Pipeline overview

```text
Stage 0: search --open-only → schedule → claim-batch → batch-board-APP-…-APP-….md
Stages 1–3: up to 3 lanes in parallel (one Task per ticket per role)
Stage 4: by impl_waves only (impl-check each ticket first)
Stage 5: per lane
Stages 6–7: per lane, sequential close — drift → release → commit (1 ticket) → playtest
Batch done when every lane row is complete on the batch board
```

Stop and **ask for human input** when any QA loop exhausts 3 iterations without **PASS**, or when scope/blockers need a product decision.

## Stage 1 — Research agent

**Goal:** Ground the task in the real codebase.

**Orchestrator:**

1. Announce: **Dispatching Research agent**.
2. Task subagent → deliver `research-brief.md` ([agents.md](agents.md#research-agent)).
3. Verify brief exists; read return **Reflection** block; update `status.md` (Stage 0 ✅, Research ✅, `registry_gap` noted).

**Research subagent** (not orchestrator) explores code, traces paths, reads AGENTS.md + domain spec, writes the brief per [templates.md](templates.md).

## Domain spec creation (`registry_gap`)

Research **must** declare `registry_gap` in `research-brief.md`:

| Value | Meaning |
|-------|---------|
| **`false`** | Ticket **Domain spec** (or `build/docs/engine-integration.md`) clearly owns this work. |
| **`true`** | Long-lived behavior has **no** registry owner; task-only spec would violate drift policy ([AGENTS.md](../../AGENTS.md) — no orphan code). |

### PM rules

| `registry_gap` | PM action |
|----------------|-----------|
| **`false`** | Update matching domain spec(s). `run-folder/spec.md` = summary + pointers only. **Do not** create `tmp/app-*-spec.md`. |
| **`true`** | Propose new domain spec path(s) in task `spec.md` (e.g. `tmp/app-<domain>-spec.md`). Create files **only after** spec QA confirms task-only spec is insufficient (see QA gate). |

**New `tmp/app-*-spec.md` requires all:**

1. `registry_gap: true` in research brief, with justification.
2. QA spec **PASS** explicitly records `domain_spec_creation: approved` (or `not_needed`).
3. PM adds a row to [tmp/app-master-spec.md](../../tmp/app-master-spec.md) spec registry and uses the [domain spec template](../../tmp/app-master-spec.md) (§ Domain spec template).
4. Task `spec.md` links to the new file; no duplicate long-form truth in the run folder.

**Canon (`build/systems/`, `build/docs/`):** extend `engine-integration.md` or systems markdown when behavior is durable; app work stays in `tmp/app-*-spec.md`.

**Human input** if Research and PM disagree on `registry_gap`, or QA rejects creation after 3 rounds.

## Stage 2 — PM agent + QA (spec)

### PM writes spec

**Orchestrator:** announce **Dispatching PM agent** → Task → verify `spec.md` (+ domain spec updates) → `status.md` PM draft ✅.

**PM subagent:** [agents.md § PM](agents.md#pm-agent) — honor `registry_gap`, write `run-folder/spec.md`, update domain specs as required.

### QA reviews spec (adversarial)

**Orchestrator:** announce **Dispatching QA agent** (spec review round *N*) → Task → read `qa-spec-pass.md` or `qa-spec-report-<n>.md` + return **Reflection** block.

**QA subagent** ([agents.md § QA](agents.md#qa-agent)): ticket gate, registry/drift gate, adversarial review — **PASS** or **FAIL** per existing rules.

### PM fixes spec (loop ≤3)

On **FAIL:** orchestrator announces **Dispatching PM agent** (revision round *N*) with path to latest `qa-spec-report-*.md` → PM Task → then **Dispatching QA agent** again. Max 3 QA rounds.

If still failing after round 3: **BLOCKED — spec QA** → human input.

## Stage 3 — Dev agent + QA (plan)

### Dev writes plan

**Orchestrator:** announce **Dispatching Dev agent** (plan) → Task → `plan.md` → status Dev plan draft ✅.

**Dev subagent:** deep code-path traces, `plan.md` ⊆ ticket **Expected files** ([agents.md § Dev](agents.md#dev-agent)).

### QA reviews plan (adversarial, code-level)

**Orchestrator:** announce **Dispatching QA agent** (plan review round *N*) → Task → pass/report + return **Reflection** block.

**QA subagent:** independent traces, ticket scope gate — existing PASS/FAIL rules.

On **FAIL:** **Dispatching Dev agent** (plan revision) → **Dispatching QA agent** (≤3 rounds). Round 3 fail → **BLOCKED — plan QA**.

## Stage 4 — Parallel implementation

**Before any ticket enters Stage 4:** `python tmp/backlog/claim_ticket.py impl-check APP-XXX` must return `"allowed": true`. If false, finish the **blocking ticket’s lane** through Stage 7a (or remove it from the batch) before starting impl on the dependent ticket.

**Batch:** Only tickets in the **current `impl_waves` row** on the batch board may be in Stage 4 at the same time. Do not impl a wave-2 ticket until wave-1 blockers are **`done`** and released.

### Dev splits work streams

**Orchestrator:** announce **Dispatching Dev agent** (workstreams) → Task → `workstreams.md`.

**Dev subagent** defines streams in `workstreams.md` from `plan.md`.

### Run streams in parallel

**Orchestrator:** announce **Dispatching Dev agent** — **APP-XXX** (streams…) → Task(s) for **one ticket**. Multiple streams for the same ticket = multiple Tasks in one message. **Different tickets** in the same wave = multiple Tasks in one message (each prompt: single APP-XXX + `focus` set).

Each implementation subagent: **one ticket only** — stream section from that ticket’s `workstreams.md`, tests to run.

**Orchestrator after all return:** merge conflicts **within the ticket**, integration tests, read return **Reflection** blocks, update **that** `status.md` and batch board stage.

## Stage 5 — QA final implementation

**Orchestrator:** announce **Dispatching QA agent** (implementation review round *N*) → Task.

**QA subagent:** review diffs, run tests, map ticket AC — `qa-implementation-pass.md` or `qa-implementation-report.md`.

On **FAIL:** **Dispatching Dev agent** (fix) → **Dispatching QA agent** (≤3 rounds). Exhausted → **BLOCKED — implementation QA**.

## Stage 6 — Spec drift check + ticket close (per lane)

After **this ticket’s** implementation PASS (do not mix tickets in one drift report):

**Orchestrator:** announce **Dispatching QA agent** — **APP-XXX only** (drift) → Task. No drift artifact file.

**QA subagent:** compare code vs specs **for this ticket**; update domain spec changelog if needed; mark **this** ticket AC done. Return **Drift check** block + **Reflection** block in the message (see [templates.md](templates.md)).

**Orchestrator:** `python tmp/backlog/claim_ticket.py release APP-XXX --done` → then Stage 7 **for this ticket only**. Release archives the ticket markdown to `tmp/backlog/closed/`.

In a **batch**, repeat Stages 6–7 per lane. Updating a **shared** domain spec for ticket B is OK after ticket A’s commit if A already landed spec changes — avoid two lanes editing the same spec file at once.

**Lane COMPLETE** requires Stage 7 commit + `human-test-plan.md` for that ticket (unless user opted out of commits).

## Stage 7 — Git commit + human playtest plan (per lane, required)

**Goal:** One commit and one playtest doc **per ticket**. Clear the backlog `stop` hook and hand off manual PyGame checks.

### 7a — Commit (orchestrator, one ticket per commit)

**Batch rule:** **N tickets → up to N commits**, each scoped to **one APP-XXX**. No `APP-069, APP-070: …` combined messages.

1. Run commit **immediately after** `release APP-XXX --done` for that lane (before starting Stage 6 on the next lane if files overlap).
2. Stage **only this ticket’s** paths:
   - **This** ticket’s **Expected files** only
   - Domain spec(s) **this** ticket touched
   - **This** `tmp/backlog/app-xxx-*.md` (active root) or `tmp/backlog/closed/app-xxx-*.md` after archive
   - **This** `tmp/backlog/runs/APP-XXX-<task>/` (recommended)
3. **Never** stage another ticket’s paths in the same commit.
4. **Never** commit `tmp/.active-ticket.json`, `tmp/.active-batch.json`, secrets, or `play/workspace/`.
5. Message format — **exactly one** ticket ID in the subject:

   ```bash
   git add <paths for APP-XXX only>
   git commit -m "APP-XXX: <short summary>" -m "<tests run; spec synced>"
   ```

6. Record the hash in **this** `run-folder/status.md` and the batch board **Commit** column.
7. Verify: no unstaged `app/` paths remain **from this ticket** before moving to the next lane.

**Skip commit** only if the user opted out for the **whole session**; note in **this** `status.md`. Other lanes in the batch still commit unless user said otherwise.

### 7b — Human playtest plan (per lane)

**Orchestrator:** announce **Dispatching QA agent** — **APP-XXX** (human playtest) → Task → **this** `run-folder/human-test-plan.md`.

**QA subagent** writes playtest doc per [templates.md](templates.md). This is **playtest**, not pytest:

- Entry: [`app/README.md`](../../app/README.md) — `cd app && python main.py`
- **Test cases** the human runs in the PyGame client (menu actions, inputs, what to look for on screen / in `app/logs/*.jsonl` if relevant)
- Map each case to ticket acceptance criteria or spec requirements
- Include **pass/fail** checkboxes and **expected vs failure** signals

Derive cases from `spec.md`, ticket AC, and what actually shipped (e.g. creation flow, combat, travel, logging events).

### 7c — Close pipeline

1. Update `status.md`: Stage 6 ✅, Stage 7 ✅ (commit hash + link to `human-test-plan.md`).
2. Tell the user: commit hash, how to launch the app, and **run the human test plan** before considering the feature verified at the table.

**Why commit is last:** [`.cursor/hooks/backlog_ticket_gate.py`](../../.cursor/hooks/backlog_ticket_gate.py) `stop` handler warns when `app/` files appear in `git diff HEAD` without `tmp/.active-ticket.json`. Committing ticket-scoped `app/` changes removes that diff so the hook stays quiet after release.

## Orchestration rules

| Rule | Detail |
|------|--------|
| Real subagents | Research / PM / Dev / QA = Task dispatches; orchestrator does not do their work inline |
| Announce dispatches | User-visible **Dispatching {Role} agent** before every Task call |
| Reflection | Internal reflect→retry loop (≤3 attempts per dispatch); **Reflection** block in return — escalate human if still incomplete after 3 |
| Drift check | Stage 6 only — no file; **Drift check** block in QA return message; domain spec + ticket AC updates still land in repo |
| No backfill | Orchestrator **never** writes stage artifacts or calls `pipeline-set-stage --gate` to tick gates without a real subagent dispatch |
| Stop hook | Uncommitted `app/`/`build/`/`play/` with incomplete pipeline → run missing stages; **never** retroactively mark gates done |
| Ticket first | No Research without Stage 0 claim; hooks enforce `app/` edits |
| Role separation | Do not skip Research before PM; do not implement before plan QA PASS |
| QA mindset | Assume defects exist; require evidence (file:line, trace) for findings |
| Evidence | Research/plan/QA reports cite repo paths and symbols |
| Tests | Run commands listed in spec/plan/ticket; report pass/fail in QA sign-offs |
| Scope | No drive-by refactors; plan files ⊆ ticket Expected files |
| App drift | Any `app/` change updates matching `tmp/app-*-spec.md` when ticket closes |
| New domain spec | Only when `registry_gap: true` + QA `domain_spec_creation: approved` + master registry updated |
| Active session | `tmp/.active-ticket.json` set by `claim_ticket.py`; cleared on `release --done` |
| Stage 7 commit | **One commit per ticket**; subject is one `APP-XXX`; never squash a batch into one commit |
| Batch close | Stages 6–7 **per lane**; update batch board after each commit |
| Same-file batch | Overlapping Expected files → close lanes **sequentially** through 7a |
| Human playtest | `human-test-plan.md` in run folder — manual game steps, not headless pytest only |
| Artifact location | **Only** `tmp/backlog/runs/<APP-XXX>-<task>/` — never `.dev-team/` |
| Batch limit | ≤3 tickets via `claim-batch`; use `search --open-only` + `schedule` first |
| Pickable only | Auto-select **`open`** only — never `in_progress` / `done` / `cancelled` |
| Impl order | `impl_waves` from `schedule`; `impl-check` before Stage 4 per ticket |

## Quick artifact index

All paths relative to **`tmp/backlog/runs/<APP-XXX>-<task-name>/`**:

| File | Owner |
|------|--------|
| `status.md` | Orchestrator |
| `research-brief.md` | Research |
| `spec.md` (+ domain specs) | PM |
| `qa-spec-report-*.md` / `qa-spec-pass.md` | QA / PM loop |
| `plan.md` | Dev |
| `qa-plan-report-*.md` / `qa-plan-pass.md` | QA / Dev loop |
| `workstreams.md` | Dev |
| `qa-implementation-report.md` / `qa-implementation-pass.md` | QA / Dev |
| `human-test-plan.md` | QA (Stage 7) |

## Tomb Dust pointers

| Area | Read first |
|------|------------|
| Project rules | [AGENTS.md](../../AGENTS.md) |
| Backlog | [tmp/backlog/README.md](../../tmp/backlog/README.md) (active) · [closed/](../../tmp/backlog/closed/README.md) |
| Search | `python tmp/backlog/claim_ticket.py search --open-only` |
| Schedule | `python tmp/backlog/claim_ticket.py schedule APP-XXX APP-YYY` |
| Claim batch | `python tmp/backlog/claim_ticket.py claim-batch APP-XXX ...` |
| Claim one | `python tmp/backlog/claim_ticket.py APP-XXX --task <name>` |
| App domains | [tmp/app-master-spec.md](../../tmp/app-master-spec.md) |
| Engine bridge | [tmp/app-gamebridge-spec.md](../../tmp/app-gamebridge-spec.md) · [build/docs/engine-integration.md](../../build/docs/engine-integration.md) |
| Canon / grid | `build/data/av-grid/`, `build/systems/` |
| Play entry | [app/README.md](../../app/README.md) |
| Hook enforcement | [.cursor/hooks/backlog_ticket_gate.py](../../.cursor/hooks/backlog_ticket_gate.py) |

## Additional resources

- Role definitions: [agents.md](agents.md)
- Document templates: [templates.md](templates.md)
