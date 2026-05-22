# APP-081: NPC gender-aware voice resolution for narration TTS

| Field | Value |
|-------|-------|
| **ID** | APP-081 |
| **Type** | feature |
| **Priority** | P2 |
| **Status** | cancelled |
| **Domain spec** | [`app-tts-narration-spec.md`](../app-tts-narration-spec.md) |
| **Created** | 2026-05-20 |

## Summary

TTS voice selection for NPC dialogue is **heuristic and brittle**. `parse_scene` (`play/tomb_gm/services/tts/scene.py`) maps quotes to voice keys via hard-coded `_SPEAKER_RULES` and prose patterns (`she says` → `npc-female`, else `npc-male`). `resolve_voice` (`voices.py`) then picks an edgeTTS voice from `config.yaml` `npc_voices` or guesses gender from the **voice key string** — not from canon NPC identity.

**Gap:** Named NPCs with known gender (e.g. **Mira Ashret** — female; **Marshal Garrick Holt** — male) can get the wrong voice when prose omits pronouns or when a generic key like `postern-clerk` matches the wrong default. The narration system should **resolve the speaking NPC**, look up **canon gender**, and select the matching male/female edge voice (with per-NPC overrides still winning).

## Current behavior (baseline)

| Layer | File | Behavior |
|-------|------|----------|
| Parse | `scene.py` | Quote → `voice` key via rules + `_FEMALE_PATTERNS` → often `npc-male` / `npc-female` |
| Resolve | `voices.py` | `npc_voices[key]` → else `_infer_gender(voice_key)` on key words → `npc_voice_default_male` / `_female` |
| Config | `app/config.yaml` | Explicit voices for a few ids; defaults `en-US-AndrewNeural` / `en-US-JennyNeural` |

## Acceptance criteria

### Canon NPC gender source

- [ ] Add a **machine-readable NPC voice registry** (recommended: `build/data/npcs/npcs.json` or equivalent) with at minimum: `id` (stable slug), `display_name`, `gender` (`male` \| `female` \| `neutral`), optional `voice_key` override.
- [ ] Seed registry from hub NPCs in `build/systems/npcs/` (e.g. `mira-ashret`, `marshal-garrick-holt`, `elder-marin`, `archivist-thessaly-vorn`, `lyra-the-stormcaller`) with gender aligned to canon prose.
- [ ] Document registry location and fields in domain spec; NPC markdown may add a **Voice** / **Gender** line in front matter or index table (human-readable mirror — optional stretch).

### Narration → voice pipeline

- [ ] `parse_scene` (or a shared helper) resolves detected speakers to **registry npc ids** where possible (extend `_SPEAKER_RULES` or replace with registry-driven name/alias patterns).
- [ ] Voice keys emitted for NPC lines prefer **stable npc ids** (e.g. `mira-ashret`) over generic `npc-male` / `npc-female` when identity is known.
- [ ] `resolve_voice` looks up registry **gender** (and optional per-NPC edge voice) before string-heuristic `_infer_gender`.
- [ ] Resolution order documented and tested: **config `npc_voices[id]`** → **registry explicit voice** → **registry gender → default male/female** → **prose heuristics** → **default male**.

### UI + panel consistency

- [ ] Narration panel voice coloring (`app/ui/theme.py` `VOICE_COLORS` / `VOICE_LABELS`) shows sensible display names for new npc ids (or falls back gracefully).
- [ ] NPC card speaker indicator reflects the resolved npc id during TTS playback (existing `speaker` queue events).

### Tests

- [ ] Unit tests: registry gender → correct edge voice for male and female npc ids without explicit `npc_voices` entry.
- [ ] Scene parse tests: quoted dialogue attributed to a named female NPC uses female voice even when surrounding prose has no `she`/`her`.
- [ ] Regression: existing `marshal-garrick-holt` / `postern-clerk` / `breley-sergeant` cases in `play/tomb_gm/tests/test_tts_scene.py` still pass (update expectations if voice keys change).

## Expected files

- `build/data/npcs/npcs.json` _(or agreed canon path)_ — npc id, gender, aliases
- `play/tomb_gm/services/tts/scene.py` — speaker detection → npc id
- `play/tomb_gm/services/tts/voices.py` — registry-aware `resolve_voice`
- `play/tomb_gm/services/tts/` — loader for npc registry (new module if needed)
- `app/config.yaml` — align `npc_voices` keys with registry ids; keep defaults
- `app/ui/theme.py` — optional display names/colors for hub npc ids
- `play/tomb_gm/tests/test_tts_scene.py` — gender + registry cases
- `tmp/app-tts-narration-spec.md`
- `build/systems/npcs/README.md` — optional gender/voice index column

## Spec sync (required on close)

1. Mark **Status** → `done` in this ticket (add **Closed** date).
2. Update [`app-tts-narration-spec.md`](../app-tts-narration-spec.md): § NPC voice resolution, registry schema, resolution order, config keys.
3. If cross-domain (canon NPC data), note in [`app-master-spec.md`](../app-master-spec.md) registry row if needed.

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-081 --task npc-gender-voice
python tmp/backlog/claim_ticket.py release APP-081 --done
```

## Notes

- **Cancelled (2026-05-22)** — superseded by [APP-084](app-084-key-npc-canon-registry.md). Do not implement.
- **Creation desk voice:** use **`isla-brack`** per APP-084 — not `postern-clerk`.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-043 | related — document voice keys in spec (can close together or APP-043 after 081) |
| APP-041 | related — strip status tags before TTS |
| APP-058 | related — runtime TTS mute toggle |
