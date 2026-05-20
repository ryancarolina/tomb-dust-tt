# QA PASS: plan — round 1

**Task:** app-076-swap-default-llm-to-haiku-4-5  
**backlog_ticket:** APP-076  
**ticket_path:** [tmp/backlog/app-076-swap-default-llm-to-haiku-4-5.md](../../app-076-swap-default-llm-to-haiku-4-5.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (spec QA confirmed `registry_gap: false`)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec `tmp/app-shell-config-spec.md`
- [x] Acceptance criteria testable (config string, spec table/changelog, manual smoke, JSONL grep)
- [x] Plan files ⊆ ticket **Expected files** (strict equality — two files only)
- [x] Code traces match repo (spot-checked; line refs accurate)
- [x] AGENTS.md / canon compliance (config + spec sync only; no `build/` or orchestrator logic drift)
- [x] Verification commands listed (import smoke, `Select-String` / grep, manual smoke, JSONL grep)
- [x] Non-goals / out-of-scope explicit (orchestrator fallback, tuning, per-mode routing, new pytest, `app-master-spec.md`)
- [x] R1–R4 / ticket AC mapped in plan § AC mapping

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/config.yaml` — L3 `llm.model` only | Yes |
| `tmp/app-shell-config-spec.md` — L23 shipped-default table row | Yes |
| `tmp/app-shell-config-spec.md` — changelog append APP-076 | Yes |

**Read-only (no edits):** `app/main.py`, `app/gm/orchestrator.py`, `app/gm/openrouter.py`, `app/gm/logger.py`, `app/ui/app.py`, `tmp/app-master-spec.md`, `app/tests/*` — all explicitly out of scope.

## Code trace audit

Independent spot-check against live repo (pre-impl state):

| Symbol / flow | File | Present | Plan ref |
|---------------|------|---------|----------|
| Shipped default still Flash Lite | `app/config.yaml` L3 | Yes (`google/gemini-3.1-flash-lite`) | §1 before |
| Spec table drift (pre-impl) | `tmp/app-shell-config-spec.md` L23 | Yes (Flash Lite) | §2a before |
| `self.model` from config; Sonnet fallback | `app/gm/orchestrator.py` L90 | Yes | Preserve |
| Status bar `Model:` from config | `app/ui/app.py` L246–247 | Yes | Verification manual |
| `log_llm_request(..., model, ...)` | `app/gm/orchestrator.py` L723+ | Yes | JSONL AC |
| APP-046 changelog row at L78 | `tmp/app-shell-config-spec.md` L78 | Yes | §2b append after |

Plan correctly preserves code fallback `anthropic/claude-sonnet-4` and does not touch L37 fallback paragraph.

## Ticket AC → plan / verification

| Ticket AC | Plan coverage | Test / mechanism |
|-----------|---------------|------------------|
| `config.yaml` → `anthropic/claude-haiku-4.5` | §1 L3 before/after | `Select-String` / grep on `config.yaml` |
| Spec table + changelog, no drift | §2a L23, §2b append | Visual diff; table matches config |
| Manual smoke: new game → creation tool step → exploration turn | § Verification manual | Human with `OPENROUTER_API_KEY` |
| JSONL shows new model id | § Verification grep | `Select-String` on `logs/session-*.jsonl` |

### Spec R1–R4 map

| ID | Plan locus | Verification |
|----|------------|--------------|
| R1 | `app/config.yaml` L3 | Automated grep |
| R2 | spec table L23 + changelog | File diff on close |
| R3 | Manual smoke steps 1–4 | Human playtest |
| R4 | JSONL `"model"` field | Post-smoke grep |

## qa-spec-pass adversarial notes — plan resolution

| Spec QA note | Plan handling |
|--------------|---------------|
| OpenRouter model id not catalog-verified | § Risk / escalation — smoke surfaces invalid id |
| Manual + JSONL AC human-gated | § Verification + Risk (no API key → document in `status.md`) |
| Windows grep alternative | PowerShell `Select-String` in verification block |
| R3 exploration step slightly soft | Manual step 3 + status bar check — human-testable |
| No `app-master-spec.md` update | Explicit in § Ticket close and out-of-scope |
| Pre-impl drift expected | Plan before/after matches live L3 + L23 |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-076 `in_progress`; domain spec aligned |
| Plan ⊆ Expected files | **PASS** | Two files; strict equality; no scope creep |
| Code traces | **PASS** | Config → orchestrator → API/log/UI path unchanged |
| AC testability | **PASS** | All four ticket AC mapped |
| Spec drift closure | **PASS** | Table + changelog; APP-046 row preserved as history |
| Over-engineering | **PASS** | Config-only; no Python edits |

## Notes (non-blocking — impl QA)

1. **OpenRouter model id** — `anthropic/claude-haiku-4.5` not verified against live catalog; manual smoke is the gate. Revert L3 if API returns model-not-found.
2. **JSONL AC requires API key** — Import smoke alone cannot close R4; impl must run manual smoke or document blocker in run `status.md`.
3. **Status bar check** — Not a ticket AC row but in spec human hints; plan includes it in manual step 4 — good extra signal, no extra file edits.
4. **Changelog wording** — Plan uses full APP-076 rationale string; AC only requires dated APP-076 reference — acceptable superset.
5. **APP-031/032 escalation** — Plan correctly defers transcript 400 fixes; only escalate if smoke cannot complete creation tool step.

**Verdict:** PASS — ready for implementation.
