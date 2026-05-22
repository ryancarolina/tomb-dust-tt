# Research Brief: APP-041-strip-status-tags-before-tts

**Date:** 2026-05-21  
**Question:** Where does narration become TTS audio, and which status tags (`[Location:…]`, `[Phase:…]`, `Awaiting:`) still reach the speak payload today?

**backlog_ticket:** APP-041  
**ticket_path:** tmp/backlog/app-041-strip-status-tags-before-tts.md  
**domain_spec:** tmp/app-tts-narration-spec.md  
**ticket_status_at_start:** in_progress  

**registry_gap:** false

## Registry gap justification

[`tmp/app-tts-narration-spec.md`](../../../app-tts-narration-spec.md) is the registered owner for TTS integration, voice config, and narration panel behavior ([`tmp/app-master-spec.md`](../../../app-master-spec.md) § Spec registry — **TTS & narration** → `play/tomb_gm/services/tts/`). APP-041 expected files (`app/gm/tts or narration layer`) are imprecise but map to this domain; no new domain spec row is required.

## Summary

TTS is triggered only from the PyGame client after each orchestrator turn. `orchestrator.process_turn()` returns the full narration string (including code-owned footers and LLM status lines). `app/ui/app.py` displays that raw string in the narration panel, calls `parse_scene(narration)` once, and passes the resulting line list into `speak_scene()` in a background thread. **`speak_scene` synthesizes from parsed `{text, voice}` lines, not the raw narration string** when `lines` is provided.

Sanitization today lives in `play/tomb_gm/services/tts/scene.py`: `_strip_ui` drops whole metadata lines (including line-initial `Awaiting:`), then `_strip_brackets()` removes closed `[…]` blocks before voice splitting. That path **already strips well-formed bracket footers** (e.g. creation `WORLD_INTRO` footer) but **leaks** inline `Awaiting: TOKEN`, unbracketed `Location: … | Phase: …` lines, and malformed/unclosed `[Location:…` fragments. `strip_llm_status_tags()` in `app/gm/creation.py` runs at **compose time** for creation flavor only; exploration/combat narration has no equivalent pre-TTS strip (APP-077 is display-layer footer work, not TTS).

Fix should target the TTS payload choke point (`parse_scene` and/or a shared strip helper invoked from `app/ui/app.py` before `speak_scene`), add `play/tomb_gm/tests/test_tts_scene.py` coverage for status-tag fixtures, and update ticket **Expected files** to include `play/tomb_gm/services/tts/scene.py` (and `app/ui/app.py` if wiring changes).

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Turn → narration | `app/gm/orchestrator.py` | `process_turn` → `_emit_narration`; creation via `_compose_creation_narration`; exploration via `_compose_exploration_narration` (APP-024 strip only; APP-077 footer not landed) |
| Creation status strip (compose) | `app/gm/creation.py` | `strip_llm_status_tags`, `format_creation_status` — **not** on TTS path |
| UI TTS trigger | `app/ui/app.py` | `_process_turn` L289–332; `_speak_narration` L344–375 |
| Narration display | `app/ui/panels/narration.py` | Shows full text via `narration_text` queue — status tags **intentionally visible** |
| Scene parse / strip | `play/tomb_gm/services/tts/scene.py` | `parse_scene`, `_strip_ui`, `_strip_brackets`, `_SKIP_LINE`, `filter_for_mode` |
| Speak queue | `play/tomb_gm/services/tts/queue.py` | `speak_scene` — uses `lines` arg when provided |
| TTS config | `app/config.yaml` | `tts.mode`: `speak_all` \| `speak_dialogue` \| `text_only` |
| LLM status prompt | `app/gm/system_prompt.py` | Instructs `[Location: … \| Phase: … \| Awaiting: …]` on exploration/combat turns |
| CLI (dev only) | `play/tomb_gm/cli/cmd_speak.py`, `cmd_narrate.py` | Same `speak_scene` / `parse_scene` stack |
| Tests (gap) | `play/tomb_gm/tests/test_tts_scene.py` | Voice split + session-block skip; **no** status-tag strip assertions |
| Related tickets | APP-073 (creation compose strip), APP-077 (exploration footer), APP-042 (interrupt) | APP-041 is TTS-layer; complementary to APP-073/077 |

## Code-path traces

### A — Player turn → TTS (canonical app path)

1. **Entry:** `app/ui/app.py` `_submit` → `_process_turn(text, turn_id)` (background thread).
2. **Narration:** `self._orchestrator.process_turn(text)` → `str` (creation / exploration / combat branches in `orchestrator.py`).
3. **Parse once:** `parse_scene(narration)` → `list[{text, voice}]` (`scene.py` L184–203).
4. **Display:** `_ui_queue.put(("narration_text", narration))` — **unfiltered** full string.
5. **TTS gate:** if `tts.mode != "text_only"`, spawn `_speak_narration(narration, lines, turn_id)`.
6. **Speak:** `_speak_narration` → `filter_for_mode(lines, mode)` for speaker UI hints → `speak_scene(text, lines=speak_lines, …)` (`queue.py` L35–36 uses `lines_from_payload(lines)`, **not** re-parsing `text`).
7. **Synth:** per line `synthesize_to_file(line["text"], …)` → `play_file_blocking`.
8. **Interrupt:** `_submit` calls `request_stop()` when `_turn_state == "speaking"` (APP-042 scope).

### B — `parse_scene` sanitization order

