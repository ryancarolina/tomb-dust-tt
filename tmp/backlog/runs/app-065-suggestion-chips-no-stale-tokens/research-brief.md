# Research Brief: app-065-suggestion-chips-no-stale-tokens

**Date:** 2026-05-20
**Question:** Why do suggestion chips show internal `Awaiting:` tokens and stay stale after creation finalize? What should replace narration scraping as the chip source-of-truth?

**backlog_ticket:** APP-065
**ticket_path:** tmp/backlog/app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md
**domain_spec:** tmp/app-pygame-ui-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket **Domain spec** is [`tmp/app-pygame-ui-spec.md`](../../../app-pygame-ui-spec.md), which owns `app/ui/**` and already lists APP-065 under Input panel behavior and open work. [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **PyGame UI** maps to that spec. Secondary touchpoints (optional orchestrator wiring, creation prompt vocabulary) stay within ticket **Expected files** — no new domain spec required. PM will expand the pygame-ui spec with chip source-of-truth and blocklist rules per AC.

## Summary

Suggestion chips are built in `app/ui/app.py` by regex-scraping GM narration for `[…Awaiting: …]` and pushing the raw token(s) into `InputBox.set_suggestions`. Two independent bugs drive the Bumpy repro:

1. **Stale chips:** After each turn, suggestions update only when `_extract_suggestions(narration)` is non-empty (`if suggestions:` guard). When post-finalize narration omits a bracketed `Awaiting:` line, parse returns `[]` and the UI **never clears** prior chips — the old `EQUIPMENT_CONFIRMATION` chip remains clickable.
2. **Internal tokens as chips:** Parsed values are shown and submitted verbatim. System prompt teaches LLMs to emit `[Location: … | Awaiting: TOKEN]`; creation code footers use granular labels (`EQUIPMENT_GOLD_CONFIRMATION`, `RECEPTION_CHOICE`, etc.). LLM drift can emit non-canonical labels (`EQUIPMENT_CONFIRMATION`, per APP-073). Any bracketed `Awaiting:` value becomes a chip — including engine FSM enums unsuitable as player input.

`play/tomb_gm/suggest.py` builds **CLI/LLM-context** prompts (`commands`, GM-facing `prompts` like “Collect [P1]…[P4] actions”) — not player-facing chip text. It has no per-creation-step player actions and cannot be dropped into the UI without a new curated map layer.

**Recommended fix:** (1) Always queue `set_suggestions` every turn (empty list clears stale chips). (2) Stop using narration as chip source. (3) Add code-owned player suggestion builder keyed by `creation.step` / `CREATION_STATUS_LABELS` during creation and by engine `awaiting` (+ optional combat/exploration maps) elsewhere; wire from `_process_turn` via orchestrator (needs `creation.step`, not in `bridge.status()` alone). (4) Document blocklist + curated map in `app-pygame-ui-spec.md`. Prefer implementing APP-073 before or with APP-065 if both touch creation footer/chip UX (batch board wave order).

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Chip parse + update gate | `app/ui/app.py` | `_extract_suggestions`, `_process_turn` L315–317, startup L141–146 |
| Chip widget | `app/ui/panels/input_box.py` | `set_suggestions`, `handle_click` — label == submit text |
| Creation status labels | `app/gm/creation.py` | `CREATION_STATUS_LABELS`, `format_creation_status()` — footer for drift/UI badge, not chips today |
| Equipment confirm copy | `app/gm/creation.py` | `format_equipment_summary`, `is_equipment_confirm` — player text “yes/ready”, not token |
| Narration compose | `app/gm/orchestrator.py` | `_compose_creation_narration`, `_auto_finalize` footer |
| Engine suggest | `play/tomb_gm/suggest.py`, `app/gm/bridge.py` | `build_suggest` / `handle_suggest` — coarse `awaiting` enums |
| LLM status instruction | `app/gm/system_prompt.py` L213 | Teaches bracket line with `Awaiting: NEXT` |
| Status parse (drift) | `app/gm/logger.py` | `parse_narration_status_line` — broader `Awaiting:` regex than UI |
| Tests | `app/tests/test_creation_flow.py`, `test_session_resume_failure.py` | Assert `Awaiting:` substrings in narration, not chips |

## Code-path traces

### Startup chips (hardcoded — correct pattern)

1. Entry: `App._init_orchestrator` (`app/ui/app.py:120–147`).
2. After orchestrator init, pushes `("suggestions", ["load game", "new game"])` or `["new game"]` based on `bridge.has_save()`.
3. Never goes through `_extract_suggestions`.
4. These are player-facing and remain valid until first `_process_turn` overwrites (or fails to clear).

### Turn loop — stale chip bug

1. Entry: `InputBox.handle_click` / Enter → `_submit` → `_process_turn` (`app/ui/app.py:250–268, 270–337`).
2. `narration = self._orchestrator.process_turn(text)`.
3. `status = self._orchestrator.get_status()` → `bridge.status()` only (no `creation.step`).
4. `suggestions = self._extract_suggestions(narration)`.
5. **Bug:** `if suggestions: self._ui_queue.put(("suggestions", suggestions))` — empty parse leaves prior `input_box.suggestions` untouched.
6. `_process_ui_queue` → `input_box.set_suggestions(data)` when message received.

### `_extract_suggestions` — internal token bug

```python
match = re.search(r"\[.*?Awaiting:\s*(.+?)\]", narration)
# splits on | or , ; returns up to 4 parts as chip strings
```

1. Requires `Awaiting:` **inside** square brackets (non-greedy `.*?`).
2. **Matches:** LLM bracket status lines; `[Awaiting: new game]` (`orchestrator.py:364`); `[Awaiting: NAME_INPUT]` when resume failure wraps footer (`orchestrator.py:356–357`).
3. **Often does not match:** Code creation footers — bare `Awaiting: EQUIPMENT_GOLD_CONFIRMATION` from `format_creation_status()` (no brackets). Post-finalize footer puts `Awaiting: RECEPTION_CHOICE` on a **second line outside** `[Location: …]` (`orchestrator.py:1221`) — parse returns `[]` → stale chips.
4. When LLM echoes full bracket line (system prompt format), raw token(s) become chips — e.g. `EQUIPMENT_CONFIRMATION`, `PLAYER_ACTIONS`, `COMBAT_TURN`.
5. `strip_llm_status_tags` in creation (`creation.py:82–85`) removes standalone `Awaiting:` lines and `[Location:…]` / `[Phase:…]` blocks but **not** combined `[Location: … | Awaiting: TOKEN]` — those survive into narration and feed the parser.

### `play/tomb_gm/suggest.py` — not a chip source today

1. Entry: `GameBridge.suggest()` → `handle_suggest` → `build_suggest(status, check, pending_gate)`.
2. Keys off coarse engine `awaiting`: `SETUP`, `CHARACTER_CREATION`, `ROSTER_SETUP`, `PLAYER_ACTIONS`, `COMBAT_TURN`, etc.
3. `prompts` are operator/GM hints (e.g. CHARACTER_CREATION: “GM rolls all dice — never ask players to roll”; PLAYER_ACTIONS: spell cast strings for GM beat workflow).
4. No mapping from granular creation labels (`SKILLS_INPUT`, `EQUIPMENT_GOLD_CONFIRMATION`) — engine stays `CHARACTER_CREATION` for entire desk (APP-066).
5. **Conclusion:** Reuse `suggest` **structure** (status-driven) but add app-layer **player chip map**; do not parse `suggest.prompts` blindly.

### Ticket repro (Bumpy, equipment → finalize)

1. Equipment step narration includes bracketed or LLM `Awaiting: EQUIPMENT_CONFIRMATION` (non-canonical; canon is `EQUIPMENT_GOLD_CONFIRMATION` in `CREATION_STATUS_LABELS`).
2. `_extract_suggestions` → chip `EQUIPMENT_CONFIRMATION`.
3. Player types “I am ready” → `is_equipment_confirm` matches → `_auto_finalize` runs.
4. Finalize narration: flavor + body + footer with `Awaiting: RECEPTION_CHOICE` on unbracketed second line — parser returns `[]`.
5. Stale chip remains; click submits `EQUIPMENT_CONFIRMATION` → creation handler rejects (wrong step / not confirm text).

## Existing specs & docs

- **Ticket domain spec:** `tmp/app-pygame-ui-spec.md` — Input row references APP-065; no chip source-of-truth or blocklist yet (PM task).
- **Related tickets:** APP-007 (code-owned status line), APP-036 (creation step badge from engine), APP-066 (engine vs granular awaiting), APP-073 (strip/wrong LLM awaiting labels — batch mate, impl before APP-065 preferred).
- **Prior research:** APP-066 notes APP-065 separately — granular footers are drift labels, not player chip text.
- **`app/README.md`:** Documents “Click suggestion → Send that action” — behavior must stay, source must change.

## Tests & commands

```bash
# Creation golden path (narration Awaiting asserts, no chip tests)
python -m pytest app/tests/test_creation_flow.py -q

# Resume / startup suggestion sources
python -m pytest app/tests/test_session_resume_failure.py -q

# Manual repro (ticket)
# cd app && python main.py
# new game → complete creation → at equipment confirm observe chip token
# confirm with "ready" → post-finalize: chip should clear (currently fails)
# click stale chip → invalid input (currently fails)

# After fix — add unit tests recommended:
# - build_player_suggestions(creation.step=EQUIPMENT_GOLD) → ["Yes, confirm", ...] not UPPER_SNAKE
# - _process_turn mock: narration without Awaiting → set_suggestions([])
```

## Risks & unknowns

- **`get_status()` gap:** UI only gets `bridge.status()`; granular chips need `orchestrator.creation.step` or new `orchestrator.get_player_suggestions()` — ticket lists `orchestrator.py` as optional Expected file.
- **Curated map completeness:** Only equipment confirm and startup have obvious chip pairs in ticket AC; other creation steps (race/class/skills) may be free-text only or need table-derived options — PM/spec should define per-step policy (empty chips OK).
- **Exploration/combat:** `PLAYER_ACTIONS` / `COMBAT_TURN` chips need design — map travel is click-driven; combat actions may be open-ended. Safer default: **no chips** unless mapped, never scrape LLM footer.
- **Display vs submit:** `input_box.py` uses one string for label and submit; ticket allows mapped submit text — only change panel if label ≠ submit.
- **APP-073 interaction:** Wrong LLM labels in narration may persist in footer text until APP-073; chip fix must not depend on narration cleanliness.
- **Regex false positives:** `[Awaiting: new game]` is valid player chip; blocklist must allow lowercase player phrases, block `UPPER_SNAKE_CASE` / known enum set.

## Raw notes

### `_extract_suggestions` vs code footers

| Footer shape | Example | Regex match? |
|--------------|---------|--------------|
| Bare code line | `Awaiting: SKILLS_INPUT` | No |
| Bracket wrap (resume fail) | `[Awaiting: NAME_INPUT]` | Yes → bad chip |
| Two-line finalize | `[Location: 32-C \| …]\nAwaiting: RECEPTION_CHOICE` | No → stale |
| LLM bracket status | `[Location: 32-C \| Phase: prep \| Awaiting: EQUIPMENT_CONFIRMATION]` | Yes → bad chip |
| Startup-style | `[Awaiting: new game]` | Yes → OK |

### `CREATION_STATUS_LABELS` (chip map keys)

| `creation.step` | Awaiting label | Ticket chip example |
|-----------------|----------------|---------------------|
| NAME | NAME_INPUT | (free text — likely no chips) |
| RACE | RACE_INPUT | — |
| ROLL_STATS | STATS_REVIEW | — |
| CLASS | CLASS_INPUT | — |
| SKILLS | SKILLS_INPUT | — |
| SPELL_SCHOOLS | SPELL_SCHOOLS_INPUT | — |
| SPELLS | SPELLS_INPUT | — |
| EQUIPMENT_GOLD | EQUIPMENT_GOLD_CONFIRMATION | `Yes, confirm` / `I need different gear` |
| FINALIZE | FINALIZE | — |
| WORLD_INTRO | RECEPTION_CHOICE | exploration actions TBD |

### Engine `awaiting` values (`cmd_core.py`)

`SETUP`, `SESSION_ENDED`, `CHARACTER_CREATION`, `ROSTER_SETUP`, `PLAYER_ACTIONS`, `COMBAT_TURN`, `DYING`, `DOWNED`, `BLOCKED`, `HUMAN_GATE` — all blocklist candidates if ever parsed from narration.

### Acceptance mapping

| Ticket AC | Research recommendation |
|-----------|-------------------------|
| Clear stale chips when extract empty | Unconditional `put(("suggestions", suggestions))` every turn — trivial |
| Never show internal tokens | Remove narration scrape; blocklist + curated map |
| Player-facing actions only | New `build_player_suggestions(orchestrator)` keyed by `creation.step` + engine `awaiting` |
| Equipment confirm examples | Map `EQUIPMENT_GOLD` → confirm/objection strings aligned with `format_equipment_summary` / `is_equipment_confirm` |
| Startup load/new game | Keep hardcoded init path; include in map for consistency |
| Click submits label/mapped text | Same string OK for v1; extend `input_box` only if label ≠ submit |
| Spec documents source-of-truth | Expand `app-pygame-ui-spec.md` Input section |

### Recommended impl shape (for Dev/PM)

1. `app/ui/suggestions.py` (or `app/gm/ui_suggestions.py`): `PLAYER_SUGGESTIONS_BY_CREATION_STEP`, `PLAYER_SUGGESTIONS_BY_AWAITING`, `_INTERNAL_TOKEN_RE` blocklist.
2. `Orchestrator.get_player_suggestions() -> list[str]` reads `self.creation` + `bridge.status()`.
3. `_process_turn`: replace `_extract_suggestions(narration)` with orchestrator method; always queue result.
4. Deprecate or delete `_extract_suggestions`.
5. Tests in `app/tests/test_ui_suggestions.py` (new) or extend creation flow with chip asserts at equipment + post-finalize.
