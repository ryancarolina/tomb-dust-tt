# Implementation Plan: APP-023-friendly-travel-av-grid

**Status:** draft (plan r2 — QA PLAN-001/002)  
**backlog_ticket:** APP-023  
**ticket_path:** tmp/backlog/app-023-friendly-travel-name-to-av-grid.md  
**domain_spec:** tmp/app-exploration-delve-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Add engine **`resolve_surface_address(content, query, from_address)`** in `play/tomb_gm/services/world.py` — exit-scoped friendly-name resolution for surface travel. Reuse slug/scoring patterns from `site_resolve.py` with **apostrophe folding** and **exit `tradeRoute`** scoring. Wire the same helper into **`bridge.world_travel`** (pre-`can_travel`) and **`process_beat`** travel branch (post-`_find_address`). Fail closed: ambiguity and unknown never move the party; layered-only matches return **`USE_ENTER_DUNGEON`**.

**Out of scope:** JSON `aliases`, global name index, `cmd_world.py` CLI parity, map UX (APP-063), `enter_dungeon` / `resolve_site_address` changes.

**TurnTruth:** Resolver returns structured errors only — no LLM narration path touched.

---

## Code-path traces (current → planned)

### Flow A — `bridge.world_travel` (LLM tool / primary AC path)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:_execute_tool` | `world_travel` → `bridge.world_travel(**args)` | unchanged |
| 2 | `bridge.py:world_travel` | Load party `from_addr`; `WorldService` + `ContentService` | unchanged |
| 3 | same | `world.can_travel(from_addr, to_address)` immediately (`198`) | **If `to_address.strip()` not in `legal_exits(from_addr)`** (or not exact canonical id match): call `resolve_surface_address(content, to_address, from_address=from_addr)` |
| 4 | same | — | On `resolved["ok"]`: set `to_address = resolved["address"]`; optional attach `resolved_from` to return |
| 5 | same | — | On resolve fail: return `{ok: false, error, from, to, ...}` from resolver (preserve `from`/`to` query fields) — **no DB update** |
| 6 | same | `can_travel` → UPDATE party_state → `log_event` → cell payload (`198–208`) | unchanged after resolved id |
| 7 | same | Errors: `UNKNOWN_ADDRESS`, `INVALID_TRAVEL`, `UNKNOWN_FROM_ADDRESS` only | Add resolver errors: `AMBIGUOUS_ADDRESS`, `USE_ENTER_DUNGEON`; `UNKNOWN_ADDRESS` may include exit hint `message` |

**Passthrough:** When `to_address` is already a legal exit id (case-insensitive exact match), skip resolver — existing canonical path unchanged (R7 / T canonical row).

---

### Flow B — `process_beat` travel (friendly name failure path today)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `bridge.py:process_beat` | Delegates to `beat.process_beat` | unchanged |
| 2 | `beat.py:process_beat` | Per line: `_intent_travel` → `_find_address` (regex only) | unchanged through `_find_address` |
| 3 | same | `travel_hint` + no dest → `legal_exits[0]` default (`434–438`) | **unchanged** — not APP-023 |
| 4 | same | No `dest` → `NO_DESTINATION` mechanical (`456–464`) | **When `travel_intent == "travel"` and no `dest`:** call `resolve_surface_address(content, text, from_address=address)` — use full line text or extract destination phrase after travel verb (see § Beat query extraction) |
| 5 | same | — | On resolve ok: `dest = resolved["address"]`; fall through to `_apply_travel` |
| 6 | same | — | On fail: map errors per domain spec — `UNKNOWN_ADDRESS` → `error: NO_DESTINATION` (same `message`); pass through `AMBIGUOUS_ADDRESS`, `USE_ENTER_DUNGEON` unchanged |
| 7 | `beat.py:_apply_travel` | `world.can_travel` → UPDATE → log (`164–200`) | unchanged — receives resolved canonical id |

**Beat query extraction:** Prefer resolving the substring after travel verbs (`travel to`, `go to`, `head to`, `walk to`, `move to`) when present; else pass trimmed line. Keeps “We travel to kings road” and “kings road” aligned with tool arg `kings road`.

