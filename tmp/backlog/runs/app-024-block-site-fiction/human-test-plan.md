# Human Playtest Plan: APP-024-block-site-fiction

**backlog_ticket:** APP-024  
**Commit:** pending (Stage 7 — use latest commit with APP-024 in message; impl may be uncommitted until batch commit)  
**Play entry:** `cd app && python main.py` — see [app/README.md](../../../app/README.md)

**Scope:** APP-024 adds a **surface-only site-entry fiction gate** in the orchestrator. While `party.mode == "surface"` and no successful `enter_dungeon` / `site_enter` ran this turn, interior/threshold-crossing prose is stripped and replaced with a code-owned refusal line. Automated pytest (7 cases) passed at impl QA; manual play validates **live LLM + PyGame UI** behavior pytest mocks cannot fully cover (marker false positives, multi-turn exploration, map/travel regression).

## Prerequisites

- [ ] Python 3.11+ with deps (`pip install -r app/requirements.txt`)
- [ ] OpenRouter API key in `app/.env` (`OPENROUTER_API_KEY=…`)
- [ ] **Surface exploration save:** either **`new game`** through creation to Registry hub at **Breley Keep (`32-C`)**, **or** **Continue** from a save already finalized on surface near the undercrypt entrance
- [ ] Optional log watch: `app/logs/session-YYYY-MM-DD.jsonl`
- [ ] Repo root cwd for TC-1 pytest gate

## What to look for (all TCs)

| Bad (fail) | Good (pass) |
|------------|-------------|
| Narration describes **crossing the threshold**, **torchlit corridors**, **vault interior**, or **"you are now in the crypt/undercrypt/dungeon"** while stats/map still show **surface / Breley (`32-C`)** | Surface banter at the entrance is OK; interior crossing prose is **absent** or replaced by refusal |
| `[Mechanics failed — …]` banner **followed by** success entry prose ("You step into…", "torchlit", "corridor") | Banner may appear; body is **refusal line** and/or benign surface text — **no** entry-success prose beneath banner |
| Legitimate **in-dungeon room search** stripped to empty/refusal | Interior room description **unchanged** when already inside (`dungeon` / `site` mode) |
| Wilderness/travel prose mentioning "crypt" **without crossing verbs** removed entirely | Adjacent-cell travel still works; non-entry surface prose preserved |

**Code-owned refusal (exact copy when strip empties prose):**

> The entrance holds you at the threshold — the Registry ledger still shows you on the surface. Crossing requires a successful **enter_dungeon** or **site_enter** call; the delving clock does not start until then.

**Engine truth checks:** sidebar **Location** still **Breley Keep / `32-C`** (or surface root) when gate blocks; phase badge should **not** flip to delve from engine state alone. After successful entry, location/mode should reflect **undercrypt / `32-C-UG-1`** (or site/dungeon layer on map).

---

## Test cases

### TC-1: Automated regression gate (recommended before manual play)

**Goal:** Confirm APP-024 module and app regression slice still green.

| Step | Action | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | From repo root: `python -m pytest app/tests/test_exploration_site_entry_gate.py -q` | Exit code **0**; **7** tests pass | [ ] |
| 2 | From repo root: `python -m pytest app/tests/ -q -k "not exploration_site_entry"` | Exit code **0**; no regressions | [ ] |

**Failure signals:** Any pytest failure — stop manual play and file bug.

---

### TC-2: Setup — surface at Breley undercrypt entrance (maps to all manual TCs)

**Goal:** Reach **surface** exploration at **Breley Keep (`32-C`)** with a finalized character — the scenario from domain spec § Manual verification.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | `cd app && python main.py` | Window opens, no traceback | [ ] |
| 2 | **`new game`** → complete creation (name → race → stats → class → skills → spells → equipment → reception), **or** **Continue** from a save already at hub | Character finalized; not stuck in creation | [ ] |
| 3 | If not already at Breley, travel to **`32-C`** (map click on Breley Keep cell, or type e.g. `travel to Breley Keep` / `go to 32-C`) | Sidebar **Location** shows Breley / **`32-C`**; phase **preparation** (or hub-appropriate surface phase) | [ ] |
| 4 | Confirm you are **not** inside the undercrypt yet | Map shows surface layer; no `UG-1` as current location | [ ] |

