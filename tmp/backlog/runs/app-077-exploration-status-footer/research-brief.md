# Research Brief: APP-077-exploration-status-footer

**Date:** 2026-05-22  
**Question:** Where does exploration/combat narration still rely on LLM-authored status lines, and how should a code-owned footer from `bridge.status()` mirror the creation pattern (`strip_llm_status_tags` + `format_creation_status`)?

**backlog_ticket:** APP-077  
**ticket_path:** tmp/backlog/app-077-code-owned-exploration-status-footer.md  
**domain_spec:** tmp/app-exploration-delve-spec.md  
**ticket_status_at_start:** in_progress  

**registry_gap:** false

## Registry gap justification

[`tmp/app-exploration-delve-spec.md`](../../../app-exploration-delve-spec.md) is the registered owner for exploration path in orchestrator, travel/site tools, and map UX ([`tmp/app-master-spec.md`](../../../app-master-spec.md) § Spec registry — **Exploration & delve**). Ticket expected files (`orchestrator.py`, `creation.py`, `system_prompt.py`, `test_exploration_status_footer.py`, domain spec + cross-link in `app-llm-orchestrator-spec.md`) are a subset of that domain and orchestrator cross-refs. No new domain spec row is required.

## Summary

Exploration and combat still instruct the LLM to emit a bracket status line every turn (`system_prompt.py` L213, L273). `_llm_loop` and `_combat_llm_loop_inner` return raw model prose to `_emit_narration` with **no** status strip or code footer — unlike creation, which uses `_compose_creation_narration` → `strip_llm_status_tags` + `format_creation_status()`.

A stub `_compose_exploration_narration` exists for **APP-024 only** (site-entry sanitizer + refusal line); its docstring names APP-077 but strip/footer logic is **not implemented**. Exploration applies compose in `process_turn` after `_llm_loop` and inside `_llm_loop` on the `all_failed and content` path; **combat never calls compose** (`_combat_turn` → `_emit_narration` directly).

`strip_llm_status_tags()` in `creation.py` (APP-073) already removes `[Location:…]`, `[Phase:…]`, and any `Awaiting: TOKEN` inline — reusable for exploration prose. **`format_exploration_status(status)` does not exist**; the nearest reference is `_auto_finalize`'s hardcoded bracket footer (`orchestrator.py` L1992). `_check_creation_drift` runs on every `_emit_narration` but **returns immediately** outside creation scope — no exploration drift telemetry today.

Fix = add `format_exploration_status(bridge.status())`, extend `_compose_exploration_narration` (APP-024 → strip meta/status → append footer), wire combat success paths, soften/remove prompt mandate, optional `log_exploration_drift` when stripped prose disagrees with engine. APP-065 chips already use `bridge.status().awaiting` via `get_player_suggestions()` — footer ownership still matters for player-visible lies, TTS/display, and future parsers.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Exploration turn | `app/gm/orchestrator.py` `process_turn` L1135–1181 | `_llm_loop` → `_compose_exploration_narration` → `_emit_narration` |
| LLM loop | `app/gm/orchestrator.py` `_llm_loop` L2501–2643 | Depth-0 resets `_entry_committed_this_turn`; no-tool return is raw `content`; `all_failed+content` composes APP-024 only |
| Combat loop | `app/gm/orchestrator.py` `_combat_turn` L2262–2339, `_combat_llm_loop_inner` L2356–2452 | PC: tools → narrate call → raw return; monster: `_narrate_text`; **no compose** |
| Compose stub | `app/gm/orchestrator.py` `_compose_exploration_narration` L657–662 | APP-024 sanitizer only; no `strip_llm_status_tags`, no footer |
| Creation pattern | `app/gm/orchestrator.py` `_compose_creation_narration` L1183–1218 | Strip + body + `format_creation_status()` |
| Status strip | `app/gm/creation.py` `strip_llm_status_tags` L573–576, `_LLM_STATUS_TAG_RE` L115–118 | Bracket Location/Phase + any `Awaiting: TOKEN` |
| Creation footer | `app/gm/creation.py` `format_creation_status` L671–674 | Single `Awaiting: {label}` — exploration needs full bracket line |
| Footer reference | `app/gm/orchestrator.py` `_auto_finalize` L1992 | `[Location: … \| Phase: … \| HP: … \| Fortune: … \| GP: …]` + `Awaiting: RECEPTION_CHOICE` |
| Engine snapshot | `app/gm/bridge.py` `status()` L36–37 → `play/tomb_gm/cli/cmd_core.py` `handle_status` L84–226 | `party`, `roster[]`, `combat`, `awaiting` |
| LLM context (truth) | `app/gm/context.py` `build_state_context` L8–79 | Authoritative Location/Phase/Awaiting for prompt — separate from player footer |
| Prompt mandate | `app/gm/system_prompt.py` L207–213, L271–273 | "Include state line" + example bracket format |
| Drift (creation only) | `app/gm/orchestrator.py` `_check_creation_drift` L561–620 | Uses `parse_narration_status_line`; calls `log_creation_drift` |
| Drift parse | `app/gm/logger.py` `parse_narration_status_line` L72–84 | First `Phase:` / `Awaiting:` in full narration string |
| Emit | `app/gm/orchestrator.py` `_emit_narration` L646–648 | Logs + creation drift only |
| APP-024 gate | `app/gm/orchestrator.py` `sanitize_premature_site_entry_flavor` L159–171 | Line-level entry markers; compose order: **024 before 077** per domain spec |
| UI chips | `app/ui/suggestions.py`, `orchestrator.get_player_suggestions` L428–442 | Engine `awaiting` — not narration scrape (APP-065) |
| TTS (sibling) | `play/tomb_gm/services/tts/scene.py` | Bracket strip at speak time (APP-041); compose footer still authoritative for display |
| Tests (gap) | — | No `test_exploration_status_footer.py`; APP-024 tests hit compose stub without footer assertions |

