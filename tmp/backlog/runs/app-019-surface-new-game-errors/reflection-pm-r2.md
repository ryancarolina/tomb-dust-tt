# Reflection: PM — APP-019 surface-new-game-errors

**Agent:** PM
**Round:** 2
**Deliverables:** `spec.md` (r2), `tmp/app-session-persistence-spec.md` (§ Emit ownership), `reflection-pm-r2.md`

## Completed

- **SPEC-001 (blocker):** Added R1a/R1b emit ownership. Contexts A/C emit inline in `process_turn` (single owner). Context B requires `_handle_player_death` to `_emit_recovery_narration` on setup failure and return an `already_emitted` signal; both combat call sites (~1586, ~1680) MUST skip `_emit_narration` when set. Documented forbidden double-emit and `_emit_narration`-on-failure patterns.
- **SPEC-002:** T-019c now specifies direct `_handle_player_death` + monkeypatch (no full combat integration); asserts single `log_gm_narration`. T-019d gains dual JSONL asserts. T-019e covers context B drift silence.
- **SPEC-003:** Removed stale “extend Expected files before impl” note (ticket already lists orchestrator + tests). Aligned domain cause-line strings to run spec R5 table.

## Self-critique

- Chose `(message, already_emitted)` tuple contract over mandating a named dataclass — Dev may use equivalent signal; behavior (one JSONL, no caller re-emit on failure) is the hard requirement.
- Did not pin exact return type name in domain spec — run spec R1b is authoritative; domain § Emit ownership summarizes for drift checks.
- Success-path death still uses caller `_emit_narration`; if Dev consolidates all death emit inside handler, must preserve drift check on success desk copy only.

## Did I miss anything?

- [x] QA SPEC-001 / SPEC-002 / SPEC-003
- [x] Domain spec sync — emit ownership + cause lines + tests
- [x] Ticket Expected files — unchanged (already correct)
- [ ] Optional R6 sentinel string pin — deferred; QA noted as non-blocking

## Handoff

**Ready for:** QA spec review round 2 (adversarial PASS/FAIL on R1b + T-019c)
**Escalate human if:** Dev prefers moving all death emit into handler (success + failure) — acceptable if combat callers stop calling `_emit_narration` entirely and success drift behavior is preserved
