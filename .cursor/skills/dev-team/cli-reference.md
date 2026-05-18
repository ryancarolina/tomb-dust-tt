# Dev Team — CLI Reference

Run every command from the **project root** with `--workspace .`.

## Setup

```powershell
# PowerShell — use ; not &&
$CLI = ".cursor/skills/dev-team/scripts/dev_team_cli.py"
```

```bash
# bash
CLI=".cursor/skills/dev-team/scripts/dev_team_cli.py"
```

All commands: `python $CLI --workspace . <subcommand>`

## Every orchestrator turn

| Order | Command |
|-------|---------|
| 1 | `status` |
| 2 | `check` — if `blocked: true`, fix blockers before dispatching |
| 3 | `suggest` — recommended next commands; `stop: true` at human gates |
| 4 | Role work or wait at gate |

## Session lifecycle

| Step | Command |
|------|---------|
| Status | `status` |
| Defense check | `check` |
| Next steps | `suggest` |
| Assert gate ready | `assert-gate spec` |
| Clear legacy state | `reset` |
| Verify repo path | `verify-path docs/foo.md` |
| Begin scoping | `scope begin --name combat` (**--name required**) |
| Propose scope | `scope propose --text "One or two plain sentences."` |
| Confirm scope | `scope confirm` — **only after human says yes in a later turn** |
| Start | `start --mode full` |
| Show work | `works show` |
| List work dirs | `works list` |
| Tail logs | `log tail` |
| Clear active work logs | `log clear` |
| Log note | `log note --role orchestrator --message "…"` |
| Remove old work dir | `works remove --slug <slug>` |
| Cancel | `abort` |

### Start modes

| Mode | First state | Skips |
|------|-------------|--------|
| `full` | `RESEARCH` | — |
| `lite` | `SPEC` | Research (user may inline spec at start) |
| `skip-research` | `SPEC` | Research phase |
| `skip-to-dev` | `DEV` | Research + spec work (pre-flags QA pass; human gates still required) |

Human gates (`*_GATE`) are **never** skipped by any mode.

## Artifacts

Artifact root: `.dev-team/works/<slug>/artifacts/`

| Step | Command |
|------|---------|
| Save artifact | `write spec --file .dev-team/works/<slug>/artifacts/spec.md` |
| Validate only | `validate` |
| PM submit spec | `submit spec` → `QA_SPEC_REVIEW` |
| QA pass spec | `qa-pass spec` → `SPEC_GATE` |
| QA reject spec | `write-qa-feedback spec --file …` then `qa-reject spec` → `SPEC` |
| Dev submit | `submit dev` → `QA_DEV_REVIEW` |
| QA pass dev | `qa-pass dev` → `DEV_GATE` |
| QA reject dev | `write-qa-feedback dev --file …` then `qa-reject dev` → `DEV` |
| Final QA submit | `submit qa` → `QA_GATE` |
| Record tests | `record-checks --note "pytest: pass"` |

## Human gates (two steps)

1. **Human** replies in chat: `approve spec`, `lgtm`, `revise spec: …`, `reject to spec`, etc.
2. **Hook** records ack in `works/<slug>/gate-acks.jsonl`
3. **Orchestrator** runs matching CLI: `approve spec`, `revise spec`, `reject spec`, etc.

| CLI (after human ack) | From state |
|-----------------------|------------|
| `approve research` | `RESEARCH_GATE` |
| `approve spec` | `SPEC_GATE` |
| `approve dev` | `DEV_GATE` |
| `approve qa` | `QA_GATE` |
| `revise <phase>` | matching `*_GATE` |
| `reject research` / `reject spec` / `reject dev` | see [state-machine.md](state-machine.md) |

Never set `DEV_TEAM_HUMAN_ACK` in the agent shell — that bypass is for the human's terminal only.

## Memory

| Command | Purpose |
|---------|---------|
| `memory recall --phase spec --limit 5` | Surface lessons for a role |
| `memory add --kind bug --phase dev --title "…" --lesson "…"` | Record a lesson |
| `memory stats` | Counts by age bucket |
| `memory promote <id>` | Promote draft from `qa-reject` |

Database: `.dev-team/memory.db` (project-local, gitignored).

## Work directory layout

```
.dev-team/
  active.json
  memory.db
  works/
    combat-2026-05-18-143022/
      meta.json
      session.json
      artifacts/
      logs/
        events.jsonl
        audit.log
```

`scope begin --name combat` → folder `combat-<YYYY-MM-DD-HHmmss>`.

## Tests (after skill changes)

```bash
python -m pytest .cursor/skills/dev-team/scripts/test_machine.py .cursor/skills/dev-team/scripts/test_memory.py .cursor/skills/dev-team/scripts/test_human_approval.py -q
```
