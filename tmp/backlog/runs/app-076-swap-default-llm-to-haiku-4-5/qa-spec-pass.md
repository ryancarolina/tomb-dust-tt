# QA PASS: spec — round 1

**Task:** app-076-swap-default-llm-to-haiku-4-5  
**backlog_ticket:** APP-076  
**ticket_path:** [tmp/backlog/app-076-swap-default-llm-to-haiku-4-5.md](../../app-076-swap-default-llm-to-haiku-4-5.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (registry_gap false; existing shell spec owner updated on close)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec `tmp/app-shell-config-spec.md`
- [x] Acceptance criteria complete and testable (file diff, spec table/changelog, manual smoke, JSONL grep)
- [x] Scope limited to ticket **Expected files** only (`app/config.yaml`, `tmp/app-shell-config-spec.md`); read-only refs explicitly excluded
- [x] `registry_gap: false` — shell spec owns `config.yaml` + shipped-default table; no new domain spec
- [x] Code traces match repo (live read: `config.yaml` still Flash Lite; `Orchestrator` `self.model` from config; Sonnet fallback unchanged; `log_llm_request` → `data.model`; UI `Model:` from `config["llm"]["model"]`)
- [x] Non-goals / out-of-scope aligned with ticket Notes (no orchestrator fallback change, no per-mode routing, no tuning unless smoke fails)
- [x] AGENTS.md compliance — config + spec sync only; no canon/mechanics drift
- [x] Every ticket AC row mapped in `spec.md` R1–R4

## AC coverage (ticket → spec → domain)

| Ticket AC | spec.md | Domain spec (on close) |
|-----------|---------|------------------------|
| `config.yaml` → `anthropic/claude-haiku-4.5` | R1 | § Shipped default table `llm.model` row |
| Spec + changelog, no drift | R2 | Changelog + table sync (APP-046 row updated) |
| Manual smoke: new game → creation tool step → exploration turn | R3 | § Tests manual row (implicit via smoke) |
| JSONL shows new model id | R4 | — (logging owned elsewhere; AC verified via grep) |

## registry_gap / domain_spec_creation

- **registry_gap:** false — justified in research-brief; `tmp/app-shell-config-spec.md` registered owner for `app/config.yaml` and `main.py`.
- **domain_spec_creation:** not_needed — Dev updates existing shell spec table + changelog per R2; no `app-master-spec.md` registry row change (default string only, no cross-domain behavior).

## Out of scope (confirmed)

| Item | Where documented |
|------|------------------|
| Per-mode model routing | Ticket Notes; spec § Non-goals |
| Change `Orchestrator` code fallback (`anthropic/claude-sonnet-4`) | Ticket Notes; R2 explicit preserve |
| `max_tokens` / `temperature` tuning | Ticket Notes; R1 leave unchanged |
| OpenRouter / UI / logger code edits | spec § Non-goals; read-only refs only |
| APP-031/032 transcript fixes | Soft dependency; smoke escalation only |

## Adversarial notes (non-blocking)

1. **OpenRouter model id** — `anthropic/claude-haiku-4.5` not verified against live OpenRouter catalog; invalid id surfaces at smoke/API error. Acceptable for config-only ticket.
2. **Manual + JSONL AC** — Human-gated; no automated pytest for model string. Import smoke (`python -c "import main"`) is sufficient for CI; impl QA must run grep on latest `app/logs/session-YYYY-MM-DD.jsonl` after smoke.
3. **Test plan `grep`** — Examples assume Unix `grep`; on Windows Dev may use `rg` or `Select-String` — same intent.
4. **R3 exploration step** — “or earliest post-creation GM turn” is slightly soft; still human-testable; Stage 7 playtest can nail one concrete path.
5. **`app-master-spec.md`** — Ticket template mentions update if cross-domain behavior changes; not required here (shipped default only).
6. **Current drift (expected pre-impl)** — `app/config.yaml` and domain spec table still show `google/gemini-3.1-flash-lite`; R1/R2 close this on implement.

## Summary

`spec.md` fully covers a two-file config default swap with clear requirements, test plan, human hints, and explicit non-goals. Ticket AC maps 1:1 to R1–R4. Scope is tight; registry_gap handling is correct. **PASS** — ready for Dev plan + implement.

## Re-review focus

_None required for round 2 unless PM expands scope (orchestrator fallback, tuning, or new expected files)._