---

### Flow C — `resolve_surface_address` (new engine API)

| Step | File:symbol | Action |
|------|-------------|--------|
| 1 | `world.py:resolve_surface_address` | Normalize query: strip, lower; build `query_slug` via `site_resolve._slug` on **folded** text |
| 2 | same | `exits = WorldService(content).legal_exits(from_address)`; if `None` → `UNKNOWN_FROM_ADDRESS` shape |
| 3 | same | **Passthrough:** if folded query equals exit id (case-insensitive) and ∈ exits → `{ok: true, address, resolved_from: query}` |
| 4 | same | **Pass 1 candidates:** exits where `layerStack == []` and `address != from_address` (unless query is exact id for current cell — R7) |
| 5 | same | Score each candidate: `displayName` tiers (100/90/70/60) + optional exit `tradeRoute` (80 **only when display tier > 0** — compound gate); **never** score `from_address` displayName/tradeRoute for non-exact queries |
| 6 | same | Pick best score; ties → `AMBIGUOUS_ADDRESS` + `options`; score 0 → go pass 2 |
| 7 | same | **Pass 2:** layered exits only (`layerStack` non-empty); same scoring; single winner → `USE_ENTER_DUNGEON`; ties → `AMBIGUOUS_ADDRESS`; still 0 → `UNKNOWN_ADDRESS` with surface exit hint list |
| 8 | same | Success → `{ok: true, address, displayName, resolved_from}` |

**Scoring helpers (new, module-level in `world.py`):**

```python
_APOSTROPHE_FOLDS = str.maketrans("", "", "'\u2019")  # ASCII + Unicode right single quote

def _fold_apostrophes(text: str) -> str:
    return text.translate(_APOSTROPHE_FOLDS)

def _display_match_score(
    query_norm: str, query_slug: str, *, address: str, display_name: str
) -> int:
    # 100 address exact/slug; 90 display exact/slug; 70 slug substring; 60 name substring
    # All substring/slug work on _fold_apostrophes(...) for query + display_name

def _score_surface_candidate(
    query_norm: str, query_slug: str, *, address: str, display_name: str, trade_route: str | None
) -> int:
    display_score = _display_match_score(...)
    route_score = 0
    if trade_route and display_score > 0:
        # Compound gate (PLAN-001): tradeRoute is a boost, not a standalone match.
        # Prevents route-only mile posts (32-D) beating named road cells (33-C).
        if query_slug == _slug(trade_route) or query_slug in _slug(trade_route) or _slug(trade_route) in query_slug:
            route_score = 80
    return max(display_score, route_score)
```

Import **`_slug`** from `tomb_gm.services.site_resolve` — do not duplicate slug rules.

**Scoring policy (PLAN-001 fix):** **`tradeRoute` score 80 applies only when the same candidate also scores > 0 on `displayName` / address tiers (60–100).** Route metadata alone must not win over a neighbor whose **display name** matches the query. No JSON edit to `32-D`; no global tie-break heuristics.

**Full candidate table — `kings road` @ `32-C` (pass 1 surface, live JSON 2026-05-22):**

| Exit | displayName | tradeRoute | display tier | route tier (gated) | **Total** |
|------|-------------|------------|--------------|-------------------|-----------|
| `31-C` | Crystaline hills | — | 0 | — | **0** |
| `32-B` | Heartland fields | — | 0 | — | **0** |
| `32-D` | Heartland mile post | kings-road | 0 | **suppressed** (display 0) | **0** |
| `33-C` | King's Road (east bend) | — | **70** (slug `kings-road` ⊆ `kings-road-east-bend`) | — | **70** |

**Winner:** **`33-C`** — T1/T6 and human Breley hub playtest pass.

**Naming:** API is **`resolve_surface_address`** — not `build/tools/av_grid.py:resolve_surface` (surface-root parser for grid tooling).

---

### Flow D — `resolve_site_address` (reference pattern — unchanged)

