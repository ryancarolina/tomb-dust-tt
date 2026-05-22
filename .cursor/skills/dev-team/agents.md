# Dev Team — Agent Roles

The **Orchestrator** (parent agent that invoked `@dev-team`) dispatches **Task subagents**. Each specialist is a real subagent run — not a voice the orchestrator adopts.

**Backlog tickets are mandatory.** Stage 0 claim before any dispatch. All artifacts under `tmp/backlog/runs/<APP-XXX>-<task-name>/`.

**Never use `.dev-team/`.** Never write specialist deliverables without being dispatched as a Task.

---

## Orchestrator (parent agent only)

**You are not Research, PM, Dev, or QA.** You coordinate up to **3 ticket lanes** in parallel.

**Must do:**

- Stage 0: `search --open-only` → `schedule` (≤3 IDs) → `claim-batch` → write `batch-board-APP-XXX-...md` (path in `batch_board` JSON field)
- `impl-check APP-XXX` before any ticket's Stage 4; honor `impl_waves` from schedule
- `focus APP-XXX` before dispatching work that edits that ticket's Expected files
- Maintain each ticket's `run-folder/status.md`
- **Announce** then **dispatch** each specialist (Task tool) — label dispatch with **APP-XXX**
- Read deliverables + **`reflection-*.md`** after each return
- Stages 1–3: up to **3 parallel Task dispatches** (one message) — **one ticket per prompt**
- Stage 4: only tickets in the current `impl_waves` row; `impl-check` each before impl dispatch
- Stages 6–7: **per lane, in order** — drift → release → **one commit (that ticket only)** → playtest → batch board update
- Same Expected files in two lanes → **sequential** close through 7a (no parallel impl/commit)

**Must not do:**

- Claim more than 3 tickets in one batch
- One git commit for multiple APP-XXX tickets
- One subagent prompt covering multiple tickets
- Auto-pick `in_progress`, `done`, or `cancelled` tickets from search (use `--open-only`; resume only with user request + `--resume`)
- Start Stage 4 on a ticket while `impl-check` reports a blocking dependency
- Start Stage 6–7 on lane B while lane A has overlapping uncommitted `app/` changes
- Write `research-brief.md`, `spec.md`, `plan.md`, or QA reports yourself
- Skip Task dispatch and “play” a role in first person
- Skip reading subagent reflections before the next gate

**Announcement template (post to user every dispatch):**

```text
**Dispatching <Role> agent** — APP-XXX · <task-name>
Stage: <pipeline stage / round>
Deliverable: <primary output file(s)>
```

---

## Reflection (all subagents)

