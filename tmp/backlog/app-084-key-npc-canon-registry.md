# APP-084: Key NPC canon registry + TurnTruth verify

| Field | Value |
|-------|-------|
| **ID** | APP-084 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | open |
| **Domain spec** | [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md) (TurnTruth/verify); [`app-tts-narration-spec.md`](../app-tts-narration-spec.md) (voice/TTS); [`app-character-creation-spec.md`](../app-character-creation-spec.md) (Isla at desk); canon: `build/systems/npcs/` |
| **Created** | 2026-05-22 |

## Summary

Hub **key NPCs** (Isla, Holt, Mira, Marin, Thessaly, Lyra) anchor lore, services, and quest hooks, but identity is split across markdown prose, hard-coded TTS regex, ad hoc `config.yaml` voices, and **prompt-only** LLM instructions. The model can call Holt *she*, describe Mira as a knight, or rewrite personality session to session — nothing blocks it.

Introduce a **machine-readable key NPC registry** (`build/data/npcs/`) as the single source of truth for stable id, **canonical appearance/personality**, gender, archetype, hub, stats, aliases, and **fixed edgeTTS voice**. Wire TTS/UI to the registry **and** extend the APP-083 **TurnTruth → verify → retry → publish** pipeline so any narration mentioning a key NPC must match registry facts before the player sees it.

**Supersedes** [APP-081](app-081-npc-gender-voice-resolution.md) (cancel when this closes).

## Problem

| Layer today | Key NPC gap |
|-------------|-------------|
| Prompt | "Voice NPCs distinctly" — no canon card injected |
| TTS | Holt regex only; others generic |
| Verify (APP-083) | Creation catalogs only — **no NPC identity rules** |
| Exploration | `_llm_loop` → compose — **no verify gate** |

Key NPCs need the same treatment as creation spell catalogs: **truth in context, verify out, retry until pass**.

## Key NPC roster (v1 — hub catalog)

Indexed in [`build/systems/npcs/README.md`](../../build/systems/npcs/README.md).

| id | Display name | Hub | Gender | Archetype | Canon edge voice (proposed) |
|----|--------------|-----|--------|-----------|----------------------------|
| `isla-brack` | Clerk-Sergeant Isla Brack | Breley Keep (`32-C`) | female | registry intake clerk | `en-US-MichelleNeural` |
| `marshal-garrick-holt` | Marshal Garrick Holt | Breley (`32-C`) | male | knight / castellan | `en-US-SteffanNeural` |
| `mira-ashret` | Mira Ashret | Edgecombe (`24-A`) | female | registry clerk (satellite) | `en-US-AriaNeural` |
| `elder-marin` | Elder Marin | Edgecombe | male | sage / herbalist | `en-US-RogerNeural` |
| `archivist-thessaly-vorn` | Archivist Thessaly Vorn | Boydon Tower | female | archivist mage | `en-US-SaraNeural` |
| `lyra-the-stormcaller` | Lyra the Stormcaller | Skyreach / Boydon | female | storm mage | `en-US-AmberNeural` |

### Registry intake clerk — `isla-brack` (character creation)

**Decision:** Character creation at Breley Keep is **Isla Brack**, not Mira Ashret and not generic `postern-clerk`. Mira runs the Edgecombe satellite (maps, stamps, survivors); Isla runs **first-time delver intake** at the Keep's Registry window. The male `postern-clerk` in Holt quest fiction remains a **generic** postern gatekeeper — separate character.