**Failure signals:** Cannot reach surface hub; crash during creation/travel; already inside undercrypt before TC-3 (reset save or `new game`).

---

### TC-3: Surface — no-tool / wrong-tool entry blocked (maps to AC: block without successful entry tool)

**Goal:** Prompting site entry without a successful `enter_dungeon` / `site_enter` must **not** deliver interior fiction.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | At Breley surface (`32-C`), type **`I enter the crypt.`** (or **`I go down into the undercrypt.`**) and submit | GM responds | [ ] |
| 2 | Read narration body | **No** lines describing threshold crossing, torchlit corridors, vault interior, or "you are now inside the crypt/undercrypt/dungeon" | [ ] |
| 3 | If model narrated entry anyway | Refusal line appears (see § What to look for) **or** only benign surface/entrance banter remains | [ ] |
| 4 | Check sidebar **Location** / map | Still **surface / `32-C`** — entry did **not** commit mechanically | [ ] |
| 5 | Optional: repeat with **`I delve into Breley undercrypt`** if first prompt was ignored | Same gate behavior — no interior success prose without tool commit | [ ] |

**Failure signals:** Full interior scene while still on `32-C`; map jumps to `UG-1` without successful entry tool; crash.

---

### TC-4: Surface — failed `enter_dungeon` + LLM entry prose (maps to AC: `all_failed and content` path)

**Goal:** When tools fail but the model still writes entry success prose, player sees failure banner + **safe** text — not hallucinated interior beneath the banner.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Still on surface at Breley, try an entry prompt that may fail tools — e.g. **`enter the undercrypt now`** without a clear address, or **`set_phase delve`** then **`enter`** (APP-022 may hint; failure is OK) | Response may include **`[Mechanics failed — …]`** mentioning `enter_dungeon`, `set_phase`, or similar | [ ] |
| 2 | Read text **after** the failure banner | **No** "You step into…", **no** "torchlit", **no** "corridor" success prose; refusal line and/or surface-safe text only | [ ] |
| 3 | Check sidebar **Location** | Still **surface / `32-C`** | [ ] |

**Failure signals:** Banner present but entry-success paragraphs follow; engine shows undercrypt location without `ok: true` entry tool.

**Note:** Live LLM tool choice varies — if this turn succeeds on first try, skip to TC-5 and retry TC-4 on a fresh surface turn with vaguer wording.

---

### TC-5: Happy path — successful entry allows fiction (maps to AC: authorized entry prose)

**Goal:** After successful `enter_dungeon` / `site_enter`, entry and interior narration is **allowed** and engine state commits.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | From Breley surface, type a clear entry intent — e.g. **`I enter Breley undercrypt`** or **`enter_dungeon site_address 32-C-UG-1`** (natural language OK if model calls tool) | GM narrates entry; tools succeed (no persistent `[Mechanics failed — enter_dungeon]` for this turn) | [ ] |
| 2 | Read narration | Entry / interior description **present** — crossing and undercrypt atmosphere **allowed** after commit | [ ] |
| 3 | Check sidebar **Location** and/or map | Shows **undercrypt / `32-C-UG-1`** or dungeon/site layer — **not** still surface-only | [ ] |
| 4 | Phase badge | May show **delve** or site-appropriate phase after entry (engine-driven) | [ ] |

**Failure signals:** Tools succeed but all interior prose stripped to refusal; location stays `32-C` despite successful narration; crash on entry.

---

### TC-6: In-dungeon bypass — interior narration without re-entry (maps to AC: no regression inside site)

