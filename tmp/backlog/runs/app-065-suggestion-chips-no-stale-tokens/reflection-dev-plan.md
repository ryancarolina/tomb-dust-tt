# Reflection: Dev — APP-065 plan

**Agent:** Dev  
**Round:** 1  
**Deliverables:** `plan.md`, `reflection-dev-plan.md`

## Completed

- Read research-brief, spec r2, qa-spec-pass, ticket Expected files, domain spec § Suggestion chips.
- Traced current bug paths in `app/ui/app.py` L315–317 (stale guard) and L339–348 (`_extract_suggestions` regex).
- Traced equipment handler at `orchestrator.py` L1004–1008 and post-finalize `creation.active = False` at L1196–1197.
- Wrote `plan.md` with approach, five code-path trace tables, six task sections, file list ⊆ Expected files, test matrix, AC mapping.
- Confirmed `app/ui/suggestions.py` and `app/tests/test_ui_suggestions.py` do not exist yet (greenfield).
- Confirmed domain spec already updated by PM; impl only needs checklist + changelog on close.

## Self-critique

- **Import path unverified:** Plan notes `from ui.suggestions import ...` but I did not grep all orchestrator cross-package imports before writing. Impl must confirm APP is on `sys.path` when orchestrator loads (likely yes via `main.py` / conftest).
- **`_process_turn` finally restructuring is subtle:** Moving `_save_session()` and suggestion refresh into one `finally` changes control flow vs current `except: return`. Plan pseudocode is correct in intent but impl must preserve TTS / `turn_idle` ordering after `finally` and not double-queue on stale `turn_id` early returns inside `try`.
- **Exception-path test gap:** Deliberately deferred full pygame `App` test for R1 exception refresh — relies on QA plan gate reading `finally` block. If QA plan is strict, may need a thin extracted helper.
- **Startup DRY left optional:** Keeping hardcoded startup chips avoids init-timing risk but duplicates SETUP map logic; acceptable per spec but worth a one-line comment in impl linking to `PLAYER_SUGGESTIONS_BY_AWAITING`.

## Did I miss anything?

- [x] Ticket scope / Expected files — plan files ⊆ ticket list; `input_box.py` explicitly no-change
- [x] Domain spec / registry_gap / AGENTS.md — registry_gap false; pygame-ui spec owns behavior
- [x] Code paths traced — turn loop, scrape removal, builder lookup, equipment handler, finalize guard
- [x] Tests / AC mapped — test_ui_suggestions cases + regression commands; exception path noted as QA-review item
- [ ] APP-073 batch ordering — noted prefer 073 first; plan does not depend on 073 landing
- [ ] `orchestrator` → `ui` import convention — flagged open question; verify at impl

## Handoff

**Ready for:** QA plan gate (adversarial code-level review of traces, finally-block design, test coverage gaps)

**Escalate human if:** QA requires automated `_process_turn` exception test and pygame mocking is deemed too costly — product choice between extract helper vs manual-only AC
