# Dev Team — Examples

## Happy path (full mode)

**Turn 1 — Orchestrator (IDLE)**

```text
python $CLI --workspace . status
python $CLI --workspace . check
python $CLI --workspace . scope begin --name combat-export
```

Collaborate with human; draft 1–2 sentences. **End turn** (do not confirm yet).

**Turn 2 — Human:** `confirm scope`

**Turn 3 — Orchestrator**

```text
python $CLI --workspace . scope confirm
python $CLI --workspace . start --mode full
python $CLI --workspace . memory recall --phase research --limit 5
```

Dispatch **Researcher** → write `research.md` → `validate` → `submit research` → state `RESEARCH_GATE`.

Present human gate. **End turn.**

**Turn 4 — Human:** `approve research`

**Turn 5 — Orchestrator**

```text
python $CLI --workspace . approve research
```

Dispatch **PM** → `spec.md` with **Implementation allowlist** → `validate` → `submit spec` → `QA_SPEC_REVIEW`.

Dispatch **QA** → `validate` → `qa-pass spec` → `SPEC_GATE`. Present gate. **End turn.**

**Turn 6 — Human:** `approve spec`

**Turn 7 — Orchestrator**

```text
python $CLI --workspace . approve spec
```

Dispatch **Developer** (allowlisted paths only) → `submit dev` → QA dev review → `DEV_GATE` → human → `approve dev` → final QA → `QA_GATE` → `approve qa` → `DONE`.

## Docs-only task (no src yet)

Scope: "Split the game design doc into modular markdown files under docs/ with a clear index."

Spec allowlist:

```markdown
### Implementation allowlist
- docs/**
- Tomb Dust Game System.md
```

## Recovery: missing allowlist at SPEC_GATE

1. QA or CLI fails: `spec.md must include ### Implementation allowlist`
2. If still in `SPEC`: add section → `submit spec` → `qa-pass spec`
3. If already in `SPEC_GATE` with frozen hash: human `revise spec: add allowlist for docs/**` → back to `SPEC` → fix → resubmit

## Recovery: agent skipped RESEARCH_GATE

**Wrong:** `submit research` then immediately `approve research` without human message.

**Fix:** If still at `RESEARCH_GATE`, stop and wait for human. If already past illegally, `abort` and restart, or human `reject to research` from `SPEC_GATE`.

## Anti-patterns (from real audit logs)

| Anti-pattern | Why it fails |
|--------------|--------------|
| `scope propose` + `scope confirm` + `start` same turn | Human never confirmed scope |
| `approve spec` from agent shell without user chat | Human-only gate |
| `write spec` in `SPEC_GATE` | Wrong state; breaks qa-pass hash |
| `reject to spec` while in `DEV` | Requires `DEV_GATE` |
| Edit `src/` before `approve spec` | `implementation_lock` hook |

See [troubleshooting.md](troubleshooting.md) for error → fix mapping.