| Step | File:symbol | Notes for APP-023 |
|------|-------------|-------------------|
| 1 | `site_resolve.py:_match_score` | Scores 100/90/70/60 — **no** apostrophe fold, **no** `tradeRoute`, **no** exit scope |
| 2 | `site_resolve.py:resolve_site_address` | Child-first from `current_surface_address`, then global layered scan |
| 3 | `bridge.py:enter_dungeon` | Calls site resolver before `enter_site` (`628–666`) — **do not modify** |

Surface resolver differs: **exit-scoped**, surface-first pass, `tradeRoute` 80, apostrophe fold, `USE_ENTER_DUNGEON` for layered-only matches.

---

### Flow E — CLI `cmd_world.py:handle_travel` (not in Expected files)

| Step | Current | Planned |
|------|---------|---------|
| 1 | `get_cell(to_address)` or `unknown_address_error` (`139–140`) | **No change in APP-023** — optional parity noted in domain spec |
| 2 | `can_travel` | Friendly CLI travel still fails until follow-up ticket |

Existing `test_world.py` CLI tests remain valid for canonical ids; new friendly cases test **`resolve_surface_address` directly** + beat CLI.

---

### Flow F — Map click (unchanged)

`app/ui/app.py` submits `travel to {canonical_id}` — bypasses resolver; regression via existing map tests / human plan.

---

## Task breakdown

### 1. Engine resolver — `play/tomb_gm/services/world.py`

#### 1.1 Module helpers

- `_fold_apostrophes(text: str) -> str`
- `_display_match_score(query_norm, query_slug, *, address, display_name) -> int` — tiers 100/90/70/60 only
- `_score_surface_candidate(...)` — `max(display, gated tradeRoute 80)` per compound gate above
- `_surface_exit_hints(content, exits: list[str]) -> str` — format legal surface exits with `displayName` for `UNKNOWN_ADDRESS.message`

#### 1.2 `resolve_surface_address(content, query, *, from_address) -> dict`

Implement R1–R4 per domain spec § Friendly surface travel resolution:

| Pass | Candidates | Outcome |
|------|------------|---------|
| 0 | Exact id ∈ `legal_exits` | Immediate success |
| 1 | Surface exits from `legal_exits`, exclude `from_address` for fuzzy match | Best > 0 → resolve; tie → `AMBIGUOUS_ADDRESS`; 0 → pass 2 |
| 2 | Layered exits from `legal_exits` | Single best → `USE_ENTER_DUNGEON`; tie → `AMBIGUOUS_ADDRESS`; 0 → `UNKNOWN_ADDRESS` |

**Error shapes** (include `query` where spec lists it):

| Error | Keys |
|-------|------|
| `AMBIGUOUS_ADDRESS` | `ok`, `error`, `query`, `options: [{address, displayName}]`, `message` |
| `UNKNOWN_ADDRESS` | `ok`, `error`, `query`, `message` (lists surface exit hints) |
| `USE_ENTER_DUNGEON` | `ok`, `error`, `query`, `message` (names matched layered exit; use `enter_dungeon`) |

Keep `WorldService.can_travel`, `legal_exits`, `unknown_address_error` unchanged — resolver is additive.

---

### 2. Bridge hook — `app/gm/bridge.py`

In `world_travel` (~L184–208), after loading `from_addr` and before `can_travel`:

```python
from tomb_gm.services.world import WorldService, resolve_surface_address

exits = world.legal_exits(from_addr) or []
to_stripped = to_address.strip()
if to_stripped.lower() not in {e.lower() for e in exits}:
    resolved = resolve_surface_address(content, to_stripped, from_address=from_addr)
    if not resolved.get("ok"):
        return {**resolved, "from": from_addr, "to": to_address}
    to_address = resolved["address"]
    resolved_from = resolved.get("resolved_from")
else:
    resolved_from = None

ok, code = world.can_travel(from_addr, to_address)
# ... existing UPDATE / return; optionally include resolved_from when set
```

**Note:** Exact-id check uses `legal_exits` membership, not global `get_cell` — ids not in exits still run resolver (then may fail `INVALID_TRAVEL` if resolver wrongly succeeds — tests guard this).