## Code-path traces

### A — Exploration turn (happy path)

1. **Entry:** `process_turn` — not creation/combat; builds `state_context` from fresh `bridge.status()` (`orchestrator.py` L1135–1167).
2. **`_llm_loop(messages, depth=0)`** — LLM may return tool_calls + assistant `content` with embedded `[Location: … | … | Awaiting: …]`.
3. Tools execute; loop recurses until **no tool_calls** → returns raw `content` (L2557) — **no compose inside loop**.
4. **`process_turn` L1170–1172:** `gate_active = _exploration_gate_active(pre_turn_mode)`; `_compose_exploration_narration(narration, gate_active=gate_active)` — today only APP-024 strip/refusal.
5. **`_emit_narration(narration)`** — `log_gm_narration`; `_check_creation_drift` no-ops (not creation scope).
6. **Exit:** Full string (including LLM status line if model emitted one) → UI history + TTS.

**APP-077 target:** step 4 becomes sanitizer → `strip_llm_status_tags(prose)` → optional meta strip → append `format_exploration_status(self.bridge.status())` using **post-tool** status snapshot.

### B — Exploration `all_failed and content` (early return)

1. **`_llm_loop` L2615–2634:** Tools all failed but assistant had prose; builds `[Mechanics failed — …]` prefix.
2. **`_compose_exploration_narration(content, gate_active=…)`** — APP-024 only today.
3. Optional APP-022 delve hint inserted between prefix and safe content (L2632–2633).
4. Returns composed string **without** passing through `process_turn` compose again — compose must be **complete** inside helper (strip + footer).

### C — Combat PC turn

1. **Entry:** `_combat_turn` → `_combat_llm_loop` → `_combat_llm_loop_inner`.
2. Tool phase: `combat_action` only; on success, second LLM call (`context="combat_narrate"`, `tools=None`) L2444–2450.
3. **Return:** `final.get("content") or brief` — raw LLM text with prompt-mandated status line.
4. **`_combat_turn` L2334:** `_emit_narration(narration)` — **no `_compose_exploration_narration`**.
5. **`all_failed` combat path L2413–2427:** returns failure prefix only (strips assistant content) — no footer needed.

**APP-077 target:** compose before `_emit_narration` in `_combat_turn` (or at end of `_combat_llm_loop_inner` success path) with combat-aware footer (ticket: turn/actor from `status.combat`).

### D — Combat monster / aftermath narration

1. **`_narrate_text(prompt)`** L2217–2222 — `_narrate_only` with full `SYSTEM_PROMPT` (includes status-line mandate).
2. Used when combat ends or monsters act (`_combat_turn` L2299, L2332).
3. Same gap: no compose; LLM may emit bracket line.

