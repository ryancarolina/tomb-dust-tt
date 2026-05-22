# Spec: APP-041-strip-status-tags-before-tts

**Status:** draft  
**backlog_ticket:** APP-041  
**ticket_path:** [tmp/backlog/app-041-strip-status-tags-before-tts.md](../../app-041-strip-status-tags-before-tts.md)  
**domain_spec:** [tmp/app-tts-narration-spec.md](../../../app-tts-narration-spec.md)  
**registry_gap:** false  
**Domain specs touched:** `tmp/app-tts-narration-spec.md`

## Problem

TTS synthesizes GM status metadata as spoken prose. `app/ui/app.py` calls `parse_scene(narration)` once per turn, passes the resulting `{text, voice}` lines to `speak_scene`, and queues the **raw** narration string for the panel. `play/tomb_gm/services/tts/scene.py` already drops whole metadata lines (`_SKIP_LINE`, line-start `Awaiting:`) and closed `[…]` blocks (`_strip_brackets`), but **inline** and **unbracketed** status still reach the speak payload:

| Input pattern | Spoken today? |
|---------------|---------------|
| Whole-line `[Location: … \| Phase: … \| Awaiting: …]` | No |
| Whole-line `Awaiting: RACE_INPUT` | No |
| Inline `The clerk nods. Awaiting: SKILL_INPUT` | **Yes** |
| Inline `Welcome [Location: 32-C \| Phase: desk] delver.` | No (bracket removed) |
| Unclosed `[Location: 32-C \| Phase: preparation` | **Yes** |
| Line `Phase: preparation` | **Yes** |
| Line `Location: 32-C \| Phase: delve \| Awaiting: TRAVEL` | **Yes** |

`strip_llm_status_tags()` in `app/gm/creation.py` runs at **creation compose** only; exploration/combat narration has no compose-time strip. APP-073 and APP-077 address display/compose drift; **APP-041** owns the **TTS choke point** so any status embedded in prose never reaches synthesis.

## Goals

- **Fiction-only speak payload:** no `Location:`, `Phase:`, or `Awaiting:` tokens (bracketed, inline, or whole-line) in any line passed to `speak_scene` / `synthesize_to_file`.
- **Single choke point:** harden `parse_scene` in `play/tomb_gm/services/tts/scene.py` — no duplicate strip in `app/ui/app.py`.
- **Panel unchanged:** narration panel continues to show the full orchestrator string including status footers.
- **Regression tests** in `play/tomb_gm/tests/test_tts_scene.py` for the research leak matrix.

## Non-goals

| Deferred | Owner |
|----------|--------|
| Strip status from creation **compose** flavor | [APP-073](../../app-073-strip-llm-embedded-status-tags-in-creation.md) |
| Code-owned exploration status **footer** at compose | [APP-077](../../app-077-code-owned-exploration-status-footer.md) |
| TTS interrupt on new turn | [APP-042](../../app-042-tts-stop-on-player-interrupt.md) |
| Import `app/gm/creation.py` from `play/tomb_gm` | Forbidden — engine-owned regex in `scene.py` |
| Change `narration_text` queue payload | Out of scope — display keeps tags |
| `text_only` mode behavior | Unchanged (no audio) |
| CLI `cmd_speak --text` / `--lines` | Dev-only bypass of `parse_scene` — may still speak raw status; out of scope (canonical play uses app → `parse_scene`) |

## Requirements

Full behavior contract: domain spec § **Status tag strip before TTS (APP-041)**.

### R1 — Engine status strip in `parse_scene`

Add `_strip_status_tags(text: str) -> str` in `play/tomb_gm/services/tts/scene.py` and invoke it inside `parse_scene` **after** `_strip_ui` and **before** `_strip_brackets` (order matters: remove inline tokens before bracket pass; whole-line drops can stay in `_strip_ui` / `_is_ui_metadata`).

**Must remove from remaining prose (anywhere in line):**

1. Closed bracket blocks: `\[Location:[^\]]*\]`, `\[Phase:[^\]]*\]` (same semantics as creation `_LLM_STATUS_TAG_RE`).
2. Inline `Awaiting:\s*[A-Z0-9_]+` (case-insensitive label; token uppercase/alnum/underscore).
3. Unclosed bracket status fragments: from `[` through end of line when line matches `\[?\s*Location:` or `\[?\s*Phase:` (covers malformed `[Location: 32-C \| Phase: preparation`).
4. Whole-line unbracketed status footers: lines matching `^\s*Location:\s*.+` or `^\s*Phase:\s*.+` or pipe-separated `Location:.*\|.*Phase:` (extend `_is_ui_metadata` / `_SKIP_LINE` — prefer line drop over inline sub if entire line is metadata).

**Must preserve:**

