# Tomb Dust — App Master Spec

**Status:** Active registry  
**Created:** 2026-05-20  
**Scope:** Entire PyGame client under `app/` — development and testing source of truth  
**Entry point:** [`app/main.py`](../app/main.py)

**Canonical development specs** — all `tmp/app-*-spec.md` files are versioned in git.

---

## Drift policy (non-negotiable)

**Specs are the source of truth for app development and testing. Drift between spec and code is NEVER allowed.**

| Rule | Meaning |
|------|---------|
| **Spec first** | Every app change starts in or updates the **respective domain spec** before or alongside code. |
| **Spec = tests** | Each domain spec defines acceptance criteria and tests; passing those tests is the definition of done. |
| **Changelog required** | Completed work gets a dated entry in the spec’s changelog (§ Changelog). |
| **No orphan code** | Behavior not described in any spec is out of scope — add to a spec first. |
| **No stale specs** | If code changes, the spec updates in the **same PR / session**. Never leave specs lying. |

### Agent workflow (every `app/` change)

1. Read this master spec → open the **domain spec** for the area you touch.
2. Pick or create a **backlog ticket** in [`backlog/README.md`](backlog/README.md) (`open` → `in_progress`).
3. Implement in code to match the domain spec; stay within ticket **Expected files**.
4. Run tests listed in the spec + ticket acceptance criteria.
5. Close ticket (`done`); append **Changelog** entry in the domain spec.
6. If the change spans domains, update **each** affected spec and ticket.

### When specs disagree with code

**The spec wins until you update both.** Either revert code or update the spec in the same change — never merge drift.

---

## Spec registry

Each spec is named for **what it changes**. One spec owns one domain.

| Domain | File | Owns (`app/`) | Related engine/canon |
|--------|------|---------------|----------------------|
| Shell & config | [`app-shell-config-spec.md`](app-shell-config-spec.md) | `main.py`, `config.yaml`, `requirements.txt`, `.env` | — |
| Session persistence | [`app-session-persistence-spec.md`](app-session-persistence-spec.md) | `session_state.json`, autosave, resume | `play/workspace/` |
| PyGame UI | [`app-pygame-ui-spec.md`](app-pygame-ui-spec.md) | `ui/**` | — |
| GameBridge | [`app-gamebridge-spec.md`](app-gamebridge-spec.md) | `gm/bridge.py` | `play/tomb_gm/` |
| Character creation | [`app-character-creation-spec.md`](app-character-creation-spec.md) | `gm/creation.py`, creation path in orchestrator | `build/data/character/` |
| LLM orchestrator | [`app-llm-orchestrator-spec.md`](app-llm-orchestrator-spec.md) | `gm/orchestrator.py`, `tools.py`, `context.py`, `system_prompt.py`, `openrouter.py`, `choice_memory.py` | — |
| Exploration & delve | [`app-exploration-delve-spec.md`](app-exploration-delve-spec.md) | travel/site tools in orchestrator + map UI | `play/tomb_gm/services/site.py`, `world.py` |
| Combat play | [`app-combat-play-spec.md`](app-combat-play-spec.md) | `gm/combat_fsm.py`, combat tools in orchestrator | `play/tomb_gm/services/simulation/combat.py` |
| Economy & inventory (app) | [`app-economy-inventory-play-spec.md`](app-economy-inventory-play-spec.md) | equip/stash/vendor tools + UI stats | [`build/docs/engine-integration.md`](../build/docs/engine-integration.md) § Inventory v3 |
| TTS & narration | [`app-tts-narration-spec.md`](app-tts-narration-spec.md) | TTS hooks, voice labels, narration panel | `play/tomb_gm/services/tts/` |
| Logging & QA | [`app-logging-qa-spec.md`](app-logging-qa-spec.md) | `gm/logger.py`, `app/logs/`, `app/tests/` | CI |

**Only `app-*-spec.md` files belong in `tmp/`.** Canon mechanics: `build/systems/` + [`build/docs/engine-integration.md`](../build/docs/engine-integration.md).

**Work tracking:** [`backlog/README.md`](backlog/README.md) — one ticket per task; each ticket links to exactly one domain spec above.

---

## Priority execution order (P0 first)

```text
app-exploration-delve-spec  → fix site passage edges (unblocks check)
app-logging-qa-spec         → creation_drift logging
app-character-creation-spec → deterministic tables + finalize gate
app-session-persistence-spec → reliable new game
app-llm-orchestrator-spec   → creation hard gate + transcript sanitize
app-exploration-delve-spec  → delve/travel tool alignment
app-combat-play-spec        → combat tool gating
app-logging-qa-spec         → app/tests + golden path
```

---

## Domain dependency map

```text
app-shell-config
  → app-session-persistence
  → app-gamebridge
      → app-character-creation
      → app-llm-orchestrator
          → app-exploration-delve
          → app-combat-play
          → app-economy-inventory-play
      → app-pygame-ui (reads state from bridge/orchestrator)
      → app-tts-narration
  → app-logging-qa (all domains)
```

---

## Global definition of done (app release)

Tracked as release tickets in [`backlog/README.md`](backlog/README.md):

| Ticket | Gate |
|--------|------|
| [APP-053](backlog/app-053-keep-domain-specs-drift-free.md) | Domain specs match code |
| [APP-054](backlog/app-054-app-tests-pytest-green.md) | `python -m pytest app/tests` green |
| [APP-055](backlog/app-055-tombgm-tests-pytest-green.md) | `python -m pytest play/tomb_gm/tests` green |
| [APP-056](backlog/app-056-validatecontent-clean.md) | `validate_content.py` clean |
| [APP-052](backlog/app-052-release-smoke-new-game-through-save-resume.md) | Full smoke: new game → creation → beat → save → resume |

---

## Domain spec template

Every domain spec MUST include:

1. **Status** — `Not started` | `In progress` | `Complete` | section-level ✅  
2. **Scope** — code paths owned  
3. **Spec** — behavior the app must exhibit  
4. **Task checklist** — completed `- [x]` items; open work links to [`backlog/`](backlog/README.md) tickets  
5. **Tests** — commands + scenarios (spec is the test spec)  
6. **File map** — spec ↔ code  
7. **Changelog** — dated entries when work lands  

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial app master spec + full domain registry; drift policy for agents |
| 2026-05-20 | Removed non-app tmp docs; merged into domain specs |
| 2026-05-20 | Renamed `*-plan.md` → `*-spec.md` |
| 2026-05-20 | Removed `play/docs/*-spec.md` and `build/backlog/`; `tmp/` is the only spec tree (tracked in git) |
| 2026-05-20 | Added `tmp/backlog/` ticket system (APP-001–057); no-ticket-no-change cursor rule |
| 2026-05-20 | APP-056: `validate_content.py` clean (site edge remap via APP-001) |
