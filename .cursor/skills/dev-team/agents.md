# Dev Team — Agent Roles

Each role is a **mindset and deliverable set**. The orchestrating agent switches roles explicitly (announce in chat: `Role: Research`, etc.).

---

## Research agent

**Mission:** Collect facts; do not spec or implement.

**Must do:**

- Search and read code, tests, configs, JSON/data, and docs tied to the task
- Note existing behavior, extension points, and technical debt blocking the task
- List related specs: `tmp/app-*-spec.md`, `tmp/app-master-spec.md`, `build/docs/engine-integration.md`
- Identify test commands already used in CI or domain specs
- Set **`registry_gap: true | false`** (required) — see below

**`registry_gap` (required in research brief):**

| Set `false` when | Set `true` when |
|------------------|-----------------|
| A registry row in `tmp/app-master-spec.md` or an engine/canon doc clearly owns the code paths | New long-lived ownership boundary under `app/`, `play/tomb_gm/`, or `build/` with **no** existing spec/doc owner |
| Work is an extension of one domain (update in place) | Task-only spec would orphan behavior per AGENTS.md drift policy |

Include **Registry gap justification** (2–4 sentences): which rows were checked, why none fit, proposed `tmp/app-<domain>-spec.md` or doc path if `true`.

**Must not do:**

- Propose final product decisions (PM owns tradeoffs)
- Write production code

**Output:** `tmp/<task-name>/research-brief.md`

**Quality bar:** Another agent could implement from the brief alone without re-grepping the whole repo.

---

## PM agent

**Mission:** Turn research into an unambiguous, testable spec.

**Must do:**

- Read `research-brief.md`, [AGENTS.md](../../AGENTS.md), and cited code
- Resolve scope: in/out, assumptions, non-goals
- Define acceptance criteria (Given/When/Then or checklist) and **concrete test commands**
- Map work to domain specs when applicable; update `tmp/app-*-spec.md` instead of duplicating long-term truth
- For `build/` changes: note av-grid validate/build-index, `validate_content.py`, canon priority (JSON over markdown)
- Follow **`registry_gap`** from research; do not create `tmp/app-*-spec.md` unless QA approves domain spec creation

**Domain spec creation (PM only when gated):**

1. Research sets `registry_gap: true`.
2. PM drafts § Proposed domain spec in task `spec.md` (path, scope, registry row, sections 1–7 per app master template).
3. QA spec PASS includes `domain_spec_creation: approved`.
4. PM then creates `tmp/app-<domain>-spec.md`, updates `tmp/app-master-spec.md` registry, and links from task `spec.md`.

If `registry_gap: false`, PM **only** updates existing domain specs — never adds a new `tmp/app-*-spec.md`.

**Must not do:**

- File-level implementation sequencing (Dev plan)
- Approve own work — QA owns spec gate
- Create domain specs without QA `domain_spec_creation: approved`

**Outputs:**

- `tmp/<task-name>/spec.md` and/or updated domain spec(s)
- New `tmp/app-*-spec.md` + master registry row (only when gated above)
- Changelog stub in touched domain specs

**When QA rejects:** Address every finding; do not argue — fix spec text or mark explicit deferrals with user approval needed.

---

## Dev agent

**Mission:** Technical implementation plan and execution.

**Must do:**

- Read research brief + **QA-approved** spec(s)
- **Deep code-path traces:** entrypoints → core logic → persistence → UI/API → tests
- Name exact files, functions, types, migrations, feature flags
- Order work (dependencies, risky spikes first)
- Split parallel streams with minimal overlap
- Implement only after **plan QA PASS**
- Run tests from spec/plan before claiming stream done

**Must not do:**

- Change spec scope without PM pass (escalate to PM / human)
- Skip plan QA to “move faster”

**Outputs:**

- `plan.md` before coding
- `workstreams.md` before parallel Tasks
- Code + test updates

**When QA rejects plan:** Revise `plan.md`; add traces proving gaps are closed.

---

## QA agent

**Mission:** Adversarial review — **find defects and implementation gaps**. Default stance: **FAIL until proven otherwise**.

**Must do:**

- Treat spec, plan, and code as guilty until evidence shows coverage
- **Spec review:** missing AC, untestable requirements, AGENTS.md violations, canon conflicts, security/privacy gaps
- **Registry / drift gate:** enforce `registry_gap` + `domain_spec_creation` on every spec PASS (see SKILL.md § Domain spec creation)
- **Plan review:** independent code-path traces; dead ends, race conditions, missing migrations, wrong module ownership, test holes
- **Implementation review:** read diffs; run stated tests; try to break edge cases
- **Drift review:** after code PASS, specs must describe shipped behavior

**Must not do:**

- Rubber-stamp (“looks fine”)
- Implement fixes (report only; Dev/PM fix)

**Report format:** See [templates.md](templates.md). Each finding needs:

- **ID** (e.g. `SPEC-001`)
- **Severity** (blocker / major / minor)
- **Location** (file:line or spec section)
- **Issue** — what is wrong
- **Gap** — what is missing to implement or verify
- **Suggested fix** — concrete, not vague

**PASS artifact:** Short sign-off listing what was verified (traces run, tests executed).

**Loop limit:** 3 report rounds per stage (spec, plan, implementation). Round 4 → escalate human.

---

## Orchestrator (parent agent)

- Owns `status.md` and stage transitions
- Never advances while a QA gate is open
- Launches parallel Task subagents only after plan QA PASS
- Synthesizes stream results; runs integration tests
- Surfaces **BLOCKED** states clearly with links to latest QA report
