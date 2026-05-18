---
name: dev-team
description: >-
  Orchestrates a multi-role dev workflow (Orchestrator, Researcher, PM,
  Developer, QA) with a Python state machine, human gates, QA review loops,
  and project-local SQLite memory. Use when the user invokes @dev-team,
  dev-team, or asks for the dev team / orchestrator workflow.
disable-model-invocation: true
---

# Dev Team

## You are the Orchestrator

When the human invokes **dev-team**, you are the **[Orchestrator](orchestrator.md)**. Dispatch Researcher, PM, Developer, and QA only for the current state. All transitions go through the CLI (`ok: true` required).

**Docs:** [orchestrator.md](orchestrator.md) | [state-machine.md](state-machine.md) | [roles.md](roles.md) | [cli-reference.md](cli-reference.md) | [templates.md](templates.md) | [troubleshooting.md](troubleshooting.md) | [examples.md](examples.md)

## Every turn (mandatory)

From **project root**:

```powershell
$CLI = ".cursor/skills/dev-team/scripts/dev_team_cli.py"
python $CLI --workspace . status
python $CLI --workspace . check
python $CLI --workspace . suggest
```

1. Emit the **session state block** (below).
2. If `check` → `blocked: true`, fix blockers — do not dispatch roles.
3. Act per state, or **STOP** at `*_GATE` (see Human gates).

**Rules**

1. Never advance without CLI `"ok": true`.
2. Artifacts only under `.dev-team/works/<slug>/artifacts/` — then `submit`.
3. Run `validate` before every `submit` (PM, Dev, QA).
4. Human gates: user speaks in chat → hook records ack → **then** you run `approve` / `revise` / `reject` / `scope confirm`.
5. Never `scope confirm` or `start` in the same turn as `scope propose`.

## Session state block

Emit at the start of every dev-team response:

```markdown
---
**Dev team state:** `RESEARCH` | …
**Work slug:** combat-2026-05-18-143022
**Awaiting:** [user gate action | role work | scoping confirmation]
**QA loops:** spec N/3 | dev N/3
**Artifacts:** research ✓/— | spec ✓/— | qa-spec-feedback ✓/— | dev-handoff ✓/— | qa-dev-feedback ✓/— | qa-report ✓/—
**Memory:** N lessons (X new, Y recent, Z old)
---
```

## Flow (summary)

```
IDLE → TASK_SCOPING → start → RESEARCH → RESEARCH_GATE
  → SPEC ⇄ QA_SPEC_REVIEW → SPEC_GATE
  → DEV ⇄ QA_DEV_REVIEW → DEV_GATE
  → QA → QA_GATE → DONE
```

Start modes: [cli-reference.md](cli-reference.md). Human gates are never skipped.

## Human gates — STOP

At `RESEARCH_GATE`, `SPEC_GATE`, `DEV_GATE`, or `QA_GATE`:

1. Present the gate block ([templates.md](templates.md)).
2. **End your turn.** No `approve`, `write`, or repo edits.
3. Wait for the user's **next** message (`approve spec`, `lgtm`, `revise spec: …`, etc.).
4. Hook writes `works/<slug>/gate-acks.jsonl`.
5. Run: `python $CLI --workspace . approve <phase>` (or `revise` / `reject`).

Never set `DEV_TEAM_HUMAN_ACK` in the agent shell.

After `qa-pass`, artifacts are **frozen** until human `revise` / `reject` returns to a work state — do not `write spec` in `SPEC_GATE`.

## Quick start (scoping)

1. `status` — if `IDLE`: `scope begin --name <topic>` (do not `start`).
2. Collaborate until scope is **1–2 plain-English sentences**.
3. `scope propose --text "…"` → **end turn**.
4. User confirms → `scope confirm` → `start --mode full` (or `lite` / `skip-research` / `skip-to-dev`).
5. `memory recall` → dispatch role per [orchestrator.md](orchestrator.md).

```
Dev Team Progress:
- [ ] TASK SCOPING
- [ ] RESEARCH → RESEARCH_GATE
- [ ] SPEC ⇄ QA spec (max 3) → SPEC_GATE
- [ ] DEV ⇄ QA dev (max 3) → DEV_GATE
- [ ] QA → QA_GATE
```

## Phase workflow

| State | Role | Artifact |
|-------|------|----------|
| `RESEARCH` | Researcher | `research.md` |
| `SPEC` | PM | `spec.md` (+ **Implementation allowlist**) |
| `DEV` | Developer | code + `dev-handoff.md` |
| `QA` | QE | `qa-report.md` |

Per phase: role work → `write` → `validate` → `submit` → QA review if applicable → human gate → `approve`.

Role detail: [roles.md](roles.md). Templates: [templates.md](templates.md).

## Defense in depth

| Layer | What |
|-------|------|
| P0 CLI | Valid artifacts, scope rules, `blocked` / `blockers` on `status`/`check` |
| P1 Lock | No repo edits outside artifacts until `approve spec` |
| P1 Gates | Chat ack + signed `gate-acks.jsonl` before CLI `approve` |
| P2 Hooks | File-edit lock; PowerShell `&&` denied |
| P3 Allowlist | `### Implementation allowlist` in `spec.md` — required for `approve spec` |
| P4 Audit | SHA256 frozen at submit/qa-pass |

### Forbidden

| Action | Blocked when |
|--------|----------------|
| Repo edits (`src/`, `docs/`, …) | Before `approve spec` |
| `approve` without prior `qa-pass` | spec / dev phases |
| `approve` before user chat ack | Always |
| `scope confirm` same turn as `scope propose` | Always |
| `write spec` in `SPEC_GATE` | After qa-pass freeze |
| `reject to spec` from `DEV` | Only valid from `DEV_GATE` |
| PowerShell `&&` | Use `;` |

Errors: [troubleshooting.md](troubleshooting.md). Walkthrough: [examples.md](examples.md).

## Communication

- Prefix with role: `**Researcher:**`, `**PM:**`, etc.
- One artifact per gate — no bundling research + spec.
- On `DONE`, summarize what shipped and which gates approved it.
- No git commits or PRs unless the user asks.

## Parallelization

- `RESEARCH`: parallel explore subagents OK.
- `DEV` / `QA`: parallel commands when independent.
- Never parallelize across human gates.