**Goal:** Gate **off** when already inside; room/search narration works without calling entry tools again.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | Continuing from TC-5 inside undercrypt, type **`I search the alcove.`** or **`I examine the corridor ahead.`** | GM describes room/interior normally | [ ] |
| 2 | Read narration | Interior details **retained** — **not** replaced by refusal line | [ ] |
| 3 | Optional second turn: **`I listen for movement in the vault.`** | Same — no over-aggressive strip | [ ] |

**Failure signals:** Refusal line or empty narration on benign in-site actions; gate treats dungeon room prose as premature entry.

---

### TC-7: Travel regression — surface prose not over-stripped (maps to spec non-goal / sanitizer false-positive check)

**Goal:** Non-entry surface travel still works; gate does not block wilderness/hub prose.

| Step | Action (in the running game) | Expected result | Pass |
|------|------------------------------|-----------------|------|
| 1 | **`new game`** or reload surface save at **`32-C`** (exit undercrypt first if needed — e.g. **`leave the site`** / travel to surface if engine supports) | Back on Breley surface | [ ] |
| 2 | Click an **adjacent map cell** on the AV-GRID mini-map (or type travel to a neighboring surface address) | Travel resolves; narration describes movement/arrival | [ ] |
| 3 | Read narration | Travel/hub/wilderness prose **present**; no spurious refusal unless prompt was explicit site **entry** | [ ] |
| 4 | Sidebar **Location** | Updates to new surface cell | [ ] |

**Failure signals:** Travel blocked or narration collapsed to refusal for non-entry travel; map click no-op.

---

### TC-8: Sticky entry commit — optional / best-effort (maps to AC: success-then-failed retry)

**Goal:** Same-turn success then failed retry of `enter_dungeon` must **not** revoke entry fiction. **Primarily covered by pytest** (`test_success_then_failed_enter_dungeon_retains_fiction`); manual repro is optional.

| Step | Action (in the running game) | Expected result | Pass |
|------|--------|-----------------|------|
| 1 | *(Optional)* If you observe a turn where entry **succeeded** then a follow-up tool error mentions **`enter_dungeon`** again in the same response | Entry/interior prose from the successful commit **still visible** — not stripped because a later retry failed | [ ] |

**Failure signals:** Interior prose stripped after apparent successful entry in the same turn.

**Note:** Skip sign-off dependency on TC-8 if not observed — TC-1 covers this path automatically.

---

## Acceptance criteria sign-off

| AC / Req | Criterion | Verified by | Pass |
|----------|-----------|-------------|------|
| Ticket AC1 | Block site-entry fiction on surface unless turn includes successful `enter_dungeon` / `site_enter` | TC-3, TC-4 | [ ] |
| Ticket AC2 | Entry commit not revoked by later failed retry same turn | TC-1 (auto), TC-8 (optional) | [ ] |
| E3 regression | In-dungeon interior narration unchanged | TC-6 | [ ] |
| Non-goal | Travel / surface banter not over-stripped | TC-7 | [ ] |
| Happy path | Successful entry allows fiction + engine commit | TC-5 | [ ] |

## Sign-off

| Tester | Date | Result |
|--------|------|--------|
| | | all TC pass / issues: … |

## Notes for next ticket

- **APP-077:** Code-owned exploration footer runs **after** APP-024 strip in compose order — when APP-077 lands, re-run TC-3/TC-6 to ensure both layers coexist.
- **APP-022:** Failed `set_phase(delve)` hints are separate; TC-4 failure banner may mention hints — not a failure here.
- **APP-028:** Combat `[Mechanics failed — …]` prefix-only path is unchanged; this plan does not exercise combat.
- **LLM variance:** TC-3/TC-4 may need 1–2 retries with different phrasing if the model calls a successful entry tool immediately — focus on **engine location** + **narration markers**, not exact GM wording.
- **E7 telemetry:** `premature_site_entry` drift logging deferred — no JSONL assertion in this plan.
- **Sanitizer edge cases:** If TC-7 fails (wilderness stripped) but TC-3 passes, file follow-up — likely marker false positive (e.g. benign "corridor" on surface).
