# Extraction and Tomb Dust

Tomb Dust is a **hardcore extraction** setting: parties enter dangerous sites, take what they can carry, and leave before collapse, pursuit, or attrition ends them. Death is common; progress is measured in **maps cleared**, **heirlooms recovered**, and **deeds** that unlock class tiers—not in leveling alone.

## What “Tomb Dust” means

1. **Literal:** cremated ash or scraped remains of delvers left in sites too dangerous to retrieve.  
2. **Social:** slang for anyone disposable on a bad map—“You’ll end up Tomb Dust.”  
3. **Mechanical tone:** defeat teaches; **death ends the run**—corpse on the map, **new game**, fresh character. See [death-and-persistence.md](../meta/death-and-persistence.md).

## The delving economy

| Role | Function |
|------|----------|
| **Delver** | Enters site on contract or gamble |
| **Registry clerk** | Sells map claims, logs survivors, settles disputes |
| **Fence / appraiser** | Buys salvage; Appraisal checks |
| **Patron** | Noble, tower, or knight order funding a run |
| **Guide** | Edgecombe wood-wise; fen pilots |

**Typical run:** buy map stamp → equip → enter at stamped **AV-GRID** address → extract salvage before the site's **threat clock** fills ([Collapse and threat clock](#collapse-and-threat-clock)) → sell → pay tax → train skills with gold/XP.