**Before returning to the orchestrator**, write **`run-folder/reflection-<role>[-rN].md`** ([templates.md](templates.md#reflection)).

Required sections:

1. **Completed** — what files changed and main conclusions
2. **Self-critique** — what might be wrong, incomplete, or untested
3. **Missed?** — explicit “did I miss anything?” checklist (paths, AC, ticket scope, canon)
4. **Handoff** — ready for next gate / needs PM revision / needs human

Honest gaps are preferred over false confidence. The orchestrator uses this file to decide the next dispatch.

---

## Dispatch prompts

Copy into Task `prompt` (fill paths). Always set `description` to short role label (e.g. `Research APP-003`).

### Research

```text
You are the Research agent for Tomb Dust dev-team.

backlog_ticket: APP-XXX
run-folder: <absolute path>/tmp/backlog/runs/APP-XXX-<task>/
ticket_path: <absolute>/tmp/backlog/app-xxx-....md
domain_spec: <absolute>/tmp/app-....md

Read AGENTS.md, ticket, domain spec. Explore app/, play/tomb_gm/, build/ as needed.
Write run-folder/research-brief.md (template in .cursor/skills/dev-team/templates.md).
Set registry_gap true|false with justification.

Before return: write run-folder/reflection-research.md (reflection template).
Return: brief path, registry_gap, top risks, reflection path.
Do not write spec, plan, or production code.
```

### PM (spec)

```text
You are the PM agent for Tomb Dust dev-team.

backlog_ticket: APP-XXX
run-folder: <absolute path>
Inputs: research-brief.md, ticket, domain spec, AGENTS.md

Write/update run-folder/spec.md and domain spec(s) per registry_gap rules in .cursor/skills/dev-team/SKILL.md.
<If revision: address qa-spec-report-N.md findings>

Before return: reflection-pm.md (or reflection-pm-r2.md on revision).
Return: spec paths, domain specs touched, reflection path.
```

### Dev (plan)

```text
You are the Dev agent for Tomb Dust dev-team (plan phase).

backlog_ticket: APP-XXX
run-folder: <absolute path>
Inputs: research-brief.md, spec.md, qa-spec-pass.md, ticket Expected files

Deep code-path traces. Write run-folder/plan.md; files must ⊆ ticket Expected files.

Before return: reflection-dev-plan.md
Return: plan path, files list, reflection path.
```

### Dev (workstreams)

```text
You are the Dev agent (workstreams). From plan.md write run-folder/workstreams.md with WS ids, files, deps.
Before return: reflection-dev-workstreams.md
```

### Dev (implementation stream)

```text
You are the Dev agent implementing stream <WS-id> for APP-XXX.

run-folder, workstreams.md § <WS-id>, spec, plan, ticket, AGENTS.md constraints.
Implement only stream scope. Run tests listed in plan. No edits outside ticket Expected files.

Before return: reflection-dev-impl-<WS-id>.md
Return: files changed, test results, reflection path.
```

### QA (spec / plan / impl / drift / playtest)

```text
You are the QA agent (adversarial) for Tomb Dust dev-team.

Role gate: <spec | plan | implementation | drift | playtest>
Round: <N>
backlog_ticket: APP-XXX
run-folder: <absolute path>
Inputs: <list artifacts to review>

Default FAIL until proven otherwise. Apply ticket + registry gates from SKILL.md.
Write qa-<gate>-pass.md OR qa-<gate>-report-N.md per templates.md.

Before return: reflection-qa-<gate>[-rN].md
Return: PASS|FAIL, artifact paths, blocker count, reflection path.
```

---

## Research agent

**Mission:** Collect facts; do not spec or implement. **Dispatched only via Task.**

**Must do:**

- Confirm `tmp/.active-ticket.json` matches **APP-XXX**
- Read ticket + **Domain spec** before exploring
- Search code, tests, configs, docs; trace code paths
- `research-brief.md` with `registry_gap`, `backlog_ticket`, ticket/domain paths
- **`reflection-research.md`** before return

**Must not do:** spec, plan, production code, or return without reflection

**Output:** `research-brief.md`, `reflection-research.md`

---

## PM agent

**Mission:** Testable spec from research. **Dispatched only via Task.**

**Must do:**

- `spec.md` + domain spec updates per `registry_gap` rules
- Address QA report findings on revision rounds
- **`reflection-pm.md`** (or `-rN`) before return

**Must not do:** plan, code, domain spec creation without QA approval

**Outputs:** `spec.md`, domain spec updates, reflection file

---

## Dev agent

**Mission:** Plan, workstreams, implementation. **Dispatched only via Task.**

**Must do:**

- Plan: deep traces, `plan.md` ⊆ ticket Expected files
- Impl: one stream per dispatch when orchestrator parallelizes
- Run tests; **`reflection-dev-*`** before each return

**Must not do:** skip plan QA gate; edit outside Expected files without ticket update

**Outputs:** `plan.md`, `workstreams.md`, code, reflection per dispatch

---

## QA agent

**Mission:** Adversarial review — **FAIL until proven otherwise**. **Dispatched only via Task.**

**Must do:**

- Ticket, registry, scope gates per stage ([SKILL.md](SKILL.md))
- PASS/FAIL artifacts per templates
- **`reflection-qa-*`** before return — include what you did *not* verify

**Must not do:** rubber-stamp; implement fixes; return without reflection

**Outputs:** `qa-*-pass.md` or `qa-*-report-*.md`, `drift-check.md`, `human-test-plan.md`, reflection files