### E — Creation pattern (template)

1. **`_compose_creation_narration(flavor, body[, footer])`** — `strip_llm_status_tags` + flavor strippers → body → `format_creation_status()` or explicit footer.
2. **`format_creation_status`** — code-owned **Awaiting only** (creation HUD uses Registry badge for step).
3. **`_auto_finalize`** — explicit bracket footer + `Awaiting: RECEPTION_CHOICE` passed as `footer=` (L1992–1993) — **shape reference** for `format_exploration_status`.

### F — `bridge.status()` fields for footer mapping

From `handle_status` (`cmd_core.py` L84–226):

| Footer token | Source (proposed) | Notes |
|--------------|-------------------|-------|
| `Location` | `party.display_address` or `party.address` | `display_address` set when `mode=dungeon` (site_id / room) |
| `Phase` | `party.phase` | e.g. `preparation`, `delve`, `ingress` |
| `HP` | `roster[0].hp` | String `"current/max"` already formatted |
| `Fortune` | `roster[0].fortune` | String `"current/max"` |
| `GP` | `roster[0].gold` and/or `party.gold_in_transit` | **PM decision:** ticket notes "GP in transit"; sheet has `goldGp` on roster entry |
| `Awaiting` | `status.awaiting` | `PLAYER_ACTIONS`, `COMBAT_TURN`, `DYING`, etc. |
| Combat extras | `combat.turn_id`, `combat.round`, `combat.turn_kind` | Ticket AC: combat subset when `combat` active |

Roster ordering: sorted by DB query; typically slot 1 first — spec should pin **lowest slot** or explicit slot-1 character.

## Existing specs & docs

- **Ticket:** `tmp/backlog/app-077-code-owned-exploration-status-footer.md` — AC for footer contract, compose helper, prompt change, tests, meta strip.
- **Domain spec:** `tmp/app-exploration-delve-spec.md` — APP-077 in open work; § APP-024 coordination defines compose order (024 → 077); no § code-owned footer yet.
- **Orchestrator spec:** `tmp/app-llm-orchestrator-spec.md` — lists APP-077 open; Phase 2 verify before `_compose_exploration_narration`; compose pattern cross-link required on close.
- **Closed patterns:** APP-007/073 (creation strip + footer), APP-024 (exploration compose entry point), APP-041 (TTS bracket strip — sibling, not substitute).
- **Related open:** APP-087 (sanitizer may leave LLM bracket — 077 fixes footer-only turns), APP-089/090 (verify gate runs before compose).

## Tests & commands

```bash
# Existing — no exploration footer coverage
python -m pytest app/tests/test_exploration_site_entry_gate.py -q
python -m pytest app/tests/test_exploration_set_phase_delve_hint.py -q
python -m pytest app/tests/test_creation_flavor_sanitize.py -q  # strip_llm_status_tags regressions

# After impl (ticket)
python -m pytest app/tests/test_exploration_status_footer.py -q
```

**Acceptance mapping (ticket → locus):**

| AC | Suggested locus |
|----|-----------------|
| `format_exploration_status` golden snapshot | New tests + `creation.py` or `orchestrator.py` helper |
| `_compose_exploration_narration` strip + single footer | Extend L657–662; call fresh `bridge.status()` |
| Meta leak strip (`Campaign Memory Updated`, `---` banners) | New regex helper alongside `strip_llm_status_tags` in `creation.py` |
| Empty body after strip still gets footer | Compose helper after APP-024 refusal branch |
| Wire `_llm_loop` terminal + `_combat_llm_loop_inner` success | `_combat_turn` before `_emit_narration`; exploration already calls compose in `process_turn` |
| Prompt: client appends state | `system_prompt.py` L213, L271–273 |
| Optional `log_exploration_drift` | `logger.py` + compare stripped tags vs engine in compose or `_emit_narration` exploration branch |
| Wrong GP integration test | Mock LLM bracket with bad GP; assert footer shows engine `roster[0].gold` |

## Risks & unknowns

