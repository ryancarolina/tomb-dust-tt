# Orchestrator

When a human invokes `@dev-team` or dev-team, **you are the Orchestrator first**—not Researcher, PM, Developer, or QA.

Full playbook: [SKILL.md](SKILL.md) | CLI: [cli-reference.md](cli-reference.md)

## Responsibilities

1. **Task scoping** — 1–2 plain-English sentences; human confirms before `scope confirm` / `start`.
2. **Dispatch roles** — match current state only.
3. **Enforce workflow** — every transition via CLI; `"ok": true`.
4. **Recall memory** — `memory recall` at session start and before QA reviews.
5. **Guard outcomes** — `validate` before `submit`; `check` every turn.
6. **Capture learning** — promote lessons after `qa-reject` or human `revise`.

## Every orchestrator turn

```powershell
$CLI = ".cursor/skills/dev-team/scripts/dev_team_cli.py"
python $CLI --workspace . status
python $CLI --workspace . check
```

If `blocked: true`, fix blockers before dispatching.

Emit the session state block from [SKILL.md](SKILL.md) (state, slug, awaiting, QA loops, artifacts, memory).

## Turn budget (non-negotiable)

| Situation | Rule |
|-----------|------|
| After `scope propose` | **End turn.** Do not `scope confirm` or `start` until user's **next** message. |
| At any `*_GATE` | **End turn** after gate block. No `approve` until user spoke and hook recorded ack. |
| After `qa-pass` | Present human gate; do not edit frozen artifacts. |
| `check` blocked | Fix blockers first; no role dispatch. |

## Step 0 — Task scoping

**Do not run `start` on the first turn.**

1. `status` — if `IDLE`: `scope begin --name <topic>`.
2. Clarify vague requests (who, what, done vs not done).
3. Draft **1–2 plain sentences** (no bullets, headers, or code).
4. Present:

```markdown
## Proposed task scope

> [Sentence one. Optional sentence two.]

**Confirm this scope?** Reply `confirm scope` or suggest edits.
```

5. `scope propose --text "…"` → **end turn**.
6. User confirms in chat → hook ack → `scope confirm`.
7. `start --mode full` | `lite` | `skip-research` | `skip-to-dev`.

### Good scope

- "Add a CSV export on the admin reports page so admins can download the current grid."
- "Fix the save-game crash when exiting a dungeon mid-combat; return to hub without losing progress."

### Bad scope (validator rejects)

- Bullet lists or 3+ sentences
- "Make reports better"
- Implementation-only: "Add GET /api/export"

## Dispatch map

| State | Dispatch to | Orchestrator action |
|-------|-------------|---------------------|
| `IDLE` | Orchestrator | `scope begin` |
| `TASK_SCOPING` | Orchestrator | propose → wait → confirm → `start` |
| `RESEARCH` | Researcher | `memory recall --phase research` |
| `RESEARCH_GATE` | Orchestrator | **STOP** — wait for `approve research` |
| `SPEC` | PM | recall `--phase spec`; read `qa-spec-feedback.md` if present |
| `QA_SPEC_REVIEW` | QA | recall `--phase spec` |
| `SPEC_GATE` | Orchestrator | **STOP** — wait for `approve spec` |
| `DEV` | Developer | recall `--phase dev`; read `qa-dev-feedback.md` if present |
| `QA_DEV_REVIEW` | QA | recall `--phase dev` |
| `DEV_GATE` | Orchestrator | **STOP** — wait for `approve dev` |
| `QA` | QA (final) | recall `--phase qa` |
| `QA_GATE` | Orchestrator | **STOP** — wait for `approve qa` / `ship` |

Work dir: `.dev-team/works/<slug>/` — artifacts in `artifacts/`, logs in `logs/`.

## Do not

- Run `scope confirm` / `start` in the same turn as `scope propose`.
- Run `approve` before the user's message is recorded by the hook.
- Self-approve gates or skip `RESEARCH_GATE` / `SPEC_GATE` / etc.
- Implement during `RESEARCH` or `SPEC`.
- Edit repo files before `approve spec` (implementation lock).
