# Tomb Dust — Game Readiness Backlog

Backlog derived from the game-readiness gap analysis (May 2026). Goal: make the rules **implementable** before any electronic game architecture work.

**Status key:** `todo` · `in_progress` · `done` · `blocked`

**Priority key**

| Priority | Meaning |
|----------|---------|
| **P0** | Blocks a rules engine or reference sim |
| **P1** | Blocks a playable vertical slice (combat + extract + persist) |
| **P2** | Content polish, world scale, or pipeline quality |

**Recommended order:** Epic 1 ✅ → Wave 2 in progress → Epic 4/5/6/9 → 7/8/10

**Multitask status (2026-05-18):** E1 ✅ · Wave 2–5 ✅ · Wave 6 ✅ (expanded magic, encounters, ledger, NPC services, **M7 game-ready**)

**Game architecture green light:** [game-ready-checklist.md](game-ready-checklist.md)

---

## Epic index

| Epic | Name | Stories | Priority |
|------|------|---------|----------|
| [E1](#epic-e1--rules-canon--consolidation) | Rules canon & consolidation | TD-001 – TD-006 | P0 |
| [E2](#epic-e2--combat-loop) | Combat loop | TD-010 – TD-016 | P0 |
| [E3](#epic-e3--equipment--items) | Equipment & items | TD-020 – TD-024 | P0 |
| [E4](#epic-e4--magic-system) | Magic system | TD-030 – TD-035 | P0 |
| [E5](#epic-e5--character-creation--progression) | Character creation & progression | TD-040 – TD-046 | P0–P1 |
| [E6](#epic-e6--extraction-meta-game) | Extraction meta-game | TD-050 – TD-057 | P0–P1 |
| [E7](#epic-e7--world-data--av-grid) | World data & AV-GRID | TD-060 – TD-065 | P1 |
| [E8](#epic-e8--content-completion) | Content completion | TD-070 – TD-077 | P1–P2 |
| [E9](#epic-e9--data-layer--engine-readiness) | Data layer & engine readiness | TD-080 – TD-086 | P0–P1 |
| [E10](#epic-e10--repo--integration-contract) | Repo & integration contract | TD-090 – TD-092 | P1 |

---

## Epic E1 — Rules canon & consolidation

Align all `systems/` prose to the d20 canon in `core/` and `combat/calculations.md`. Nothing else is trustworthy until this epic closes.

### TD-001 — Publish canonical skill bonus rules

**Priority:** P0 · **Status:** todo · **Depends on:** —

**Story:** As a rules engineer, I want one authoritative skill-bonus table referenced everywhere, so that attack and check math is deterministic.

**Acceptance criteria**
- [ ] `combat/calculations.md` skill-bonus table is declared **canon** in `core/README.md` or `AGENTS.md`
- [ ] Every skill file uses “skill bonus” (tier table), not “+1 per level” on checks/attacks
- [ ] Damage formulas distinguish **skill bonus** (roll) vs **skill level** (techniques only, if any)
- [ ] Grep for `Each level provides \+1` in `systems/skills/` returns zero for check/attack bonus claims

**Files:** `systems/skills/*.md`, `systems/combat/calculations.md`, `systems/core/README.md`

---

### TD-002 — Rewrite combat skill damage formulas

**Priority:** P0 · **Status:** todo · **Depends on:** TD-001

**Story:** As a developer implementing combat, I want weapon skill damage rules that match the canonical bonus table, so that DPR scaling is bounded (+4 cap at skill 10).

**Acceptance criteria**
- [ ] `combat-skills.md` damage lines no longer add raw skill **level** to damage (e.g. `+ Swordsmanship` as integer level)
- [ ] Canonical form documented: `weapon die + ability mod + skill bonus` (unless technique says otherwise)
- [ ] Cleave / stun / percentile mechanics converted to d20 (advantage, extra save, bonus action attack, etc.) or marked **optional GM rule** in a sidebar
- [ ] At least one worked example per weapon category matches `calculations.md`

**Files:** `systems/skills/combat-skills.md`

---

### TD-003 — Purge obsolete mechanics from skill files

**Priority:** P0 · **Status:** todo · **Depends on:** TD-001

**Story:** As a canon editor, I want obsolete terms removed from skills, so that agents and engineers never reintroduce pre-d20 systems.

**Acceptance criteria**
- [ ] No references to **physical defense**, **Magical Attack Score**, **evasion**, **accuracy score**, or **1d12** attack rolls in `systems/skills/`
- [ ] Crossbow armor penetration rewritten vs **AC** or **half armor bonus** (explicit rule chosen and documented)
- [ ] Spellcasting techniques use d20 spell attack / save DC from `calculations.md`
- [ ] `AGENTS.md` obsolete list still accurate after edits

**Files:** `systems/skills/magic-skills.md`, `systems/skills/combat-skills.md`, others as found

---

### TD-004 — Resolve Magical Defense formula

**Priority:** P0 · **Status:** todo · **Depends on:** TD-003

**Story:** As a caster/defender player, I want one Magical Defense rule, so that saves and AC vs spells are computable.

**Acceptance criteria**
- [ ] Single formula in `combat/calculations.md` (e.g. `+1 per Magical Defense level to SPI saves and AC vs spell attacks`, or alternative — but **one** rule)
- [ ] `magic-skills.md` links to that section; no conflicting text
- [ ] Example: Mage with Magical Defense 4 vs spell attack shows full math

**Files:** `systems/combat/calculations.md`, `systems/skills/magic-skills.md`

---

### TD-005 — Lock Fortune (LUC) implementation rule

**Priority:** P0 · **Status:** todo · **Depends on:** —

**Story:** As a game implementer, I want a default Fortune spend behavior, so that the session pool works without GM fiat.

**Acceptance criteria**
- [ ] `core/resolution.md` names **default**: advantage *or* reroll (pick one as canon default)
- [ ] Optional campaign variant documented in one paragraph
- [ ] Pool size formula unchanged: `max(1, 1 + LUC mod)` per session

**Files:** `systems/core/resolution.md`

---

### TD-006 — Rules consolidation QA pass

**Priority:** P0 · **Status:** todo · **Depends on:** TD-001 – TD-005

**Story:** As PM, I want a checklist proving E1 is done, so that downstream epics build on stable canon.

**Acceptance criteria**
- [ ] Checklist in story comment or `backlog/e1-qa-checklist.md` with grep commands and expected zero hits for obsolete terms
- [ ] Three worked examples (melee attack, skill check, spell save) trace only through canon docs
- [ ] No new parallel rule files created

**Files:** `backlog/e1-qa-checklist.md` (optional)

---

## Epic E2 — Combat loop

Define *how combat runs*, not just how to roll.

### TD-010 — Initiative and turn order

**Priority:** P0 · **Status:** todo · **Depends on:** TD-006

**Story:** As a combat programmer, I want initiative rules, so that turn order is deterministic.

**Acceptance criteria**
- [ ] New doc `systems/combat/encounter.md` (or equivalent) defines initiative roll (suggest: d20 + AGI mod + bonuses from Dodge 9–10, Battlefield Awareness, etc.)
- [ ] Tie-breaking rule defined
- [ ] Surprise round / flat-footed interaction references `core/resolution.md`
- [ ] Linked from `systems/combat/README.md`

**Files:** `systems/combat/encounter.md`, `systems/combat/README.md`

---

### TD-011 — Action economy

**Priority:** P0 · **Status:** todo · **Depends on:** TD-010

**Story:** As a combat programmer, I want defined action types per turn, so that skills referencing bonus actions and reactions are legal.

**Acceptance criteria**
- [ ] Standard turn lists: movement (grid squares from AGI − armor penalty), action, bonus action, reaction, free object interaction
- [ ] Definitions for **bonus action**, **reaction**, **free action** with limits per round
- [ ] “Once per combat / day / long rest” glossary entry
- [ ] Cross-links from at least 3 skill techniques that use these terms

**Files:** `systems/combat/encounter.md`

---

### TD-012 — Conditions reference

**Priority:** P0 · **Status:** todo · **Depends on:** TD-010

**Story:** As a content author, I want a conditions glossary, so that monster and skill effects use consistent language.

**Acceptance criteria**
- [ ] New `systems/combat/conditions.md` defines: Grappled, Restrained, Paralyzed, Frightened, Stunned, Prone, Invisible, Poisoned (minimal set used in current monsters)
- [ ] Each entry: effect on AC, movement, actions, saves, escape/end rule
- [ ] Monster README links to conditions doc

**Files:** `systems/combat/conditions.md`, `systems/monsters/README.md`

---

### TD-013 — Rest, recovery, and resource refresh

**Priority:** P0 · **Status:** todo · **Depends on:** TD-011

**Story:** As a player, I want rest rules, so that HP/MP/Fortune/per-day abilities refresh predictably.

**Acceptance criteria**
- [ ] Short rest and long rest defined (duration, frequency limits)
- [ ] HP recovery: SPI-based healing rate from archive reconciled or replaced with explicit rule
- [ ] MP regen per turn (SPI + Mana Control) and per rest documented in one place
- [ ] Fortune pool refresh timing (per session vs per long rest) decided and documented
- [ ] “Once per long rest” skills reference this doc

**Files:** `systems/combat/encounter.md` or `systems/core/derived-stats.md`, `systems/core/resolution.md`

---

### TD-014 — Death, dying, and stabilization

**Priority:** P0 · **Status:** todo · **Depends on:** TD-012, TD-013

**Story:** As a delver player, I want death/dying rules, so that defeat is fair and links to extraction fantasy.

**Acceptance criteria**
- [ ] Rules for 0 HP: dying state or instant death (choose and document)
- [ ] Stabilization via Medicine / Field Medic aligned with `mental-skills.md`
- [ ] NPC/monster “drop to 0” traits (Undead Fortitude, Rise Again) cross-reference player-facing rules where relevant
- [ ] Bridge paragraph to extraction death (see TD-050) — even if “TBD detail in E6”

**Files:** `systems/combat/encounter.md`, `systems/world/extraction.md` (link only)

---

### TD-015 — Grid, reach, and positioning rules

**Priority:** P1 · **Status:** todo · **Depends on:** TD-010

**Story:** As a tactical game dev, I want grid combat specifics, so that cover, flanking, and reach are simulatable.

**Acceptance criteria**
- [ ] Square grid assumed (or hex — pick one)
- [ ] Reach-2 weapons, opportunity attacks (if any), difficult terrain — explicit yes/no
- [ ] Cover and flanking from `resolution.md` expanded with measurement rules
- [ ] Movement diagonal cost rule (if applicable)

**Files:** `systems/combat/encounter.md`, `systems/core/resolution.md`

---

### TD-016 — Combat loop integration & examples

**Priority:** P0 · **Status:** todo · **Depends on:** TD-010 – TD-015

**Story:** As QA, I want a full round walkthrough, so that E2 can be validated without a GM.

**Acceptance criteria**
- [ ] One complete combat example: initiative → surprise → 2 rounds → crit → condition → drop to 0
- [ ] All numbers trace to canon docs post-E1
- [ ] `systems/combat/README.md` indexes encounter, conditions, calculations, resolution

**Files:** `systems/combat/encounter.md`, `systems/combat/README.md`

---

## Epic E3 — Equipment & items

### TD-020 — Weapon stat table

**Priority:** P0 · **Status:** todo · **Depends on:** TD-002

**Story:** As a combat implementer, I want every weapon’s mechanics, so that damage rolls need no GM lookup.

**Acceptance criteria**
- [ ] `systems/equipment/weapons.md` completed: name, cost, damage die, damage type, STR/AGI, properties (finesse, two-hand, reach, loading, thrown range)
- [ ] All weapons listed in current file have stats; martial/simple/ranged groupings
- [ ] Crossbow reload time tied to action economy (TD-011)
- [ ] At least one weapon per combat skill category represented

**Files:** `systems/equipment/weapons.md`

---

### TD-021 — Define Base HP and Base MP

**Priority:** P0 · **Status:** todo · **Depends on:** —

**Story:** As a character builder, I want base HP/MP values, so that derived stats are fully computable.

**Acceptance criteria**
- [ ] `derived-stats.md` defines Base HP (constant and/or by class tier table — pick one)
- [ ] Base MP defined similarly
- [ ] Worked example for Peasant, Warrior, Mage at creation
- [ ] Monster design note: whether monsters use same formula or flat HP (reference in monsters README)

**Files:** `systems/core/derived-stats.md`, `systems/classes/classes.md`

---

### TD-022 — Starting equipment kits by base class

**Priority:** P1 · **Status:** todo · **Depends on:** TD-020, TD-040

**Story:** As a new player, I want default starting gear by class, so that character creation finishes in one pass.

**Acceptance criteria**
- [ ] Table: each Tier-1 class → weapon(s), armor (if any), adventuring gear within starting gold bounds
- [ ] Links to `economy.md` starting gold formula
- [ ] Optional “remaining gold” guidance

**Files:** `systems/equipment/gear.md` or `systems/character/creation.md`

---

### TD-023 — Encumbrance and carrying capacity in play

**Priority:** P1 · **Status:** todo · **Depends on:** TD-057

**Story:** As an extraction player, I want encumbrance rules, so that “take what you can carry” is mechanical.

**Acceptance criteria**
- [ ] STR × 10 units defined with example item weights
- [ ] Over-cap penalties (speed, Stealth, or forced drops — pick rule)
- [ ] Link from extraction doc

**Files:** `systems/core/derived-stats.md`, `systems/equipment/gear.md`, `systems/world/extraction.md`

---

### TD-024 — Trade goods and crafting inputs catalog

**Priority:** P2 · **Status:** todo · **Depends on:** TD-020

**Story:** As an economy designer, I want salvage/trade goods enumerated, so that loot tables can reference IDs.

**Acceptance criteria**
- [ ] Extend `gear.md` or new `equipment/trade-goods.md` with weights, base values
- [ ] Cross-link monster treasure lines to item names

**Files:** `systems/equipment/gear.md`, `systems/monsters/*.md`

---

## Epic E4 — Magic system

### TD-030 — Schools of magic

**Priority:** P0 · **Status:** todo · **Depends on:** TD-004, TD-006

**Story:** As a spellcaster player, I want defined magic schools, so that Spell Focus and resistances apply.

**Acceptance criteria**
- [ ] Replace TODO in `magic-skills.md` with 4–8 schools (names, themes, sample spells each)
- [ ] Ether / divine / arcane taxonomy aligned with `world/ether.md`
- [ ] School chosen at Spell Focus (level 3) documented

**Files:** `systems/skills/magic-skills.md`, new `systems/magic/schools.md` (if split)

---

### TD-031 — Core spell list (tier 1–3 casters)

**Priority:** P0 · **Status:** todo · **Depends on:** TD-030

**Story:** As a Mage/Acolyte/Hedge Wizard player, I want a starter spell list, so that casting works in combat.

**Acceptance criteria**
- [ ] Minimum 3 spells per school at levels 0–2 equivalent (cantrip + low + mid)
- [ ] Each spell: school, MP cost, action type, range, attack/save, damage/effect, scaling (if any)
- [ ] Spell attack and save DC use `combat/calculations.md` only

**Files:** new `systems/magic/spells.md` or per-school files

---

### TD-032 — Expanded spell list (tier 4–6)

**Priority:** P1 · **Status:** todo · **Depends on:** TD-031

**Story:** As a high-tier caster, I want advanced spells, so that progression has payoff.

**Acceptance criteria**
- [ ] Spells gated by class tier or skill level (rule stated)
- [ ] At least 2 spells per school for expert/master tiers
- [ ] Wild magic / Ether contact hooks for Sorcerer deeds

**Files:** `systems/magic/spells.md`

---

### TD-033 — MP costs and casting action rules

**Priority:** P0 · **Status:** todo · **Depends on:** TD-011, TD-031

**Story:** As a combat programmer, I want casting timing and MP spend rules, so that spells fit the action economy.

**Acceptance criteria**
- [ ] Default cast time (action vs bonus vs reaction) per spell tag
- [ ] Concentration rule (if any) defined or explicitly “none at launch”
- [ ] Mana Efficiency / Mana Mastery techniques aligned with spell costs

**Files:** `systems/magic/spells.md`, `systems/skills/magic-skills.md`

---

### TD-034 — Divine vs arcane casting split

**Priority:** P1 · **Status:** todo · **Depends on:** TD-030

**Story:** As a Priest/Novice player, I want divine magic differentiated, so that class fantasy is clear.

**Acceptance criteria**
- [ ] Rule for which attribute/skill governs divine casts (SPI vs INT — pick and document)
- [ ] Minimum 5 divine spells (healing, ward, smite, etc.)
- [ ] Deity hooks optional in spell fluff

**Files:** `systems/magic/spells.md`, `systems/deities/README.md`

---

### TD-035 — Magic items and spell identification

**Priority:** P1 · **Status:** todo · **Depends on:** TD-031

**Story:** As a delver, I want magic item rules, so that Arcana/Magical Knowledge checks have outcomes.

**Acceptance criteria**
- [ ] Minor/major item creation rules from skill techniques given concrete recipes or DC tables
- [ ] Identify spell / item procedures with DCs
- [ ] Link to Appraisal and Arcana skills

**Files:** `systems/equipment/gear.md`, `systems/skills/magic-skills.md`, `systems/skills/mental-skills.md`

---

## Epic E5 — Character creation & progression

### TD-040 — Starting skills allocation

**Priority:** P0 · **Status:** todo · **Depends on:** TD-006

**Story:** As a new character, I know how many skills I start with and at what level, so that creation is complete.

**Acceptance criteria**
- [ ] Rule: e.g. “3 skills at level 1, one must match class; +1 per tier promotion” (or alternative — documented)
- [ ] Maximum skill level at creation stated
- [ ] Worked example in `creation.md`

**Files:** `systems/character/creation.md`, `systems/skills/README.md`

---

### TD-041 — Base class selection procedure

**Priority:** P0 · **Status:** todo · **Depends on:** TD-040

**Story:** As a player, I want a clear base class pick flow, so that stat gates are enforced automatically.

**Acceptance criteria**
- [ ] Algorithm: roll stats → filter eligible Tier-1 classes → player chooses
- [ ] Document stat requirements from `classes.md` in creation flow
- [ ] Fallback if no class qualifies (GM override or forced Peasant)

**Files:** `systems/character/creation.md`, `systems/classes/classes.md`

---

### TD-042 — Deed counter schema

**Priority:** P0 · **Status:** todo · **Depends on:** TD-006

**Story:** As a game implementer, I want machine-trackable deed requirements, so that class tier promotion can be automated.

**Acceptance criteria**
- [ ] New `systems/classes/deeds.md` (or JSON in `data/deeds/`) listing every promotion with: `id`, `from_tier`, `to_class`, `counters[]` (type, target, quantity)
- [ ] Counter types enum: `combats_survived`, `skill_check_successes`, `gold_held`, `location_visited`, etc.
- [ ] Every deed in `progression.md` mapped to at least one counter

**Files:** `systems/classes/deeds.md`, `systems/classes/progression.md`

---

### TD-043 — Class tier promotion rules

**Priority:** P0 · **Status:** todo · **Depends on:** TD-042

**Story:** As a progressing character, I want promotion timing and PB updates defined, so that tier changes are unambiguous.

**Acceptance criteria**
- [ ] When all deeds for a path complete → promotion ritual (rest? Registry? free?)
- [ ] PB updates immediately per tier table
- [ ] Multi-path choice at tier 2+ documented (can you hold two tier-2 classes? — pick rule)

**Files:** `systems/classes/progression.md`, `systems/classes/deeds.md`

---

### TD-044 — Skill XP and gold advancement edge cases

**Priority:** P1 · **Status:** todo · **Depends on:** TD-040

**Story:** As a skill grinder, I want edge cases defined, so that XP exploits are closed.

**Acceptance criteria**
- [ ] Repeated same lock DC farming — allowed or diminishing returns?
- [ ] Failed checks: never award XP (confirm)
- [ ] Gold cost timing: on level-up attempt vs automatic deduction

**Files:** `systems/skills/skill-checks.md`, `systems/skills/progression.md`

---

### TD-045 — Clean up character creation export artifacts

**Priority:** P2 · **Status:** todo · **Depends on:** —

**Story:** As a reader, I want creation docs free of Google Docs escapes, so that diffs and tooling stay clean.

**Acceptance criteria**
- [ ] `creation.md`, `races.md`, `classes.md` stripped of `\*`, `\#`, numbered list escapes
- [ ] Consistent markdown headings
- [ ] Wood Elves and other races use consistent naming with `races/` files

**Files:** `systems/character/*.md`, `systems/classes/classes.md`

---

### TD-046 — Playable race lore completion

**Priority:** P2 · **Status:** todo · **Depends on:** TD-045

**Story:** As a worldbuilder, I want lore stubs for all 16 playable races, so that character creation UI has flavor text.

**Acceptance criteria**
- [ ] New files: wood-elves, orcs, gnomes, dragonkin, faeries, minotaurs, undead, trolls under `systems/races/`
- [ ] Each links to `character/races.md` for mechanics
- [ ] `systems/races/README.md` indexes all 16

**Files:** `systems/races/*.md`

---

## Epic E6 — Extraction meta-game

### TD-050 — Death and persistence model

**Priority:** P0 · **Status:** todo · **Depends on:** TD-014

**Story:** As a delver who dies, I want clear persistence rules, so that “Tomb Dust” means something mechanical.

**Acceptance criteria**
- [ ] New `systems/meta/death-and-persistence.md` (or section in `extraction.md`): what resets (character), what persists (Registry log, map knowledge, faction rep, stash?)
- [ ] New character inheritance rules (debt, gear, contacts)
- [ ] Align with extraction tone in `world/extraction.md`

**Files:** `systems/world/extraction.md`, new `systems/meta/` as needed

---

### TD-051 — Delve run loop (stamp → equip → enter → extract)

**Priority:** P0 · **Status:** todo · **Depends on:** TD-050

**Story:** As a party, I want a formal run structure, so that a game session maps to a delve loop.

**Acceptance criteria**
- [ ] Phases: preparation, ingress, delve, extract, aftermath
- [ ] Each phase lists required checks, costs, and failure modes
- [ ] Registry stamp cost and info gained (danger rating, layer stack) specified

**Files:** `systems/world/extraction.md`, `systems/factions/delvers-registry.md`

---

### TD-052 — Threat / collapse clock

**Priority:** P0 · **Status:** todo · **Depends on:** TD-051

**Story:** As a delver under pressure, I want a collapse clock rule, so that extraction urgency is mechanical not GM fiat.

**Acceptance criteria**
- [ ] Clock type chosen: turn-based, real-time abstract, or hazard die — documented with examples
- [ ] Triggers: noise, veil bleed, time in site, failed extract route
- [ ] Clock at max: consequences (spawn tier up, exit sealed, etc.)

**Files:** `systems/world/extraction.md`

---

### TD-053 — Map claims, off-claim, and insurance

**Priority:** P1 · **Status:** todo · **Depends on:** TD-051

**Story:** As a licensed delver, I want claim rules, so that AV-GRID addresses have legal/mechanical weight.

**Acceptance criteria**
- [ ] On-claim vs off-claim penalties (no insurance, legal risk — numeric if possible)
- [ ] Insurance payout conditions on death
- [ ] Claim-jumping and dispute resolution hook (Registry Moot)

**Files:** `systems/factions/delvers-registry.md`, `systems/world/extraction.md`

---

### TD-054 — Loot extraction and stash rules

**Priority:** P1 · **Status:** todo · **Depends on:** TD-023, TD-051

**Story:** As a survivor, I want rules for what loot escapes a delve, so that inventory management matters.

**Acceptance criteria**
- [ ] Body loot on death (drop all? insured items? Registry tax?)
- [ ] Stash location (surface hub only? Registry vault?)
- [ ] Appraisal and fence timing in aftermath phase

**Files:** `systems/world/extraction.md`, `systems/equipment/economy.md`

---

### TD-055 — Faction standing and economic hooks

**Priority:** P1 · **Status:** todo · **Depends on:** TD-050

**Story:** As a repeat delver, I want faction rep effects, so that world reactions are systematic.

**Acceptance criteria**
- [ ] Minimum viable rep track (−3 to +3?) per major faction
- [ ] 2–3 concrete effects per faction at rep thresholds (price, access, hostility)
- [ ] Tie to locations in AV-GRID where applicable

**Files:** `systems/factions/*.md`, `systems/world/extraction.md`

---

### TD-056 — Extraction scoring and “small victories”

**Priority:** P2 · **Status:** todo · **Depends on:** TD-051

**Story:** As a designer, I want scoring for partial success, so that brutal runs still feel meaningful.

**Acceptance criteria**
- [ ] Metrics: salvage value extracted, maps cleared %, deeds progressed, survivors
- [ ] Optional renown or Registry rank
- [ ] Link to class deed counters (TD-042)

**Files:** `systems/world/extraction.md`, `systems/meta/death-and-persistence.md`

---

### TD-057 — Encumbrance under pressure (extract phase)

**Priority:** P1 · **Status:** todo · **Depends on:** TD-023, TD-052

**Story:** As a fleeing delver, I want forced tradeoffs when over-encumbered during extract, so that greed has cost.

**Acceptance criteria**
- [ ] During extract phase, over-cap forces drop item or speed penalty (explicit)
- [ ] Interaction with collapse clock

**Files:** `systems/world/extraction.md`, `systems/core/derived-stats.md`

---

## Epic E7 — World data & AV-GRID

### TD-060 — MVP region full AV-GRID coverage

**Priority:** P1 · **Status:** todo · **Depends on:** TD-090

**Story:** As a level designer, I want one fully stamped region, so that a vertical slice has complete addresses.

**Acceptance criteria**
- [ ] Choose MVP region (suggest: Heartlands + Breley + Shadowfen corridor)
- [ ] All surface cells in region have `av-grid.json` entries OR documented “wilderness template”
- [ ] `validate` and `build-index` pass
- [ ] Location markdown AV-GRID ids match JSON exactly

**Files:** `data/av-grid/av-grid.json`, `systems/locations/*.md`

---

### TD-061 — Danger rating and encounter linking standard

**Priority:** P1 · **Status:** todo · **Depends on:** TD-060

**Story:** As an encounter generator, I want every delve address to have danger + monster links, so that spawns are data-driven.

**Acceptance criteria**
- [ ] Schema/doc rule: stamped delve addresses require `dangerRating` + `links.monsters[]`
- [ ] Audit passes for MVP region
- [ ] Encounter tables in location docs use monster file slugs matching JSON links

**Files:** `data/av-grid/av-grid.json`, `data/av-grid/README.md`, `systems/locations/*.md`

---

### TD-062 — Site graph format (rooms and connections)

**Priority:** P1 · **Status:** todo · **Depends on:** TD-090, TD-060

**Story:** As a dungeon generator, I want a site graph schema, so that delves are navigable in software.

**Acceptance criteria**
- [ ] New `data/sites/` schema: nodes (room id, av-grid address, tags), edges (connection type, locked?, hazard?)
- [ ] One example site: e.g. `32-C-UG-1` Breley undercrypt with ≥5 rooms
- [ ] Validator script or JSON schema

**Files:** `data/sites/`, `tools/` (new validator optional)

---

### TD-063 — Loot tables per site tier

**Priority:** P1 · **Status:** todo · **Depends on:** TD-024, TD-062

**Story:** As a loot system, I want tiered loot tables, so that rewards match danger rating.

**Acceptance criteria**
- [ ] Tables by danger tier: hazard / skirmisher / elite / boss
- [ ] Currency ranges aligned with `economy.md`
- [ ] Linked from site graph or AV-GRID `links`

**Files:** `data/loot/` or `systems/equipment/economy.md`

---

### TD-064 — Random encounter procedure

**Priority:** P2 · **Status:** todo · **Depends on:** TD-061

**Story:** As a GM-less mode, I want encounter roll procedure, so that wilderness travel is automatable.

**Acceptance criteria**
- [ ] Procedure: biome + danger → table → composition (e.g. 1d6 larvae)
- [ ] Document in `world/extraction.md` or `systems/combat/encounter.md`
- [ ] At least 3 biome tables for MVP region

**Files:** `systems/world/extraction.md`, location or data files

---

### TD-065 — Registry ledger examples as data

**Priority:** P2 · **Status:** todo · **Depends on:** TD-051

**Story:** As a UI designer, I want sample Registry ledger JSON, so that map-stamp screens have realistic copy.

**Acceptance criteria**
- [ ] 3+ `registry.ledgerExample` entries in av-grid filled with consistent format
- [ ] Document ledger field spec in `data/av-grid/README.md`

**Files:** `data/av-grid/av-grid.json`, `data/av-grid/README.md`

---

## Epic E8 — Content completion

### TD-070 — Traps core rules

**Priority:** P1 · **Status:** todo · **Depends on:** TD-011, TD-012

**Story:** As a rogue, I want trap rules, so that Trap Handling skill is fully playable.

**Acceptance criteria**
- [ ] Trap definition: detect DC, disarm DC, trigger, damage/effect, reset
- [ ] Complexity scales with Trap Handling level (from skill file)
- [ ] 3 example traps ( tomb, fen, vault )

**Files:** new `systems/combat/traps.md` or `systems/skills/subterfuge-skills.md` appendix

---

### TD-071 — Poison and disease rules

**Priority:** P1 · **Status:** todo · **Depends on:** TD-012

**Story:** As a survivor, I want poison/disease procedures, so that Medicine and Endurance skills apply.

**Acceptance criteria**
- [ ] Poison: save interval, damage stages, cure DC
- [ ] Disease: progression, contagion (if any), treatment
- [ ] Link Treat Disease / Iron Stomach techniques

**Files:** `systems/combat/conditions.md` or new `systems/combat/hazards.md`

---

### TD-072 — Complete stub monsters audit

**Priority:** P1 · **Status:** todo · **Depends on:** TD-012

**Story:** As a content lead, I want every monster index entry combat-ready, so that encounter tables never dead-end.

**Acceptance criteria**
- [ ] Audit all files in `systems/monsters/README.md` index
- [ ] Confirm stat blocks for etherwraiths, shadowkin, etc. meet template
- [ ] Remove stale TODO comments where content exists; fill true gaps

**Files:** `systems/monsters/*.md`

---

### TD-073 — Humanoid stat templates (cultists, guards)

**Priority:** P1 · **Status:** todo · **Depends on:** TD-072

**Story:** As a location author, I want generic humanoid stat blocks, so that “Thar cultist” hooks resolve to stats.

**Acceptance criteria**
- [ ] Templates: Militia, Footman, Knight, Cultist, Bandit — skirmisher tier
- [ ] Referenced from at least 2 location encounter tables

**Files:** `systems/monsters/README.md`, new `systems/monsters/humanoids.md`

---

### TD-074 — NPC services catalog

**Priority:** P2 · **Status:** todo · **Depends on:** TD-051

**Story:** As a hub-town player, I want NPC services standardized, so that aftermath phase is structured.

**Acceptance criteria**
- [ ] Service template: cost, DC, availability, faction gate
- [ ] All NPCs in `systems/npcs/` with services updated to template
- [ ] Link to Registry and economy

**Files:** `systems/npcs/*.md`

---

### TD-075 — Event mechanics (Eclipse, Dance)

**Priority:** P2 · **Status:** todo · **Depends on:** TD-005, TD-055

**Story:** As a live-ops designer, I want event rule hooks, so that seasonal content is implementable.

**Acceptance criteria**
- [ ] Eclipse Festival: mechanical boons/banes during event week
- [ ] Dance with the Dead: Fortune penalty, encounter hooks as structured triggers
- [ ] Calendar placement documented

**Files:** `systems/events/*.md`

---

### TD-076 — Deity mechanical hooks

**Priority:** P2 · **Status:** todo · **Depends on:** TD-034

**Story:** As a cleric, I want deity-specific domains or blessings, so that Aven vs Thar matters mechanically.

**Acceptance criteria**
- [ ] Aven and Thar: minimum 1 blessing + 1 taboo each with mechanical effect
- [ ] Optional domain spells or Fortune interactions

**Files:** `systems/deities/*.md`

---

### TD-077 — Techniques index

**Priority:** P2 · **Status:** todo · **Depends on:** TD-001

**Story:** As a builder, I want all skill techniques indexed, so that UI and validation can list unlocks.

**Acceptance criteria**
- [ ] Generated or curated index: skill → level 3/6/9 techniques with prerequisites
- [ ] Cross-check action types against TD-011

**Files:** `systems/skills/techniques-index.md` (generated optional)

---

## Epic E9 — Data layer & engine readiness

### TD-080 — Entity schema design doc

**Priority:** P0 · **Status:** todo · **Depends on:** TD-006

**Story:** As an engine architect, I want an entity schema spec, so that JSON exports have a target shape.

**Acceptance criteria**
- [ ] Doc lists entities: Character, Skill, Spell, Item, Weapon, Armor, Monster, Condition, Deed, Site, AvAddress
- [ ] Field types and required IDs (`slug` convention)
- [ ] Reference relationships (spell → school, site → av-grid id)

**Files:** `data/schemas/README.md`, `data/schemas/*.json` (draft)

---

### TD-081 — JSON Schema for monsters

**Priority:** P0 · **Status:** todo · **Depends on:** TD-080, TD-072

**Story:** As a tools developer, I want monsters in JSON, so that content validates independently of markdown.

**Acceptance criteria**
- [ ] `data/schemas/monster.schema.json` matches monster README template
- [ ] ≥3 monsters converted as examples
- [ ] Validator script passes examples

**Files:** `data/schemas/`, `data/monsters/`, `tools/`

---

### TD-082 — JSON Schema for items and weapons

**Priority:** P0 · **Status:** todo · **Depends on:** TD-020, TD-080

**Story:** As an inventory system dev, I want item JSON, so that gear is loadable without parsing markdown.

**Acceptance criteria**
- [ ] Schemas for weapon, armor, gear, trade-good
- [ ] Full weapon table from TD-020 represented in JSON
- [ ] Validator passes

**Files:** `data/schemas/`, `data/items/`

---

### TD-083 — JSON Schema for spells and schools

**Priority:** P0 · **Status:** todo · **Depends on:** TD-031, TD-080

**Story:** As a casting system dev, I want spell JSON, so that MP costs and effects are typed.

**Acceptance criteria**
- [ ] `spell.schema.json`, `school.schema.json`
- [ ] All TD-031 spells encoded
- [ ] Effect types enum (damage, heal, condition, buff)

**Files:** `data/schemas/`, `data/spells/`

---

### TD-084 — JSON Schema for deeds and class tiers

**Priority:** P1 · **Status:** todo · **Depends on:** TD-042, TD-080

**Story:** As a progression system dev, I want deed JSON, so that tier-ups are event-driven.

**Acceptance criteria**
- [ ] `deed.schema.json` with counter definitions
- [ ] Full mapping from `progression.md` paths
- [ ] Example character state JSON with partial deed progress

**Files:** `data/schemas/`, `data/deeds/`

---

### TD-085 — Reference rules engine (minimal)

**Priority:** P1 · **Status:** todo · **Depends on:** TD-016, TD-081, TD-082

**Story:** As QA, I want a minimal sim that runs d20 tests and one combat round, so that rules regressions are caught.

**Acceptance criteria**
- [ ] Python module in `tools/rules_engine/` (or sibling repo contract): roll, attack vs AC, apply damage, apply condition
- [ ] Tests cover E1 examples and TD-016 walkthrough numbers
- [ ] CI runnable via `python -m pytest tools/rules_engine` or similar

**Files:** `tools/rules_engine/`, tests

---

### TD-086 — Markdown → JSON codegen spike

**Priority:** P2 · **Status:** todo · **Depends on:** TD-081 – TD-083

**Story:** As a content maintainer, I want one-direction sync from markdown to JSON, so that designers can keep writing prose.

**Acceptance criteria**
- [ ] Script converts one domain (monsters OR spells) markdown → JSON
- [ ] Document sync workflow in `data/schemas/README.md`
- [ ] Decision recorded: JSON-first vs markdown-first for each domain

**Files:** `tools/`, `data/schemas/README.md`

---

## Epic E10 — Repo & integration contract

### TD-090 — Canon ownership and sync contract

**Priority:** P1 · **Status:** todo · **Depends on:** TD-080

**Story:** As a team lead, I want a written contract between this repo and the game codebase, so that canon drift is prevented.

**Acceptance criteria**
- [ ] Doc: `docs/engine-integration.md` (or section in AGENTS.md): which repo owns sim, how versions pin, how content ships
- [ ] Explicit note on sibling `tomb-dust/` project if still accurate
- [ ] Version field for ruleset (`rulesVersion` in data exports)

**Files:** `docs/engine-integration.md`, `AGENTS.md`

---

### TD-091 — Rules version and changelog

**Priority:** P1 · **Status:** todo · **Depends on:** TD-090

**Story:** As a downstream consumer, I want semver for rules, so that breaking changes are visible.

**Acceptance criteria**
- [ ] `rules/CHANGELOG.md` or root `RULESCHANGELOG.md` started
- [ ] `rulesVersion` in exported JSON / av-grid metadata policy
- [ ] E1 completion = `1.1.0` or similar bump rationale documented

**Files:** `RULESCHANGELOG.md`, `data/schemas/README.md`

---

### TD-092 — Game readiness definition of done

**Priority:** P1 · **Status:** todo · **Depends on:** TD-085, TD-051, TD-031

**Story:** As PM, I want a clear “ready for game architecture” gate, so that the team knows when to start engine work.

**Acceptance criteria**
- [ ] Checklist: E1–E6 P0 stories done, TD-080/081/082/083 done, TD-085 green, MVP region TD-060 done
- [ ] Linked from backlog README
- [ ] Reviewed and dated

**Files:** `backlog/README.md`, `backlog/game-ready-checklist.md`

---

## Suggested milestones

| Milestone | Stories | Outcome |
|-----------|---------|---------|
| **M1 — Canon stable** | TD-001 – TD-006 | Trustworthy math |
| **M2 — Combat simulatable** | TD-010 – TD-016, TD-020 – TD-021 | Fight a round in code |
| **M3 — Casters work** | TD-030 – TD-033, TD-040 – TD-041 | Spells + complete creation |
| **M4 — Tomb Dust loop** | TD-050 – TD-054, TD-042 – TD-043 | Extraction identity |
| **M5 — Data pipeline** | TD-080 – TD-085, TD-060 – TD-062 | JSON + reference engine |
| **M6 — Vertical slice content** | TD-061 – TD-063, TD-070 – TD-073 | One full delve playable |
| **M7 — Game architecture green light** | TD-092 | Start engine/UI work |

---

## Using this backlog with dev-team

To scope a dev-team session on a story:

1. Pick story ID (e.g. `TD-010`).
2. `scope propose` with story title + acceptance criteria copied from this file.
3. Keep artifacts under `.dev-team/works/<slug>/artifacts/`.
4. Mark story **done** in this file when gate passes.

---

## Summary

**Total stories:** 62 (TD-001 – TD-092, numbered by epic)  
**P0 stories:** 28 — must complete before rules engine or honest combat prototype  
**Next recommended pick:** **TD-001** (canonical skill bonus) — unblocks most of E1 and every combat skill rewrite
