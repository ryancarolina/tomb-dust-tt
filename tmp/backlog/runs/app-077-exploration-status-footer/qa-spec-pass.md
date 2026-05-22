# QA PASS: spec — round 1

**Task:** app-077-exploration-status-footer  
**backlog_ticket:** APP-077  
**ticket_path:** [tmp/backlog/app-077-code-owned-exploration-status-footer.md](../../app-077-code-owned-exploration-status-footer.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (registry_gap false; exploration owner + orchestrator cross-link updated)  
**Reviewer role:** QA (adversarial)

**Verdict:** PASS

## Gates

| Gate | Result | Evidence |
|------|--------|----------|
| Ticket valid (`in_progress`) | PASS | `tmp/backlog/app-077-code-owned-exploration-status-footer.md` |
| `registry_gap: false` | PASS | `research-brief.md` L13–15; owner `tmp/app-exploration-delve-spec.md` § Code-owned status footer (APP-077) |
| Domain spec matches run spec | PASS | Normative § at domain L339–427; run `spec.md` F1–F12 align field mapping, compose order, combat wire |
| Orchestrator cross-link | PASS | `tmp/app-llm-orchestrator-spec.md` § Code-owned exploration/combat status footer (APP-077) L594–657 |
| AC testable | PASS | Nine pytest cases + regression commands; ticket AC ↔ spec § Acceptance criteria mapping L84–97 |
| Code traces | PASS | Live read: `_compose_exploration_narration` stub L657–662 (APP-024 only); `process_turn` L1170–1172 double-compose path; `_combat_turn` L2334 emit without compose; `system_prompt.py` L213 mandate — match research + F9 |
| Affected paths ⊆ Expected files | PASS | Ticket L55–62; run spec § Expected files L124–132 |
| AGENTS.md drift policy | PASS | Behavior in domain + orchestrator specs; changelog draft entries present |
| TurnTruth / APP-083 ordering | PASS | verify pass → compose (024 + 077); strip/footer defense-in-depth — run spec L66–67, domain L306–307 / L410, orchestrator L622; F12 doc-only rule consistent with Phase 2 future wire |

## AC coverage (ticket → spec → domain)

| Ticket AC | spec.md | Domain spec |
|-----------|---------|-------------|
| Exploration footer contract documented | F1–F2; § Footer shape L68–80 | § Footer contract L347–373 |
| Combat footer when `combat.active` | F3 | § Combat shape L367–371 (`status.combat` truthy) |
| `format_exploration_status` golden snapshot | F1; `test_format_exploration_status_golden` L111 | § Tests L418–421 |
| `_compose_exploration_narration` strip + single footer | F6–F8 | § Helpers + Compose order L375–395 |
| Meta leak strip (`Campaign Memory Updated`) | F5; test L115 | § Helpers L381; test row L423 |
| Empty body still gets footer | F7; test L117 | § Empty body L393 |
| Wire `_llm_loop` + combat success paths | F9; tests L119–120 | § Wiring L397–404 |
| Prompt: client appends state | F10 | § Prompt L406; orchestrator § system_prompt L630–636 |
| Optional `log_exploration_drift` | F11 | § Optional telemetry L408 |
| Wrong GP integration test | `test_compose_exploration_single_footer` L116 | § Strip + compose test row L422 |

## TurnTruth / APP-083 ordering (explicit)

| Layer | Order | Spec source |
|-------|-------|---------------|
| APP-083 Phase 2+ (future) | `build_exploration_turn_truth` → LLM → `verify_narration` pass → **then** compose | orchestrator spec L133–134, L622; domain APP-089 L299–306 |
| APP-077 (this ticket) | Compose pipeline independent; ships before Phase 2 verify | run spec § Non-goals L30; F12 defense-in-depth |
| APP-089 encounter | verify pass → `_compose_exploration_narration` (024 + 077) | domain L306–307; run spec L66 |
| APP-090 combat | verify per phase → compose → emit; encounter verify **must not** run in combat loop | orchestrator spec L153 |
| Creation (reference) | verify → `_compose_creation_narration` | orchestrator spec L132 |

No contradiction: APP-077 does not wire verify; it documents compose **after** verify when Phase 2 lands. Strip/footer remain post-verify defense-in-depth per `tomb-dust-turn-truth-verify.mdc`.

## Adversarial notes (non-blocking)

1. **TICKET-001 — AC signature drift** — Ticket AC lists `_compose_exploration_narration(prose: str, status: dict)`; run spec F6 uses `(prose, *, gate_active: bool)` and fresh `self.bridge.status()` at append time (matches live orchestrator pattern). Dev plan should follow run/domain spec; PM may align ticket AC on close.
2. **SPEC-001 — F3 `Turn` fallback** — Run spec F3 allows fallback `combat.get("actor")`; `bridge.status()["combat"]` payload (`cmd_core.py` L211–218) exposes `turn_id`, not `actor`. Domain spec pins `turn_id` only. Dev should use `turn_id` with `"?"` fallback — drop `actor` or document mapping from `combatants`.
3. **SPEC-002 — Empty roster** — F2 pins lowest-`slot` roster entry for HP/Fortune/GP but does not define behavior when `roster` is empty (exploration edge). Dev plan should specify placeholder or skip footer fields — unlikely in normal play.
4. **SPEC-003 — Double-compose is mandatory** — `all_failed and content` composes inside `_llm_loop` (L2630) and `process_turn` composes again (L1172). F8 idempotency is **required**, not optional; `test_compose_idempotent_double_call` must gate impl.
5. **NOTE-001 — Research brief stale** — `research-brief.md` L111 says domain lacks APP-077 §; domain spec now has full § (L339+). Harmless; research predates PM domain sync.
6. **NOTE-002 — Ticket combat trigger wording** — Ticket AC says `combat.active`; spec/domain use `status.get("combat")` truthy from `bridge.status()`. Correct for compose-time snapshot; align ticket wording on close.
7. **NOTE-003 — Pre-existing combat emit gap** — `_combat_turn` L2287 returns `_narrate_text` without `_emit_narration` (early combat-end during pending_start). Out of APP-077 scope; F9 targets paths that call `_emit_narration`. Do not expand ticket unless human playtest flags silent turn.
8. **NOTE-004 — `strip_llm_status_tags` broadening** — F4 extends shared helper used by creation compose. Regression suite includes `test_creation_flavor_sanitize.py -k status` (spec L105) — Dev must run before close.

## Summary

Run `spec.md`, domain § Code-owned status footer (APP-077), and orchestrator cross-link fully cover ticket scope: footer field mapping, meta strip, compose order with APP-024/022/028 prefix paths, combat wire, prompt policy, idempotent double-compose, and test matrix. TurnTruth ordering is consistent — APP-077 compose is post-verify when APP-083 Phase 2 wires; strip/footer stay defense-in-depth. No registry gap. Spec is implementation-ready for Dev plan with minor ticket AC cleanup deferred to close.

## Re-review focus

_None required unless PM revises F3 Turn fallback, F6 signature, F8 idempotency contract, or ticket AC rows._
