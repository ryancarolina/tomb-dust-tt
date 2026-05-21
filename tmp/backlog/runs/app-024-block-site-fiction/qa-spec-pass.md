# QA PASS: spec

**Task:** app-024-block-site-fiction  
**backlog_ticket:** APP-024  
**ticket_path:** [tmp/backlog/app-024-block-site-fiction-without-enter-tool.md](../../app-024-block-site-fiction-without-enter-tool.md)  
**Round:** 2  
**domain_spec_creation:** not_needed (registry_gap false; exploration owner updated)  
**Reviewer role:** QA (adversarial)

**Verdict:** PASS

## Gates

| Gate | Result | Evidence |
|------|--------|----------|
| Ticket valid (`in_progress`) | PASS | `tmp/backlog/app-024-block-site-fiction-without-enter-tool.md` |
| `registry_gap: false` | PASS | `research-brief.md`; owner `tmp/app-exploration-delve-spec.md` § Site-entry fiction gate |
| Domain spec matches run spec | PASS | Normative §§ at domain L26–86; run `spec.md` E1–E9 align |
| AC testable | PASS | Seven pytest cases + commands; ticket AC ↔ spec § Acceptance criteria mapping |
| Code traces | PASS | Live read `orchestrator.py` L1978 overwrite, L1999–2006 `all_failed and content` — matches E1 rationale |
| Affected paths ⊆ Expected files | PASS | Ticket L23–24: `orchestrator.py`, `test_exploration_site_entry_gate.py` |
| AGENTS.md drift policy | PASS | Behavior in domain spec + run spec; changelog draft entries present |

## Round 1 remediation verified

| Finding | r1 severity | r2 status | Evidence |
|---------|-------------|-----------|----------|
| SPEC-001 — `_last_tool_results` final slot vs chain success | blocker | **Fixed** | Run `spec.md` E1 L42: sticky `entry_committed_this_turn`; explicit forbid dict-only inference; domain L40, L58–60 wiring |
| TICKET-001 — AC said "last tool" | blocker | **Fixed** | Ticket AC L18–19: "current turn's tool chain"; second AC for sticky commit / no revoke on later failures |
| SCOPE-001 — test file missing from Expected files | non-blocker | **Fixed** | Ticket L24; run spec Affected paths L104 |

## AC coverage (ticket → spec → domain)

| Ticket AC | spec.md | Domain spec |
|-----------|---------|-------------|
| Block site-entry fiction unless turn chain includes successful `enter_dungeon` / `site_enter` | E1–E6; § Entry commit vs engine mode L52–56 | § When the gate runs L34–38; § Wiring L58–60 |
| Entry commit not revoked by later failed retry / other failed tools | E1 sticky flag; `test_success_then_failed_enter_dungeon_retains_fiction` L93 | § Entry committed L40; test row L83 |
| In-dungeon / in-site interior narration unchanged | E3; `test_site_entry_gate_bypass_when_in_dungeon` | Gate bypass row L37; test row L85 |
| Spec sync on close | § Acceptance criteria mapping L68–74 | Checklist L120; changelog L160–161 |

## Adversarial notes (non-blocking)

1. **NOTE-001** — `tmp/app-llm-orchestrator-spec.md` still lacks APP-024 checklist cross-link; mechanical truth at L13–15 is consistent. Defer to ticket close per PM r2.
2. **NOTE-002** — Refusal line copy still "exact copy at implementation" (domain L54; E6). Dev plan should pin string before impl QA (APP-070 pattern).
3. **`mode=preparation`** — Gate table covers surface / dungeon / site only; hub/preparation entry edge not specified. Acceptable if product treats preparation as surface-equivalent at compose time — Dev plan should state mode snapshot used for `gate_active`.
4. **Sanitizer patterns** — E4 / domain § Sanitizer contract describe intent, not regex fixtures; `test_sanitize_premature_site_entry_flavor_unit` covers helper — Dev must define markers in impl.

## Summary

Round 1 blockers resolved: E1 now mandates sticky per-turn commit tracking (or full-chain scan) and explicitly rejects final `_last_tool_results[tool_name]` alone; ticket AC matches clarified semantics; test module is on Expected files. Domain spec, run spec, and ticket are aligned and implementation-ready for Dev plan.

## Re-review focus

_None required unless PM revises E1 signal, gate mode table, or ticket AC again._
