# Spec: APP-077-code-owned-exploration-status-footer

**Status:** draft  
**backlog_ticket:** APP-077  
**ticket_path:** [tmp/backlog/app-077-code-owned-exploration-status-footer.md](../../app-077-code-owned-exploration-status-footer.md)  
**domain_spec:** [tmp/app-exploration-delve-spec.md](../../../app-exploration-delve-spec.md)  
**registry_gap:** false (echo research-brief)  
**Domain specs touched:** `tmp/app-exploration-delve-spec.md`, `tmp/app-llm-orchestrator-spec.md` (cross-link)

## Problem

Exploration and combat narration still **instruct the LLM** to emit a bracket status line every turn (`system_prompt.py` L213, L271–273). Unlike creation (`_compose_creation_narration` → `strip_llm_status_tags` + `format_creation_status`), exploration returns raw model prose from `_llm_loop` / `_combat_llm_loop_inner` with **no strip or code footer**. Combat paths call `_emit_narration` directly — **no compose at all**.

**Observed failures:** wrong GP in LLM bracket line while engine correct; stray `**Campaign Memory Updated:**` meta after status line; APP-087 sanitizer may leave LLM bracket-only turns (footer-only player view). `_check_creation_drift` no-ops outside creation — exploration lies are invisible.

**Evidence:** ticket cites `app/logs/session-2026-05-22.jsonl` (gitignored); research traces live code paths.

## Goals

- **One authoritative status line** per exploration/combat turn — built from fresh `bridge.status()`, not LLM prose.
- **Strip LLM status tags and meta leaks** from flavor before append (reuse APP-073 helper; extend bracket coverage).
- **Wire all player-visible exploration/combat emit paths** through `_compose_exploration_narration` (or thin combat wrapper).
- **Soften system prompt** — client appends state; GM writes prose only.
- Optional **`log_exploration_drift`** when stripped prose disagreed with engine (telemetry, APP-002 pattern).

## Non-goals

| Deferred | Ticket / note |
|----------|----------------|
| APP-083 Phase 2 verify before compose | Independent — compose order stays verify pass → compose when APP-089 wires |
| Suggestion chip source (`get_player_suggestions`) | APP-065 already uses engine `awaiting` — footer fixes player-visible lies only |
| TTS bracket strip policy change | APP-041 sibling — display footer authoritative; TTS may still strip at speak time |
| Multi-PC aggregated footer HP | Out of scope — slot-1 (lowest slot) active PC summary only |
| `build_state_context` / prompt truth block | Unchanged — separate from player footer |
| Creation footer shape | `format_creation_status` stays `Awaiting:` only |

## Requirements (summary)