1. `_normalize_quotes(text)`
2. `_strip_ui` — drop metadata lines (`_SKIP_LINE`, tables, `[P1]`, line-start `Awaiting`, bare `Phase`/`Location` labels, phase keywords)
3. `_strip_brackets` — `re.sub(r"\[[^\]]*\]", "", text)` on **remaining** prose
4. `_strip_markup` — markdown chars; `_` → space (turns `SKILL_INPUT` → `SKILL INPUT` in spoken text)
5. Split paragraphs → quote-aware voice lines → `_merge_adjacent`

### C — Creation compose (upstream, not TTS)

1. `_compose_creation_narration(flavor, body[, footer])` (`orchestrator.py` L896–931).
2. `strip_llm_status_tags(flavor)` + race/stats strippers + premature-completion sanitizer.
3. Append code `body` + `format_creation_status()` or explicit `footer` (e.g. `WORLD_INTRO` bracket block + `Awaiting: RECEPTION_CHOICE`).
4. Return string → trace A. Footer lines are stripped at TTS if bracketed or line-start `Awaiting:`; inline leaks in flavor survive to TTS.

### D — Exploration / combat (upstream)

1. `_llm_loop` → optional `_compose_exploration_narration` (site-entry fiction strip only).
2. LLM may emit full bracket status line per `system_prompt.py` — usually removed by `_strip_brackets` in trace B.
3. No `strip_llm_status_tags` on exploration prose today; APP-077 will add code footer at compose (display/drift), still relies on TTS strip for anything embedded in prose.

## Existing specs & docs

- **Ticket domain spec:** [`tmp/app-tts-narration-spec.md`](../../../app-tts-narration-spec.md) — requires “Fiction-only text to TTS (no roll math, no `[Awaiting:` tags)”; checklist open for APP-041.
- **Master registry:** [`tmp/app-master-spec.md`](../../../app-master-spec.md) — TTS & narration row cites `play/tomb_gm/services/tts/`.
- **Ticket grooming note:** partial strip in `scene.py`; bracket tags in body “may still reach TTS” — confirmed for **non-bracket / inline** forms.
- **APP-077:** code-owned exploration footer — compose layer; does not replace TTS strip.

## Tests & commands

```bash
# Engine TTS unit tests (no status-tag coverage today)
PYTHONPATH=play python -m pytest play/tomb_gm/tests/test_tts_scene.py play/tomb_gm/tests/test_tts.py -q

# Reproduce leak matrix (local probe used during research)
PYTHONPATH=play python -c "from tomb_gm.services.tts.scene import parse_scene, filter_for_mode; ..."

# Manual: speak_all after creation/exploration turn — listen for Location/Phase/Awaiting
cd app && python main.py
```

**Verified leak matrix (`parse_scene` → `speak_all`):**

| Input pattern | Spoken? |
|---------------|---------|
| Whole-line `[Location: … \| Phase: … \| Awaiting: …]` | No (brackets stripped / empty line dropped) |
| Whole-line `Awaiting: RACE_INPUT` | No (`_SKIP_LINE`) |
| Inline `The clerk nods. Awaiting: SKILL_INPUT` | **Yes** — reads “Awaiting: SKILL INPUT” |
| Inline `Welcome [Location: 32-C \| Phase: desk] delver.` | No (bracket removed) |
| Unclosed `[Location: 32-C \| Phase: preparation` | **Yes** — full fragment |
| Line `Phase: preparation` | **Yes** |
| Line `Location: 32-C \| Phase: delve \| Awaiting: TRAVEL` | **Yes** |
| `WORLD_INTRO`-style body + bracket footer + `Awaiting: RECEPTION_CHOICE` | Body only; footer stripped |

## Risks & unknowns

- **Expected files mismatch:** ticket lists `app/gm/tts or narration layer` (path does not exist); real choke point is `play/tomb_gm/services/tts/scene.py` + `app/ui/app.py`. PM should widen Expected files or document engine ownership in domain spec file map.
- **Inline / unbracketed tags:** primary user-reported leak class; `_strip_brackets` and line-based `_SKIP_LINE` do not cover it.
- **Duplication with APP-073:** `strip_llm_status_tags` regex is compose-only; TTS needs its own strip or a shared utility imported by both layers (watch import direction: `play/` should not depend on `app/gm/`).
- **APP-077 interaction:** code exploration footer may add bracket lines TTS already drops; risk is **residual inline status** in LLM prose until both tickets land.
- **Underscore → space:** `_strip_markup` may leave spoken “Awaiting: SKILL INPUT” even after tag removal unless strip runs before markup or pattern accounts for `_`.
- **No pytest guard:** regression likely without new tests in `test_tts_scene.py`.
- **Display vs speak split:** panel should keep status footers; strip must apply only to TTS payload, not `narration_text` queue.

## Raw notes

- `speak_scene(text, lines=…)` ignores `text` for ordering when `lines` is non-empty (`queue.py` L35).
- `_LLM_STATUS_TAG_RE` (`creation.py` L98–100): `\[Location:…\]`, `\[Phase:…\]`, `Awaiting:\s*[A-Z0-9_]+` — broader than TTS `_strip_brackets` for inline Awaiting but creation-only today.
- `format_creation_status` returns `Awaiting: {label}` without brackets (`creation.py` L654–657); whole-line form is TTS-safe via `_SKIP_LINE`.
- `_auto_finalize` / `WORLD_INTRO` uses explicit bracket footer (`orchestrator.py` L1500) — TTS probe confirms body spoken without footer.
- Batch board: APP-041 grouped with APP-079, APP-083 (`status.md`).
- Domain spec file map omits `app/ui/app.py` and `play/tomb_gm/services/tts/scene.py` — drift to fix on close.