---

### 3. Beat parity — `play/tomb_gm/services/beat.py`

In travel branch (~L431–465), when `dest` is still `None` after `_find_address` (and not `travel_hint` default path):

```python
from tomb_gm.services.world import resolve_surface_address

if travel_intent == "travel" and not dest:
    query = _extract_travel_destination(text)  # new helper: verb phrase or full line
    resolved = resolve_surface_address(content, query, from_address=address)
    if resolved.get("ok"):
        dest = resolved["address"]
    else:
        err = resolved.get("error")
        beat_err = "NO_DESTINATION" if err == "UNKNOWN_ADDRESS" else err
        mechanical.append({
            "ok": False,
            "action": "travel",
            "error": beat_err,
            "message": resolved.get("message", ""),
            "query": resolved.get("query"),
            "options": resolved.get("options"),
            "slot": slot,
        })
        continue
```

Add `_extract_travel_destination(text: str) -> str` — regex strip leading `travel|go|head|walk|move` + optional `to`, return remainder or full text.

Do **not** call resolver for `travel_hint` intent (compass default unchanged).

---

### 4. Tests — `play/tomb_gm/tests/test_world.py`

Add `ContentService` fixture (mirror `test_site_resolve.py`: `ContentService(REPO / "build")`).

#### 4.1 Resolver unit tests (direct import)

| ID | Test name | Setup | Assert |
|----|-----------|-------|--------|
| **T1** | `test_resolve_surface_address_kings_road` | `from_address="32-C"`, query `"kings road"` | `ok`, `address == "33-C"`, `resolved_from == "kings road"` |
| **T6** | `test_resolve_surface_address_kings_road_not_current_cell` | Same as T1 | `address != "32-C"` |
| **T3** | `test_resolve_surface_address_exit_scope` | `from_address="32-C"`, query `"silversea cove"` | `error == "UNKNOWN_ADDRESS"` — global duplicate not in exits |
| **T4** | `test_resolve_surface_address_ambiguous` | `from_address="1-B"`, query `"silversea cove"` | `error == "AMBIGUOUS_ADDRESS"`; `options` addresses `{1-A, 2-B}` |
| **T5** | `test_resolve_surface_address_use_enter_dungeon` | `from_address="32-C"`, query `"undercrypt"` | `error == "USE_ENTER_DUNGEON"`; message mentions enter/dungeon or site |
| — | `test_resolve_surface_address_canonical_passthrough` | `from_address="32-C"`, query `"33-C"` | `ok`, `address == "33-C"` unchanged |
| — | `test_resolve_surface_address_then_can_travel` | T1 resolve + `WorldService.can_travel` | `(True, None)` — simulates bridge gate |
| **T8** | `test_world_travel_friendly_kings_road_bridge` | `GameBridge` session at `32-C`; `world_travel(to_address="kings road")` | `ok`; `to == "33-C"`; `bridge.status()["party"]["address"] == "33-C"` |

**T8 (PLAN-002):** Use `isolated_workspace` + `GameBridge.init()` + `campaign_new` / `session_start` (or `_bootstrap_session` pattern from existing `test_world.py`). Lives in **`test_world.py`** (Expected files) — no `app/tests/` expansion required. Asserts pre-resolve hook + DB UPDATE, not resolver alone.

**T4 fixture pinned:** Party **`1-B`**; legal surface exits **`1-A`** and **`2-B`** both `displayName` “Silversea cove” (verified live JSON 2026-05-22). Compound gate unchanged — both tie at display tier **90**.

#### 4.2 CLI regression

Keep existing `test_world_travel_*` canonical tests green — no CLI friendly travel until `cmd_world` follow-up.

---

### 5. Tests — `play/tomb_gm/tests/test_beat.py`

| ID | Test name | Setup | Assert |
|----|-----------|-------|--------|
| **T2** | `test_beat_travel_friendly_kings_road` | Seed session at `32-C`; line `"travel to kings road"` | mechanical travel `ok`; party address `33-C` |
| **T7** | `test_beat_travel_unknown_maps_no_destination` | `from_address="32-C"`; line `"travel to silversea cove"` | `error == "NO_DESTINATION"` (not `UNKNOWN_ADDRESS`) |