Full behavior and test contracts: domain spec § **Code-owned status footer (exploration & combat) (APP-077)**. Orchestrator compose pipeline: [`app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) § **Code-owned exploration/combat status footer (APP-077)**.

| ID | Summary | Locus |
|----|---------|-------|
| **F1** | **`format_exploration_status(status: dict) -> str`** — canonical bracket line from `bridge.status()` snapshot (post-tool when compose runs) | `creation.py` (alongside `format_creation_status`) |
| **F2** | **Footer field mapping (PM decision):** `Location` = `party.display_address` if set else `party.address`; `Phase` = `party.phase`; `HP` / `Fortune` = lowest-`slot` roster entry `hp` / `fortune` strings; `GP` = that entry's `gold`; if `party.gold_in_transit > 0`, format `GP` as `{gold} (+{gold_in_transit} transit)`; `Awaiting` = top-level `status.awaiting` | F1 |
| **F3** | **Combat subset:** when `status.get("combat")` is truthy, insert `\| Turn: {turn_id}` before `\| Awaiting:` using `combat.turn_id` (fallback `combat.get("actor")` or `"?"` if absent) | F1 |
| **F4** | **Extend status strip:** broaden `_LLM_STATUS_TAG_RE` (or sibling) to remove **full bracket lines** matching exploration footer shape — tokens `Location`, `Phase`, `HP`, `Fortune`, `GP`, `Turn`, `Awaiting` inside `[…]` — in addition to existing APP-073 patterns | `creation.py` `strip_llm_status_tags` |
| **F5** | **`strip_llm_meta_narration(text) -> str`** — remove LLM meta leaks: `**Campaign Memory Updated:**` (and variants), horizontal-rule blocks whose sole content is memory/campaign update banners; trim trailing `---` + empty update stubs | `creation.py` |
| **F6** | **`_compose_exploration_narration(prose, *, gate_active: bool) -> str`** — after APP-024 sanitizer + refusal line: `strip_llm_status_tags` → `strip_llm_meta_narration` → append `\n\n` + `format_exploration_status(self.bridge.status())`; **always** append footer when not early-return refusal-only edge (see F7) | `orchestrator.py` |
| **F7** | **Empty body after strip:** if prose empty after F6 strips (and not APP-024 refusal-only path that already set code refusal line), still append footer — never emit bracket-only with no prose unless entire turn is code-only refusal/failure prefix | F6 |
| **F8** | **Idempotent compose:** strip matches F4 bracket shape before append so double-compose (`process_turn` + `all_failed` inner path) yields exactly one footer | F6 |
| **F9** | **Wire emit paths:** (a) `process_turn` post-`_llm_loop` — already calls compose; (b) `_llm_loop` `all_failed and content` — compose must be complete inside helper; (c) `_combat_turn` — compose before every `_emit_narration` on LLM narration returns (`_combat_llm_loop` success, `_narrate_text` combat end/monster paths); **skip** code-only paths (`[Mechanics failed — …]` only, `_handle_player_death` boilerplate) | `orchestrator.py` |
| **F10** | **`system_prompt.py`:** remove mandatory “Include state line” / Response Format bracket mandate; instruct: *“The client appends an authoritative status line from the engine — do not emit `[Location: …]` or `Awaiting:` tags in your prose.”* Keep combat `turn_id` / tool rules unchanged | `system_prompt.py` |
| **F11** | **Optional drift:** before strip, if prose contained bracket `Phase`/`Awaiting`/`GP` disagreeing with engine, call `log_exploration_drift({...})` — telemetry only | `logger.py`, compose or `_emit_narration` exploration branch |
| **F12** | **`TurnTruth` verify rule (future):** APP-083 universal rule “no fake status tags in flavor” — APP-077 strip is defense-in-depth until Phase 2 verify ships | doc only |

### Compose order (exploration + combat, after APP-077)

1. `sanitize_premature_site_entry_flavor` (APP-024) when `gate_active`
2. APP-024 refusal line if gate active and body empty
3. `strip_llm_status_tags` (APP-073 + F4 broad bracket)
4. `strip_llm_meta_narration` (F5)
5. Append `format_exploration_status(fresh bridge.status())` (F1–F3)

**Prefix paths (APP-022 / APP-028):** `[Mechanics failed — …]` and APP-022 hint insert **before** step 1 content in `_llm_loop`; composed tail still runs steps 1–5 on assistant `content` portion, then rejoin prefix + hint + composed body + footer.

**APP-083 / APP-089 ordering:** when verify gate lands, **verify pass → then compose (024 + 077)** — unchanged from domain spec APP-089 draft.

### Footer shape (normative)

**Exploration (non-combat):**

```text
[Location: {location} | Phase: {phase} | HP: {hp} | Fortune: {fortune} | GP: {gp} | Awaiting: {awaiting}]
```

**Combat active:**

```text
[Location: {location} | Phase: {phase} | HP: {hp} | Fortune: {fortune} | GP: {gp} | Turn: {turn_id} | Awaiting: {awaiting}]
```

Reference implementation seed: `_auto_finalize` footer at `orchestrator.py` L1992 (creation handoff — shape only, not creation compose path).

## Acceptance criteria mapping

| Ticket AC | Spec / test |
|-----------|-------------|
| Exploration footer contract documented | Domain spec § APP-077; F1–F2 |
| Combat footer contract when `combat.active` | F3; domain spec combat row |
| `format_exploration_status` golden snapshot | F1 — `test_exploration_status_footer.py` |
| `_compose_exploration_narration` strip + single footer | F6–F8 — unit tests |
| Meta leak strip | F5 — unit fixture `Campaign Memory Updated` |
| Empty body still gets footer | F7 — unit test |
| Wire `_llm_loop` + combat success paths | F9 — integration test |
| Prompt: client appends state | F10 |
| Optional `log_exploration_drift` | F11 |
| Wrong GP integration test | Mock LLM bad GP in prose; footer shows engine gold only |

## Test plan

```bash
python -m pytest app/tests/test_exploration_status_footer.py -q
python -m pytest app/tests/test_exploration_site_entry_gate.py -q   # APP-024 regression
python -m pytest app/tests/test_exploration_set_phase_delve_hint.py -q
python -m pytest app/tests/test_creation_flavor_sanitize.py -q -k status  # APP-073 regressions
```

**Primary new tests** (`app/tests/test_exploration_status_footer.py`):

| Test | Setup | Pass |
|------|-------|------|
| `test_format_exploration_status_golden` | Fixture `status` dict (surface + delve + combat variants) | Exact bracket strings per F2–F3 |
| `test_format_exploration_status_gp_transit` | `gold=61`, `gold_in_transit=12` | `GP: 61 (+12 transit)` |
| `test_strip_llm_status_tags_exploration_bracket` | Prose with full exploration bracket + inline `Awaiting:` | No bracket tokens in body |
| `test_strip_llm_meta_narration` | Prose ending `---\n**Campaign Memory Updated:**` | Meta removed; scene prose kept |
| `test_compose_exploration_single_footer` | `_compose_exploration_narration` with embedded wrong GP bracket | One footer; GP matches engine not LLM |
| `test_compose_empty_body_still_footer` | Strip-all input + gate inactive | Footer present |
| `test_compose_app024_refusal_plus_footer` | Gate active, entry fiction stripped to refusal | Refusal prose + footer |
| `test_compose_idempotent_double_call` | Call compose twice on same string | Single footer |
| `test_combat_turn_compose_wrong_gp` | Mock `_combat_llm_loop` return with bad bracket | Composed emit shows engine GP; includes `Turn:` when combat dict present |

Use patched `bridge.status()` fixtures — no live workspace required.

## Expected files (implementation)

- `app/gm/creation.py` — `format_exploration_status`, extend `strip_llm_status_tags`, `strip_llm_meta_narration`
- `app/gm/orchestrator.py` — `_compose_exploration_narration`; combat wire (F9)
- `app/gm/system_prompt.py` — F10 prompt edits
- `app/gm/logger.py` — optional `log_exploration_drift` (F11)
- `app/tests/test_exploration_status_footer.py` — **new**
- `tmp/app-exploration-delve-spec.md` — § APP-077 + changelog on close
- `tmp/app-llm-orchestrator-spec.md` — § APP-077 compose cross-link

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- **Surface travel / delve:** Narration ends with one bracket line; GP matches stats panel / sheet — not a number the GM invented in prose.
- **Combat turn:** Footer includes `Turn:` matching combat HUD; wrong LLM GP in middle of prose does not appear in footer region.
- **Failed tools + content:** `[Mechanics failed — …]` turns still show code footer after safe content.
- **Meta leak:** No `Campaign Memory Updated` banner visible after turns (engine handles memory silently).
- **APP-024 regression:** Refusal line turns still show footer; no bracket-only empty narration.

## Pointers

- **Research:** [research-brief.md](./research-brief.md) — code paths A–F, GP ambiguity, combat emit gaps, idempotency
- **Domain truth:** [tmp/app-exploration-delve-spec.md](../../../app-exploration-delve-spec.md) § Code-owned status footer (APP-077)
- **Orchestrator cross-link:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md) § Code-owned exploration/combat status footer (APP-077)
- **Related:** APP-007/073 (creation pattern), APP-024 (compose order), APP-041 (TTS), APP-065 (chips), APP-087 (footer-only turns)

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | Initial PM draft — footer mapping, meta strip, compose order, combat wire, prompt policy, test matrix |