Formal breakdown: [Delve run loop](#delve-run-loop) below. When a run ends in death, see [meta/death-and-persistence.md](../meta/death-and-persistence.md).

## Delve run loop

Every licensed delve follows five phases. A phase can be skipped only by GM agreement (e.g. patron-insertion straight to ingress). Track **costs** at the table in gold, supplies, clock ticks, and **failure modes** as fiction plus whatever d20 checks the scene demands.

### 1. Preparation

**Purpose:** turn cash and contacts into a legal claim and a loadout worth risking.

| | |
|--|--|
| **Typical checks** | **Persuasion / Deception** (patron terms, fence credit); **Appraisal** (verify stamp vs. chart); **Investigation** (spot forged **AV-GRID** or wrong `UG` level); clerk interview for realm license (e.g. Breley **DC 13** Persuasion or proof of prior survival) |
| **Costs** | Map **stamp** (10–500 gp by tier; 30-day claim); optional **insurance** (~15 gp); gear purchase or loan; guide/day rates; rations; ward keys; debt service on prior runs |
| **Failure modes** | Forged or mismatched stamp → **off-claim** next phase; under-funded party → insufficient light, rope, or healing; patron pulls funding; Registry blacklist; Verdant Vale sabotage on grotto listings; start in **debt** with no stash buffer |

**Registry stamp example (`47-B-UG-3`, Elite):**

```
STAMP: REG-1204 rev.C
PRIMARY: 47-B-UG-3
SURFACE ENTRY: 47-B (ruin gate 3)
DANGER: Elite (Registry survey 1204)
COST: 120 gp stamp + 15 gp insurance pool (optional)
VALID: 30 days from issue (Edgecombe clerk)
```

That 120 gp buys the right to sell salvage in Registry towns without confiscation—not safety. Wrong layer on the chart still voids insurance.

### 2. Ingress

**Purpose:** cross from safe hub to **stamped entry** without burning the claim.

| | |
|--|--|
| **Typical checks** | **Nature** / **Athletics** (fen paths, wood-wise guides); **Stealth** (avoid claim-jumpers); verify surface cell matches stamp (e.g. enter at `47-B`, not `46-B`); ward or knight **DC** at licensed gates |
| **Costs** | Travel time; tolls; guide fees; light sources; entry consumables; **Ingress** threat clock may start at the ingress threshold (see [clock](#collapse-and-threat-clock)) |
| **Failure modes** | **Off-claim** entry (no insurance, legal risk, Iron Pact penalties); ambush at gate; lost party member; alarmed ward → +1 clock tick and alerted delve; ingress delay eats stamp validity |

Everything carried past the agreed ingress threshold is **body gear** until extracted—see [death-and-persistence.md](../meta/death-and-persistence.md).

### 3. Delve

**Purpose:** reach the objective layer, fight or bypass threats, and secure salvage before the site wins.

| | |
|--|--|
| **Typical checks** | **Lockpicking** / **Trap Handling** / **Investigation**; combat (d20 vs **AC**); navigation between layers; veil anomalies ([ether.md](ether.md)); social checks with rivals on the same stamp |
| **Costs** | HP; **MP**; consumables; **Delve** threat clock ticks (time, noise, veil); sanity or Ether exposure on thin-veils |
| **Failure modes** | TPK; retreat without objective; split party; map lost; clock at max → [collapse consequences](#at-six-segments); claim dispute with another stamped crew; PC death → body and carried loot remain in site |

Layer stack must match stamp (e.g. `UG-3` under `47-B`). Delving deeper than stamped without amendment is off-claim.

### 4. Extract

**Purpose:** leave the site with salvage and survivors before collapse, pursuit, or attrition ends the run.

| | |
|--|--|
| **Typical checks** | Route choice under pressure; **Athletics / Acrobatics** (hazards); **Stealth** (avoid pursuit); encumbrance and load limits; holding a rearguard while others cross ingress |
| **Costs** | Abandon loot to move faster; rearguard injuries; **Extract** threat clock ticks; possible **partial extract** (some pack slots left behind) |
| **Failure modes** | Killed on exit; **exit sealed** (clock consequence); loot confiscated by rivals; survivor without **survivor registration** target (aftermath penalties); successful extract with missing dead → recovery hook for next run |

Extract ends when the party crosses the **ingress boundary** back to the safe hub with carried salvage.

### 5. Aftermath

**Purpose:** convert loot into gold, rep, and training—and pay the Registry its cut.

| | |
|--|--|
| **Typical checks** | **Appraisal** (fence vs. true value); **Persuasion** (tax dispute); **Survival registration** (free but mandatory in Registry towns); laundering disputed goods |
| **Costs** | **Ash tithe** and Registry tax on sales; fence margin; debt repayment; storage fees for **account stash**; skill training gold/XP |
| **Failure modes** | Unregistered sale → fine or blacklist; counterfeit salvage; patron seizes contract share; debt spiral blocks next **preparation**; faction rep loss if grotto desecration exposed |

Survivors gain **map knowledge** and **faction rep** for that run; a dead delver leaves a **corpse**—**account stash and stashGp persist** for the successor; body gear does not. See [death-and-persistence.md](../meta/death-and-persistence.md).

---

## Collapse and threat clock

Licensed delves use a **6-segment threat clock** (tokens, ticks on paper, or a die 1–6). Segments fill when the site notices the party; at **6/6**, resolve [consequences](#at-six-segments). One segment ≈ one serious escalation—carried noise, time the dead remember, veil bleed, or stone settling.

**Scope (pick at stamp briefing):**

| Scope | Use when |
|-------|----------|
| **Per phase (default)** | Separate clocks for [Ingress](#2-ingress), [Delve](#3-delve), and [Extract](#4-extract). [Preparation](#1-preparation) and [aftermath](#5-aftermath) have no clock. |
| **Whole run** | One clock from ingress threshold until the party crosses back out—short tombs, gauntlets, or timed Registry contracts. |

Clocks do not tick during preparation or aftermath unless the GM declares an ongoing site event (e.g. rival crew still inside your claim).

### What fills a segment

| Trigger | When | Ticks |
|---------|------|-------|
| **Time in site** | End of each **exploration scene** in Delve or Extract, or every **N combat rounds** of fighting/noise in those phases | **+1** (**N** from stamp danger: Hazard 4, Skirmisher 3, Elite 2, Boss 1) |
| **Failed Stealth / noise** | Failed **Stealth** to avoid notice; forced doors without silence; alarm trap | **+1**; nat 1 or critical failure **+2** |
| **Loud combat** | Unsuppressed fight (no attempt to muffle, no retreat after first exchange) | **+1**; sustained alarm or reinforcements already arriving **+2** |
| **Veil event** | Thin-veil surge, wrong-layer **EP** bleed, wild surge on thick Ether ([ether.md](ether.md)) | **+1**; major rift sign or Black Vale–class bleed **+2** |
| **Failed extract route** | Wrong fork, collapsed bridge, party split across layers past stamp | **+1** per serious mistake (GM) |
| **Hazard die (optional)** | End of each Delve scene or every **N** exploration rounds, GM rolls **d6** | **+1** on **1** unless the party took a declared precaution (silence ritual, ward chalk, Iron Pact “quiet hour”) |

**Ingress:** time-at-threshold and Stealth/noise only, unless the site is already unstable (then use Delve triggers).

**Extract strain:** if the party carries more than **STR×10** encumbrance, each trigger in Extract advances **+1 extra** segment (same event, heavier exit). See [Encumbrance under pressure](#encumbrance-under-pressure-td-057).

**Stacking:** Multiple triggers in one beat can tick more than once; narrate why the site noticed.

---

## Map claims, off-claim, and insurance (TD-053)

| Status | Definition | Mechanical effect |
|--------|------------|-------------------|
| **On-claim** | Party holds valid Registry **stamp** for the **AV-GRID** address and layer they occupy | Insurance valid; legal salvage sale; dispute resolution via Registry Moot |
| **Off-claim** | Wrong surface cell, unstamped layer, expired stamp, or depth past stamp without amendment | **No insurance**; salvage sale risk (fine 25–100 gp or confiscation); Iron Pact may seize cargo; **+1 legal risk** on aftermath Persuasion |
| **Claim-jump** | Another crew on your stamp without Moot ruling | Combat or arbitration; winner keeps extract tax rights |

### Stamp costs (reference)

| Danger tier | Stamp (30 days) | Optional insurance pool |
|-------------|-----------------|-------------------------|
| Hazard | 10–30 gp | 10 gp |
| Skirmisher | 30–60 gp | 15 gp |
| Elite | 80–150 gp | 20 gp |
| Boss | 200+ gp | 30 gp |

### Insurance payout (death on stamped run)

Premium paid in **preparation** (e.g. 15 gp). If the **contract holder** dies **on-claim** during the stamped delve:

| Payout | Amount |
|--------|--------|
| **Cash** | 50 gp to **account** (successor PC or player stash) |
| **Item** | One insured tagged item recovered by GM/table agreement OR next recovery run |
| **Void** | Off-claim death, fraud, or stamp expiry → no payout |

Disputes: **Registry Moot** ([factions/delvers-registry.md](../factions/delvers-registry.md)).

---

## Loot extraction and stash (TD-054)

| Phase | Rule |
|-------|------|
| **Ingress** | Gear on your sheet past the threshold = **body loot** until hub extract |
| **Death in site** | All body loot stays on map ([death-and-persistence.md](../meta/death-and-persistence.md)) |
| **Account stash** | **Persists across character death** — successor withdraws at hub (`services.stash`) |
| **Successful extract** | Carried salvage becomes **portable**; deposit to **account stash** at safe hub |
| **Stash hub** | Registry strongbox, licensed fence escrow, patron vault — **not** mid-delve camps |
| **Appraisal** | Aftermath: **Appraisal** vs fence offer (see below) |
| **Fence timing** | Same day as extract: full offer; +1 day −10%; +3 days −25% or "cold" |

### Registry tax and ash tithe

| Fee | Rate |
|-----|------|
| **Registry sales tax** | 10% of appraised salvage sold through licensed fences |
| **Ash tithe** | 2% of sale (funds unclaimed Tomb Dust burial) |

Debt attaches to **account**, not corpse ([death-and-persistence.md](../meta/death-and-persistence.md)).

---

## Faction standing (TD-055)

Account-level **reputation** runs **−3 to +3** per major faction. Adjust after deeds, desecration, bribery, or quest completion.

| Rep | Label | Typical effect |
|-----|-------|----------------|
| **−3** | Hostile | Refused service; ambush in faction territory; prices ×2 |
| **−2** | Unfriendly | +25% prices; no licenses |
| **−1** | Cold | Normal prices; wary NPCs |
| **0** | Neutral | Standard |
| **+1** | Favored | −10% fence margin; minor quest hooks |
| **+2** | Trusted | Stamp discounts (−10 gp); guide access |
| **+3** | Ally | Patron contracts; veto protection at Moot |

**Registry** (`32-C`, Edgecombe clerks): rep from survivor registration, tax payment, survey bounties. **Iron Pact** (underdeep): rep from vault respect vs claim-jump. **Knights** (Breley, `47-B` patrol): rep from Black Vale restraint. **Verdant Vale**: rep from grotto desecration (−2 per incident). Detail: [factions/README.md](../factions/README.md).

---

## Extraction scoring (TD-056)

Optional **run score** for brutal campaigns — partial success still matters.

| Metric | Points |
|--------|--------|
| **Salvage extracted** (gp after fence) | 1 pt per 10 gp |
| **Map cleared** (% rooms in site graph) | 2 pts per 25% |
| **Deed counter tick** | 5 pts per counter advanced |
| **Survivors** | 10 pts per PC extracted conscious |
| **Death on map** | −5 pts per PC lost (account still gains map knowledge) |

**Renown (optional):** 50+ pts in one campaign month → **Registry rank +1** (stamp discount, survey queue priority). Tie deed counters: [classes/deeds.md](../classes/deeds.md).

---

## Encumbrance under pressure (TD-057)

During **Extract** phase only, when a character is **over STR×10** units ([gear.md](../equipment/gear.md)):

| Each extract scene | Choose one |
|--------------------|------------|
| **Drop cargo** | Abandon highest-unit item (or 10 gp coin weight) in the site |
| **Push through** | Keep load; **+1 Extract threat clock** segment for that character |
| **Rearguard slow** | Party speed uses slowest member; over-cap members cannot Dash |

This stacks with **Extract strain** (+1 segment per trigger when over-cap). Narrate dropped loot as recoverable on a later run unless clock consequence destroys it.

---

### At six segments

When a clock hits **6/6**, apply **one** primary and **one** secondary consequence (or roll d6: 1–2 → A, 3–4 → B, 5–6 → C):

| | Consequence |
|---|-------------|
| **A — Spawn tier bump** | Next encounter on this stamp uses the **next** [monster threat tier](../monsters/README.md) (Hazard→Skirmisher→Elite→Boss). Boss overflow: add a second Skirmisher or Hazard swarm. |
| **B — Exit sealed** | Primary egress (stamped ingress route) is blocked—rubble, flood, ward slam. Reopen with **Athletics**, **Trap Handling**, or **Engineering** at **DC 13 + stamp danger step** (Hazard +0 … Boss +3), or find an alternate route; each failed attempt **+1** tick on the active clock. |
| **C — +1 danger tier** | All encounters until extract treat Registry **danger** as one step higher (Skirmisher stamp runs as Elite). Stacks once per clock fill. |

**Secondary (pick or roll d4):** pursuit wave (Skirmisher mix), **off-claim bleed** if still inside after one round at full (insurance void—[death-and-persistence.md](../meta/death-and-persistence.md)), or environmental hazard damage each round until exit.

**Fiction:** ceiling dust, distant horns, larvae in the walls—the table uses the mechanics above.

**After a fill:** Reset that clock to **3 segments filled** (pressure remains), or start a second face for fully **collapsed** sites (GM). Whole-run scope: do not reset until extract or TPK.

### Clock by delve phase

| Phase | Clock | Typical triggers |
|-------|-------|------------------|
| **Preparation** | None | Stamp lists danger tier and active **EP**—sets **N** and veil triggers. |
| **Ingress** | Ingress or run | Stealth at gate, rivals, ward alarm, slow approach eating stamp validity |
| **Delve** | Delve or run | Scenes, combat noise, traps, veil chambers, depth past stamp |
| **Extract** | Extract or run | Pursuit, encumbrance strain, sealed exit, rearguard fights |
| **Aftermath** | None | Collapse may strand bodies on-map for recovery hooks |

**Example:** Stamp `47-B-UG-3`, Elite, per-phase clocks. Loud fight in chamber 4 (**+1**), failed Stealth past the knight ward (**+1**), scene end (**+1**). Delve clock **3/6**. Hazard die rolls 1 (**+1**) → **4/6**; they turn back. Extract: pursuit fight (**+1** loud), scene end (**+1**) → **2/6** on Extract. They reach `47-B` before fill.

Stamped **danger rating** sets baseline encounter tier; the clock raises pressure over time—not every tick spawns a fight.

---

## AV-GRID on delver maps

Maps show a primary address and layer stack, for example:

```
PRIMARY: 47-B-UG-3
SURFACE ENTRY: 47-B (ruin gate 3)
VEIL: active — treat as 47-B-EP in chambers 7–9
DANGER: Elite (Registry 1204 rev.C)
```

A party that enters `47-B` but delves without a stamped `UG` level is **off-claim** (no insurance, legal risk). Address data: [`data/av-grid/av-grid.json`](../../data/av-grid/av-grid.json). See [grid.md](grid.md).

## Site types

| Type | Examples | Threat profile |
|------|----------|----------------|
| **Tombs** | Breley undercrypts, barrow rows | Undead, traps, hollow knights |
| **Ruins** | Shadowfen, surface forts | Mimics, wraiths, environmental |
| **Thin-veils** | Woods, caverns, battlefields | Ether larvae, aetherial beasts |
| **Vaults** | Dwarven sealed halls | Constructs, slimes, Pact politics |

## Realm attitudes

| Realm | Stance |
|-------|--------|
| **Ealdormere / Breley** | Licensed delving; knights monitor “acceptable risk” |
| **Boydon Tower** | Arcane priority; bans reckless veil-poking near tower |
| **Edgecombe** | Practical; buries locals; profits from guides |
| **Verdant Vale** | Opposes desecration; will sabotage grotto maps |
| **Iron Pact** | Controls underdeep claims; harsh penalties for claim-jumping |
| **Frostfall** | Rare delves; ice tombs are legendary contracts |

## Fortune and grit

**LUC (Fortune)** reflects the setting’s belief that survival is partly luck. **Gritty crits** and **armor tradeoffs** (knight vs ninja) reinforce that gear and position beat hoping for a natural 20.

Faction detail: [factions/delvers-registry.md](../factions/delvers-registry.md). Death and account persistence: [meta/death-and-persistence.md](../meta/death-and-persistence.md).

---

## Wilderness random encounters (TD-064)

When traveling between stamped sites in the **MVP corridor** (Heartlands → Shadowfen):

1. Each **travel scene**, roll **1d6**. On **1**, an encounter triggers.
2. Look up the party's current surface cell in [`data/av-grid/av-grid.json`](../../data/av-grid/av-grid.json) — use primary **biome** (HL, WM, or SF) and `dangerRating`.
3. Roll on the matching table in [`data/encounters/wilderness.json`](../../data/encounters/wilderness.json).
4. Monster names map to [`systems/monsters/`](../monsters/README.md) stat blocks or [`data/monsters/`](../../data/monsters/) JSON.

**Ingress/delve/extract:** use site encounters and threat clock instead — wilderness tables are for **unstamped travel** only unless GM declares otherwise.