| Field | Canon value |
|-------|-------------|
| **Full title** | Clerk-Sergeant Isla Brack, Registry Intake, Breley Keep |
| **Role** | Registers new delvers: name, lineage, class paperwork, kit issue — every **new game** |
| **Background** | Daughter of a Breley quartermaster. Failed field-medic certification after freezing on a hollow-knight triage drill. Transferred to Registry intake; now knows every form, every Eclipse-week superstition, and which names on the ledger came back from the undercrypt. |
| **Appearance** | Lean, late thirties; dark hair in a tight braid with a **single iron-grey streak**; **wire spectacles** on a cord; **ink-stained fingers**; **Registry brass stamp** on a chain; **Breley blue clerk's tabard** over a grey apron; counter-high desk stacked with triplicate forms. |
| **Personality** | Precise, dry, unsentimental — not cruel. Calls applicants *delver* until the name is inked. Patient with paperwork; **impatient with skipped lines**. Dry humor about Tomb Dust. **Superstitious during Eclipse week** (won't start a new ledger page after sundown). Warmth shows only when someone reads the form correctly the first time. |
| **Voice** | `en-US-MichelleNeural` — measured, clear, faint Breley accent; never breathy or timid |
| **Aliases** | `Isla Brack`, `Clerk Brack`, `Clerk-Sergeant Brack`, `the intake clerk`, `Registry clerk` _(creation context only — disambiguate from Mira at Edgecombe)_ |
| **vs Mira Ashret** | Isla = **intake** (never delved). Mira = **satellite senior clerk** (survived a woods map; stamps claims, insurance, survivor rolls). Isla sends completed registrations upstream; she does not sell map stamps. |
| **vs Holt** | Same Keep (`32-C`); Holt licenses **military** delves and garrison business. Isla handles **civilian Registry intake** — overlapping bureaucracy, different desk. |
| **appearanceAnchors** | `iron-grey streak`, `wire spectacles`, `Breley blue tabard`, `Registry brass stamp`, `ink-stained fingers`, `triplicate forms` |
| **forbiddenRoleTerms** | `knight`, `marshal`, `castellan`, `mage`, `archivist`, `sage`, `sergeant` _(military rank except her own clerk-sergeant title)_ |
| **Stat tier** | Ally — non-combatant (desk-bound; surrenders if forced) |

Draft markdown path: `build/systems/npcs/isla-brack.md` (add to README index under Breley / creation). **Full canon sync checklist:** § [Canon updates](#canon-updates-build) below.

---

### Generic roles (not key NPCs)

| voice key | Use |
|-----------|-----|
| `postern-clerk` | Male postern **gatekeeper** (Holt scene extras) — **not** creation desk |
| `breley-sergeant` | Breley garrison extras |
| `npc-male` / `npc-female` | Unknown speakers |

---

## System design

### Three enforcement surfaces (one registry)

```text
build/data/npcs/key_npcs.json
        │
        ├─► TurnTruth inject  — canonical card in LLM context when NPC in scope
        ├─► verify_narration  — block wrong gender/role/appearance before publish
        └─► TTS + UI          — stable voice id, display name, color
```

### Registry entry schema

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `id` | slug | yes | Stable key (`marshal-garrick-holt`) |
| `displayName` | string | yes | UI + prompts |
| `aliases` | string[] | yes | Speaker detection + truth scoping |
| `gender` | `male` \| `female` \| `neutral` | yes | Verify pronouns; TTS fallback |
| `pronouns` | string | yes | `he/him`, `she/her`, `they/them` — injected + verified |
| `archetype` | string | yes | Role tag (`knight`, `clerk`, …) — verify wrong-role claims |
| `appearance` | string | yes | **Canonical** physical description (1–2 sentences) |
| `personality` | string | yes | **Canonical** temperament (1–2 sentences) |
| `voiceNotes` | string | no | Narration hint ("commanding, gravelly") — prompt only |
| `hub` | string | yes | Primary settlement |
| `hubAddress` | AV-GRID id | no | e.g. `32-C` |
| `docPath` | string | yes | Markdown mirror path |
| `edgeVoice` | string | yes | Canonical edgeTTS voice |
| `appearanceAnchors` | string[] | no | Verify tokens that must not be contradicted (e.g. `burn-scarred left hand`) |
| `forbiddenRoleTerms` | string[] | no | Terms that violate archetype (Holt: `archivist`, `clerk`, `mage`) |
| `statBlock` | object | yes | d20 ally block |
| `factionIds` | string[] | no | Faction gates |
| `questIds` | string[] | no | Quest defs this NPC can offer ([APP-085](app-085-quest-system-key-npc-quests-ui.md)) |
| `isKeyNpc` | bool | yes | Always `true` in this file |

JSON wins over markdown on drift (AV-GRID policy).

Example (Holt):

```json
{
  "id": "marshal-garrick-holt",
  "displayName": "Marshal Garrick Holt",
  "aliases": ["Garrick Holt", "Holt", "Marshal Holt"],
  "gender": "male",
  "pronouns": "he/him",
  "archetype": "knight",
  "appearance": "Square jaw, burn-scarred left hand, Breley blue tabard over practical plate.",
  "personality": "Blunt, fair, superstitious about Eclipse week. Respects prepared parties; despises map-flippers.",
  "voiceNotes": "Commanding, clipped military diction.",
  "hub": "breley",
  "hubAddress": "32-C",
  "edgeVoice": "en-US-SteffanNeural",
  "appearanceAnchors": ["burn-scarred left hand", "Breley blue tabard", "square jaw"],
  "forbiddenRoleTerms": ["clerk", "archivist", "mage", "priestess", "merchant"],
  "docPath": "systems/npcs/marshal-garrick-holt.md",
  "isKeyNpc": true
}
```

Example (Isla — creation intake):

```json
{
  "id": "isla-brack",
  "displayName": "Clerk-Sergeant Isla Brack",
  "aliases": ["Isla Brack", "Clerk Brack", "Clerk-Sergeant Brack", "intake clerk", "Registry clerk"],
  "gender": "female",
  "pronouns": "she/her",
  "archetype": "registry intake clerk",
  "appearance": "Lean, late thirties; dark braid with a single iron-grey streak; wire spectacles on a cord; ink-stained fingers; Registry brass stamp on a chain; Breley blue tabard over grey apron.",
  "personality": "Precise, dry, unsentimental — not cruel. Patient with paperwork; impatient with skipped lines. Superstitious during Eclipse week.",
  "voiceNotes": "Measured, clear; faint Breley post cadence.",
  "hub": "breley",
  "hubAddress": "32-C",
  "edgeVoice": "en-US-MichelleNeural",
  "appearanceAnchors": ["iron-grey streak", "wire spectacles", "Breley blue tabard", "Registry brass stamp", "ink-stained fingers"],
  "forbiddenRoleTerms": ["knight", "marshal", "castellan", "mage", "archivist", "sage"],
  "docPath": "systems/npcs/isla-brack.md",
  "isKeyNpc": true
}
```

---

## Canon updates (`build/`)

**Required on close.** JSON registry and markdown canon must match; update cross-links so prose docs reflect Isla as the **creation intake clerk** and distinguish her from Mira (Edgecombe) and generic postern staff.

### New — Isla Brack

| File | Action |
|------|--------|
| [`build/systems/npcs/isla-brack.md`](../../build/systems/npcs/isla-brack.md) | **Create** — full hub NPC page (Role, Background, Appearance, Personality, stat block, services table, hooks, World ties with AV-GRID `32-C`, Key NPC header: id / gender / voice) using § Registry intake clerk canon above |
| [`build/data/npcs/key_npcs.json`](../../build/data/npcs/key_npcs.json) | **Add** `isla-brack` entry (source of truth; markdown mirrors JSON) |

### Update — NPC index & siblings

| File | Action |
|------|--------|
| [`build/systems/npcs/README.md`](../../build/systems/npcs/README.md) | Add Isla row; extend index columns: **id**, **Gender**, **Voice**; note *creation intake* vs hub services |
| [`build/systems/npcs/mira-ashret.md`](../../build/systems/npcs/mira-ashret.md) | Clarify **Edgecombe satellite only** — map stamps, insurance, survivors; **not** Breley new-delver intake; cross-link [isla-brack.md](isla-brack.md) |
| [`build/systems/npcs/marshal-garrick-holt.md`](../../build/systems/npcs/marshal-garrick-holt.md) | Cross-link Isla (same Keep, different desk); Key NPC header line when other pages updated |

### Update — locations & factions

| File | Action |
|------|--------|
| [`build/systems/locations/breley-keep.md`](../../build/systems/locations/breley-keep.md) | **NPCs:** add [Isla Brack](../npcs/isla-brack.md) (Registry intake) alongside Holt |
| [`build/systems/factions/delvers-registry.md`](../../build/systems/factions/delvers-registry.md) | Document **Breley Keep intake** (Isla) vs **Edgecombe satellite** (Mira); clerks list mentions both desks |
| [`build/systems/world/extraction.md`](../../build/systems/world/extraction.md) | Optional: *Registry clerk* row split — intake (Breley) vs claim desk (Edgecombe) |

### Update — remaining hub NPC pages (registry header sync)

| File | Action |
|------|--------|
| `build/systems/npcs/elder-marin.md` | Normalize format; add Key NPC id / gender / voice header; align stat block with JSON |
| `build/systems/npcs/archivist-thessaly-vorn.md` | Key NPC header + JSON sync |
| `build/systems/npcs/lyra-the-stormcaller.md` | Key NPC header + JSON sync |
| `build/systems/npcs/marshal-garrick-holt.md` | Key NPC header + JSON sync |
| `build/systems/npcs/mira-ashret.md` | Key NPC header + JSON sync |

### Validate

```bash
python build/tools/validate_content.py
```

- [ ] `key_npcs.json` validates against schema
- [ ] No orphan `docPath` entries
- [ ] Breley Keep + Registry faction pages link to `isla-brack.md`

---

## TurnTruth + verify (APP-083 extension)

### Extend `TurnTruth` (`app/gm/narration_verify.py`)

Add mode-aware key NPC slice:

```python
@dataclass
class KeyNpcTruth:
    id: str
    display_name: str
    gender: str
    pronouns: str
    archetype: str
    appearance: str
    personality: str
    appearance_anchors: tuple[str, ...]
    forbidden_role_terms: tuple[str, ...]

# On TurnTruth:
key_npcs_in_scope: tuple[KeyNpcTruth, ...] = ()
```

### Builders

| Builder | When | In-scope NPCs |
|---------|------|---------------|
| `build_creation_turn_truth` | Creation flavor | **`isla-brack` always** while `creation.active` (Registry desk, Breley Keep) |
| `build_exploration_turn_truth` | **New** — exploration `_llm_loop` final prose | NPCs at player's hub (`hubAddress` / location region) **plus** any id matched by alias in player input or draft prose |
| `build_combat_turn_truth` | Future | NPCs in combat roster / allied combatants only |

**Scoping rule (exploration v1):** Include key NPC if (a) player `location` maps to npc `hub` / `hubAddress`, or (b) alias appears in player input or LLM draft (post-hoc widen on retry).

### Prompt injection — `format_key_npcs_for_prompt(truths)`

When `key_npcs_in_scope` non-empty, append compact block:

```text
## Key NPCs in this scene (do not contradict)
- marshal-garrick-holt (Marshal Garrick Holt): male, he/him. Knight/castellan.
  Appearance: Square jaw, burn-scarred left hand, Breley blue tabard…
  Personality: Blunt, fair, superstitious about Eclipse week…
  Use this voice and identity whenever this character speaks or is described.
```

Inject into:
- Creation flavor messages (desk steps)
- Exploration system context before `_llm_loop` **and** on verify retry feedback
- Future combat narration pass

Also add a **system_prompt.py** bullet: *"When a key NPC from Current Game State appears, use their canonical appearance and personality — do not invent alternate versions."*

### Verify rules — `verify_key_npc_narration(prose, truths)`

Run when any key npc alias/id is detected in prose. Violations:

| Code | Rule |
|------|------|
| `npc_gender_mismatch:{id}` | Named NPC + wrong pronoun (`\bshe\b` for male id, `\bhe\b` for female id) within ±N chars of alias match |
| `npc_wrong_role:{id}:{term}` | `forbiddenRoleTerms` near alias (e.g. Holt called "the clerk") |
| `npc_appearance_contradiction:{id}:{anchor}` | Negation/contradiction of `appearanceAnchors` (e.g. "unmarked hands" when anchor is burn-scarred left hand) — use curated patterns per anchor, not open-ended NLP |
| `npc_invented_identity:{id}` | Prose assigns a **different** display name to an alias (e.g. "Garrick Holt, the elven bard") |

**Pass behavior:** Empty prose passes. Unmentioned NPCs in scope do not fail verify (prompt injection only).

Refactor `verify_narration(prose, truth)` to dispatch:

```python
if truth.mode == "creation":
    violations += _verify_creation_rules(...)
violations += _verify_key_npc_rules(prose, truth.key_npcs_in_scope)
```

### Publish gate — exploration (APP-083 Phase 2 partial)

Wire exploration narration through verify→retry (same caps as creation: `_narration_verify_max_retries`, `_narration_llm_max_attempts`):

```text
_llm_loop (tools) → draft prose
  → build_exploration_turn_truth + key npc scope
  → verify_narration
  → fail? retry LLM with violation list (exploration-only retry pass, no re-run tools)
  → pass? _compose_exploration_narration → emit
```

Exhaustion: strip offending sentences or ship minimal neutral fallback (*"The scene holds."*) — **never** publish prose that failed key NPC verify.

Log: `narration_verify_fail` / `pass` / `exhausted` with `mode: exploration` and `npc_violations`.

### TTS + UI (unchanged intent, registry-driven)

- `parse_scene`: registry alias rules → stable npc id voice key
- `resolve_voice`: config override → registry `edgeVoice` → gender default
- UI display names/colors from registry loader

Voice is **enforced in audio** by id; verify enforces **prose** matches gender/personality/appearance.

---

## Acceptance criteria

### Canon data (`build/`)

- [ ] **`build/systems/npcs/isla-brack.md`** created with full hub NPC template (see § Canon updates).
- [ ] **`build/data/npcs/key_npcs.json`** — all **six** key NPCs (incl. `isla-brack`) with `appearance`, `personality`, `pronouns`, `appearanceAnchors`, `forbiddenRoleTerms`, `edgeVoice`, stats.
- [ ] **`build/data/schemas/key-npc.schema.json`** + validate in `build/tools/validate_content.py`.
- [ ] **`build/systems/npcs/README.md`** — Isla indexed; id / gender / voice columns for all key NPCs.
- [ ] **`build/systems/locations/breley-keep.md`** — lists Isla + Holt.
- [ ] **`build/systems/factions/delvers-registry.md`** — Breley intake (Isla) vs Edgecombe (Mira) documented.
- [ ] **`build/systems/npcs/mira-ashret.md`** — explicitly not creation clerk; links to Isla.
- [ ] Remaining hub NPC markdown refreshed (Elder Marin format normalized); **JSON ↔ markdown stat blocks aligned**.

### TurnTruth + verify

- [ ] `KeyNpcTruth` + loader from registry (`play/tomb_gm/.../key_npcs.py` or shared `app/gm/key_npcs.py`).
- [ ] `build_creation_turn_truth` includes **`isla-brack`** on all desk steps; orchestrator flavor prompts name Isla, not generic "clerk".
- [ ] `build_exploration_turn_truth(status, player_input, draft_prose?)` scopes hub + alias NPCs.
- [ ] `format_key_npcs_for_prompt()` injected in creation flavor + exploration context.
- [ ] `verify_key_npc_narration()` with gender, role, appearance-anchor, invented-identity rules.
- [ ] Exploration final prose passes through verify→retry before `_compose_exploration_narration`.
- [ ] JSONL events include npc violation codes on fail.

### TTS + UI

- [ ] Registry-driven `parse_scene` aliases + `resolve_voice`.
- [ ] UI speaker labels/colors from registry.

### Tests

- [ ] Unit: Holt prose with `she/her` → `npc_gender_mismatch:marshal-garrick-holt`.
- [ ] Unit: Holt called "the archivist" → `npc_wrong_role`.
- [ ] Unit: Holt "unmarked hands" with burn-scar anchor → `npc_appearance_contradiction`.
- [ ] Unit: Isla creation flavor with `he/him` → `npc_gender_mismatch:isla-brack`.
- [ ] Unit: Isla called "the marshal" → `npc_wrong_role`.
- [ ] Integration: exploration turn with Holt at Breley — retry loop fires on gender violation, second draft passes.
- [ ] TTS: alias → stable id → `edgeVoice`; Holt regression green.

### Spec + backlog

- [ ] `app-character-creation-spec.md`: creation desk face is **Isla Brack** (`isla-brack`); generic "clerk" wording updated.
- [ ] `app-llm-orchestrator-spec.md`: § Key NPC TurnTruth, verify rules, exploration partial Phase 2.
- [ ] `app-tts-narration-spec.md`: registry schema, voice resolution order.
- [ ] Cancel APP-081; **APP-043 cancelled** — voice docs land in APP-084 TTS spec pass.

## Expected files

### Canon (`build/`)

- `build/systems/npcs/isla-brack.md` _(new — creation intake clerk)_
- `build/systems/npcs/*.md` — all six key NPC pages + `README.md`
- `build/systems/locations/breley-keep.md`
- `build/systems/factions/delvers-registry.md`
- `build/data/npcs/key_npcs.json`
- `build/data/schemas/key-npc.schema.json`
- `build/data/npcs/README.md`
- `build/tools/validate_content.py`

### App / engine
- `app/gm/key_npcs.py` _(loader — shared by verify + optional re-export to play/tomb_gm)_
- `app/gm/narration_verify.py` — KeyNpcTruth, builders, verify rules
- `app/gm/orchestrator.py` — exploration verify gate, creation truth scope
- `app/gm/context.py` — key npc block in exploration context
- `app/gm/system_prompt.py` — key npc instruction line
- `play/tomb_gm/services/tts/scene.py`, `voices.py`, `key_npcs.py`
- `app/tests/test_key_npc_verify.py` _(new)_
- `play/tomb_gm/tests/test_tts_scene.py`, `test_key_npcs.py`
- `app/config.yaml`, `app/ui/theme.py`, `app/ui/panels/npc_card.py`
- `tmp/app-llm-orchestrator-spec.md`, `tmp/app-tts-narration-spec.md`, `tmp/app-character-creation-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done`, set **Closed** date.
2. Changelog in orchestrator, TTS, and **character-creation** specs.
3. **`build/` canon checklist** (§ Canon updates) complete — `validate_content.py` clean.
4. App/engine pytest commands from specs green.

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-084 --task key-npc-turn-truth
python tmp/backlog/claim_ticket.py release APP-084 --done
```

## Notes

- **Appearance verify is anchor-based, not semantic** — curate `appearanceAnchors` per NPC; avoid fuzzy "looks different" detection in v1.
- **Personality** is primarily **prompt-injected** in v1; optional v2: `personalityAnchors` denylist (e.g. Holt must not be "timid" / "sycophantic").
- **Creation desk:** **`isla-brack`** only — replace generic "Registry clerk" / `postern-clerk` in creation path, TTS, UI, verify. Keep `postern-clerk` for Holt postern gatekeeper fiction.
- **Out of scope:** Every NPC in the setting; LLM-invented minor extras; combat ally FSM turns; portrait assets.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-083 | extends — Phase 2 partial (exploration verify scoped to key NPCs + hub truth); coordinate with APP-084 — avoid duplicate verify modules |
| APP-085 | related — `questIds[]` on NPC registry; Isla is creation NPC not quest giver |
| APP-081 | superseded |
| APP-043 | superseded — cancelled; voice docs in APP-084 |
| APP-041 | related — TTS strip must not regress |
| APP-077 | related — exploration footer still separate; verify runs on body prose |