- **GP field ambiguity:** `roster[].gold` (sheet `goldGp`) vs `party.gold_in_transit` — ticket footer shows `{gold}`; PM must document which (or both) in spec.
- **Multi-PC roster:** Footer uses slot-1 summary today per ticket notes; multi-delver parties may need aggregated HP or active PC — out of scope unless spec expands.
- **Compose call sites:** Combat has 3+ narration exits in `_combat_turn` (death, end, PC, monster); missing one leaves raw LLM status on that path.
- **Double compose:** `process_turn` composes after `_llm_loop`; `all_failed` composes inside loop — helper must be idempotent (strip own footer if re-run) or call compose only once per path.
- **APP-024 refusal line:** Ticket: still append footer when body empty unless refusal — refusal line is code-owned prose; footer should follow refusal.
- **APP-087 footer-only turns:** After aggressive sanitizer strip, LLM bracket may remain; APP-077 strip + code footer eliminates bracket-only player view.
- **Meta leak patterns:** `Campaign Memory Updated` not found in repo — LLM invention; regex list may grow (coordinate APP-088 remember_fact timing separately).
- **Strip gaps:** `_LLM_STATUS_TAG_RE` does not remove unbracketed `Location: … \| Phase: …` lines or `[HP: …]`-only brackets — verify against session samples; may need broader bracket regex (`\[[^\]]*(?:Location\|Phase\|HP\|Fortune\|GP\|Awaiting)[^\]]*\]`) if models diverge from prompt shape.
- **APP-083 ordering:** Orchestrator spec says verify before compose for exploration Phase 2 — APP-077 can land first as strip/footer; verify gate is independent but compose order must stay **verify pass → compose (024+077)** when APP-089 wires in.
- **Session evidence unverified:** Ticket cites `app/logs/session-2026-05-22.jsonl` (not in workspace); human playtest should confirm wrong GP and meta leak.
- **TTS:** Code footer will appear in narration panel; APP-041 TTS strip may still remove bracket footer at speak time — confirm product intent (status visible but not spoken vs spoken).

## Raw notes

### `_compose_exploration_narration` (live — APP-077 not landed)

```657:662:app/gm/orchestrator.py
    def _compose_exploration_narration(self, prose: str, *, gate_active: bool) -> str:
        """Exploration post-process: APP-024 site-entry strip, then APP-077 footer/tags."""
        text = sanitize_premature_site_entry_flavor(prose or "", gate_active=gate_active)
        if gate_active and not text.strip():
            text = _SITE_ENTRY_REFUSAL_LINE
        return text
```

### `_LLM_STATUS_TAG_RE` (APP-073 — reusable)

```115:118:app/gm/creation.py
_LLM_STATUS_TAG_RE = re.compile(
    r"\[Location:[^\]]*\]|\[Phase:[^\]]*\]|Awaiting:\s*[A-Z0-9_]+",
    re.I | re.MULTILINE,
)
```

### `system_prompt.py` mandate

```207:213:app/gm/system_prompt.py
## HOW YOU WORK EACH TURN (MANDATORY)
...
6. Include state line: [Location: ADDR | Phase: PHASE | HP: X/Y | Fortune: N/M | Awaiting: NEXT]
```

### `handle_status` roster shape

```160:167:play/tomb_gm/cli/cmd_core.py
        payload["roster"].append(
            {
                ...
                "hp": f"{hp.get('current', '?')}/{hp.get('max', '?')}",
                "fortune": f"{fortune.get('current', 0)}/{fortune.get('max', 1)}",
                "gold": sheet.get("goldGp", 0),
```

### `_check_creation_drift` scope gate

```561:563:app/gm/orchestrator.py
    def _check_creation_drift(self, narration: str) -> None:
        if not self._creation_drift_scope():
            return
```

Exploration narration never triggers drift logging today.

### Compose order (domain spec APP-024 §)

1. `sanitize_premature_site_entry_flavor` (APP-024)  
2. `strip_llm_status_tags` + `format_exploration_status` (APP-077)  
3. Emit via `_emit_narration`

Failed `set_phase(delve)` path (APP-022): `[Mechanics failed]` → hint → sanitized content → exploration footer.

### Chips (APP-065 — not narration-driven)

`get_player_suggestions()` reads `bridge.status().awaiting` and `creation.step` — stale `Awaiting:` in flavor no longer drives chips, but player still **reads** wrong bracket line in narration panel.

### No `format_exploration_status` / `log_exploration_drift`

Grep confirms absent; `log_creation_drift` exists as template (`logger.py` L52–54).