Reuse `_seed_session` pattern from existing beat tests.

---

### 6. Optional on close — `app/gm/tools.py`

Update `world_travel.to_address` description: AV-GRID id **or** friendly surface place name from current compass exits. Defer to ticket close / same PR if time — not blocking AC.

---

### 7. Domain spec sync on close — `tmp/app-exploration-delve-spec.md`

On `release APP-023 --done`:

1. Mark problem log item resolved.
2. Changelog: resolver shipped, tests T1–T7.
3. Optional: `tmp/app-gamebridge-spec.md` `world_travel` row (coordination — not Expected files).

---

## Requirements → implementation map

| ID | Requirement | Locus | Test |
|----|-------------|-------|------|
| **R1** | `resolve_surface_address` exit-scoped, two-pass | `world.py` | T1, T5 |
| **R2** | Scoring + apostrophe fold + **compound-gated** exit `tradeRoute`; exclude current cell | `world.py` | T1, T6 |
| **R3** | `AMBIGUOUS_ADDRESS` / `UNKNOWN_ADDRESS` + hints | `world.py` | T3, T4 |
| **R4** | Layered fallback → `USE_ENTER_DUNGEON` | `world.py` | T5 |
| **R5** | `bridge.world_travel` pre-resolve | `bridge.py` | T1, T8, `can_travel` chain test; human PyGame |
| **R6** | `process_beat` shared resolver + error map | `beat.py` | T2, T7 |
| **R7** | Canonical passthrough | `world.py` + bridge | passthrough test |

---

## Files (must ⊆ ticket Expected files)

| File | Changes |
|------|---------|
| `play/tomb_gm/services/world.py` | `_fold_apostrophes`, `_score_surface_candidate`, `resolve_surface_address`, hint helper |
| `app/gm/bridge.py` | Pre-resolve in `world_travel` |
| `play/tomb_gm/services/beat.py` | `_extract_travel_destination`; resolver call + error map in travel branch |
| `play/tomb_gm/tests/test_world.py` | Resolver unit tests T1, T3–T6, passthrough, can_travel chain, **T8 bridge friendly travel** |
| `play/tomb_gm/tests/test_beat.py` | T2, T7 friendly / unknown beat travel |
| `app/gm/tools.py` | *(optional on close)* tool description update |

**Not in Expected files (close-time only):** `tmp/app-exploration-delve-spec.md`, `tmp/app-gamebridge-spec.md`.

**Explicitly not changing:** `build/data/av-grid/av-grid.json`, `play/tomb_gm/cli/cmd_world.py`.

---

## Tests

| Step | Command | Expected |
|------|---------|----------|
| Resolver + world | `python -m pytest play/tomb_gm/tests/test_world.py -q` | all green |
| Beat travel | `python -m pytest play/tomb_gm/tests/test_beat.py -q` | all green |
| Site scoring regression | `python -m pytest play/tomb_gm/tests/test_site_resolve.py -q` | no regressions |
| Pre-claim gate | `python tmp/backlog/claim_ticket.py impl-check APP-023` | pass before `app/` edits |

---

## Rollback

Revert `world.py`, `bridge.py`, `beat.py`, and test additions. No migrations, flags, or JSON changes.

---

## Open questions

- **`_extract_travel_destination` heuristic:** Plan uses verb-stripped remainder; if edge cases fail playtest (e.g. “kings road travel”), expand regex in follow-up — not blocking T2.
- **Bridge return `resolved_from`:** Optional metadata on success — include if trivial; not required by AC.
- **T4 fixture:** Pinned to **`1-B` / `silversea cove`** — Dev need not search grid at impl time.
- **Session claim:** Run `impl-check APP-023` before editing `app/gm/bridge.py` (hook gate).
- **PLAN-001 resolved (r2):** Compound `tradeRoute` gate — no av-grid.json change; full `32-C` exit table in § Flow C.
