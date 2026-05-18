# Dev Team — Troubleshooting

When a CLI command returns `"ok": false`, read `detail` / `errors` in the JSON output. Run `log tail` for the audit trail.

## Scoping

| Error | Cause | Fix |
|-------|-------|-----|
| Scope validator rejects text | Bullets, 3+ sentences, or vague one-liner | Rewrite as 1–2 plain sentences; `scope propose` again |
| `start` without scope confirm | Skipped human confirmation | Wait for user `confirm scope` in chat → hook ack → `scope confirm` → `start` |
| `scope confirm` in same turn as `scope propose` | Agent rushed scoping | **Never** confirm in the turn you proposed; wait for user's next message |

## Human gates

| Error | Cause | Fix |
|-------|-------|-----|
| `'approve spec' is human-only and blocked for agents` | Agent ran `approve` before user message | User types `approve spec` in chat; hook writes ack; **then** orchestrator runs CLI `approve spec` |
| `approve` requires signed ack in gate-acks.jsonl | No hook record yet | End turn at gate; wait for user reply |
| `DEV_TEAM_HUMAN_ACK` mentioned | Agent tried env bypass | Do **not** set this in agent shell; human uses it only in their own terminal if documented |

## Spec / QA spec

| Error | Cause | Fix |
|-------|-------|-----|
| `spec.md must include ### Implementation allowlist` | PM omitted allowlist | Add section with glob paths (see [templates.md](templates.md)); stay in `SPEC`; `submit spec` → `qa-pass spec` again |
| `Cannot write spec artifact in SPEC_GATE` | Tried to edit spec at human gate | User `revise spec: …` or `reject to spec` from `SPEC_GATE`, **or** `reject spec` CLI after ack — not `write spec` in `SPEC_GATE` |
| `Cannot approve spec: artifact changed since qa-pass` | Edited spec after QA passed | Return to `SPEC` via human `revise`/`reject`; re-run full spec → QA → gate flow |
| `approve spec` without `qa-pass spec` | Skipped QA spec review | `submit spec` → QA `qa-pass spec` → then human gate |
| `Research was not approved` | Started spec without research gate | `approve research` at `RESEARCH_GATE`, or restart with `skip-research` |

## Dev / QA dev

| Error | Cause | Fix |
|-------|-------|-----|
| `implementation_lock` / repo edits blocked | Before `approve spec` | Write only under `works/<slug>/artifacts/` until human approves spec |
| `path not on allowlist` | Dev edited path not in spec | Add path to `### Implementation allowlist` in `spec.md`, return to `SPEC`, re-approve spec |
| `reject to spec requires DEV_GATE, got DEV` | Used reject while implementing | Finish dev + QA review first, or ask human at `DEV_GATE` to `reject to spec` |
| Max 3 QA cycles | Repeated rejections | Escalate to human: `revise`, `abort`, or scope change |

## Legacy / session

| Error | Cause | Fix |
|-------|-------|-----|
| `Legacy .dev-team/session.json detected` | Old layout | `reset` then `scope begin --name <topic>` |
| `no active dev-team work` | No `scope begin` or session ended | `status`; start new work if `IDLE` |

## PowerShell

| Error | Cause | Fix |
|-------|-------|-----|
| Hook denies `&&` | Invalid PowerShell syntax | Use `;` between commands: `Set-Location $pwd; python $CLI --workspace . status` |

## Recovery patterns

**Stuck at gate after QA passed:** Do not edit artifacts. Present human gate block and **end turn**.

**Need to change spec after `qa-pass spec`:** Human `revise spec: …` at `SPEC_GATE` (or `reject to spec` from `DEV_GATE`) — not silent `write spec`.

**Session polluted (agent skipped gates):** `abort` → `scope begin --name <new-topic>` → follow [examples.md](examples.md) happy path.