- AV-GRID addresses in fiction (e.g. `32-C-UG-1` in Holt scene) — do not drop lines solely because they contain a coordinate token unless the line is a status footer pattern above.
- Quoted dialogue and narrator prose after tag removal (collapse extra whitespace; `re.sub(r"\n{3,}", "\n\n", …)` if needed).

**Alignment note:** Patterns may mirror `app/gm/creation.py` `_LLM_STATUS_TAG_RE` but live in `play/` only; no cross-tree import.

### R2 — Display vs speak split (no UI change)

| Path | Payload | Strip? |
|------|---------|--------|
| `self._ui_queue.put(("narration_text", narration))` | Raw orchestrator string | **No** |
| `parse_scene(narration)` → `speak_scene(..., lines=…)` | Parsed lines | **Yes** (R1) |

`app/ui/app.py` `_process_turn` / `_speak_narration` wiring stays as-is; verification is behavioral (tests + manual listen), not a second strip call in `app/`.

### R3 — CLI / dev speak path

**In scope:** `cmd_narrate push` and `cmd_speak --scene` call `speak_scene(text)` without `lines` → `parse_scene` → R1 applies.

**Out of scope (non-goal):** `cmd_speak --text` and `cmd_speak --lines` pass pre-built `lines=[{"text": …}]` into `speak_scene`, which skips `parse_scene` entirely (`queue.py` uses `lines_from_payload` when `lines` is set). Dev/debug convenience only; canonical player path is `app/ui/app.py` → `parse_scene(narration)` → `speak_scene(..., lines=…)`. No requirement to strip `--text` / `--lines` payloads in APP-041.

### R4 — `speak_dialogue` / `speak_all`

`filter_for_mode` operates on already-sanitized lines; no new filter rules for status tags.

## Acceptance criteria mapping

| Ticket AC | Spec / verification |
|-----------|-------------------|
| Strip status tags before TTS speak payload | R1 — `parse_scene` output has zero status fingerprints (tests below) |
| Panel still displays status tags; strip on speak only | R2 — no edit to `narration_text` queue; manual playtest |

## Test plan

```bash
PYTHONPATH=play python -m pytest play/tomb_gm/tests/test_tts_scene.py play/tomb_gm/tests/test_tts.py -q
```

**New cases** in `play/tomb_gm/tests/test_tts_scene.py` (parametrize or one test per row):

| Fixture | Assert on `parse_scene` → concatenated spoken text |
|---------|------------------------------------------------------|
| `The clerk nods. Awaiting: SKILL_INPUT` | No `Awaiting` / `SKILL` token; clerk prose retained |
| `Welcome [Location: 32-C \| Phase: desk] delver.` | No `Location` / `Phase` / bracket residue; “Welcome … delver” |
| Unclosed `[Location: 32-C \| Phase: preparation` | Empty or prose without status fragment |
| Line `Phase: preparation` | Line omitted from output |
| Line `Location: 32-C \| Phase: delve \| Awaiting: TRAVEL` | Line omitted |
| Body + bracket footer + `Awaiting: RECEPTION_CHOICE` on separate lines | Body spoken; footer lines not spoken |
| `HOLT_SCENE` regression | Existing voice-split assertions still pass |

Optional: assert `filter_for_mode(..., "speak_all")` same guarantees.

## Expected files (implementation)

Ticket Expected files (hook allow-list):

- `play/tomb_gm/services/tts/scene.py` — `_strip_status_tags`, `parse_scene` pipeline, `_is_ui_metadata` / `_SKIP_LINE` extensions
- `play/tomb_gm/tests/test_tts_scene.py` — leak-matrix tests
- `tmp/app-tts-narration-spec.md` — § APP-041; changelog on close

**No required `app/` code change** if R1–R2 satisfied.

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; `cd app && python main.py`, `tts.mode: speak_all`._

- **Creation:** After a step with visible `Awaiting: …` in the narration panel, audio must **not** read “Awaiting”, step token, or bracket Location/Phase line.
- **Exploration:** Turn with LLM `[Location: … \| Phase: … \| Awaiting: …]` footer — panel shows footer; TTS reads fiction only.
- **Inline leak regression:** If LLM embeds `Awaiting: SKILL_INPUT` mid-sentence, panel may show it; TTS must not.

## Pointers

- **Research:** [research-brief.md](./research-brief.md) — traces A–D, leak matrix, `speak_scene` uses `lines` not raw `text`
- **Domain truth:** [tmp/app-tts-narration-spec.md](../../../app-tts-narration-spec.md) — § Status tag strip before TTS (APP-041)
- **Related:** APP-073 (compose), APP-077 (footer), APP-042 (interrupt)

## Changelog

| Date | Change |
|------|--------|
| 2026-05-21 | Initial PM draft — TTS-layer status strip in `scene.py`; display/speak split |
| 2026-05-21 | PM r2 — ticket Expected files + panel AC; R3 CLI `--text`/`--lines` documented as dev-only non-goal |
