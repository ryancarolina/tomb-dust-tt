# Reflection: PM — APP-016 round 2

**Agent:** PM  
**Round:** 2 (QA spec report 1 remediation)  
**Deliverables:** `spec.md`, `tmp/app-session-persistence-spec.md`, `tmp/backlog/app-016-snapshot-engine-status-on-save.md`, `reflection-pm-r2.md`

## QA findings addressed

| ID | Fix |
|----|-----|
| **SPEC-001** | Added full § **Engine status snapshot on save (APP-016)** with S1/S5 write rules, batch table, Consumers, AC; updated top persist bullet |
| **SPEC-002** | Resolved batch conflict: **APP-015** C2 removes `engine_status` on every `setup_new_game` entry; **APP-016** write-only on save. Updated APP-015 C2/C4, batch tables, run spec R3, test **T-015d** |
| **SPEC-003** | § Consumers documents APP-017 / APP-018 read paths; forward Notes on those tickets |
| **TICKET-001** | Expected files → `app/ui/app.py`, `app/tests/`, `tmp/app-session-persistence-spec.md`; orchestrator scoped to APP-015 batch note |

## Batch decision (SPEC-002)

Chose **option A** (APP-015 owns stale clear): surgical C2 must not preserve pre-wipe `engine_status`. APP-014 L7 whole-file delete on success remains sufficient for happy path; C2 covers failure/early-return paths where file survives.

## Canonical shapes

- Save failure: **omit** `engine_status` key (S5d preferred).
- Load/reconcile: absent key and `null` both mean “no snapshot”.
- New game entry: APP-015 removes key or sets `null` until next save.

## Self-critique

- APP-015 run `spec.md` not edited in this pass — domain spec is authoritative; APP-015 PM should align C2 wording on next touch (T-015d now in domain).
- APP-017/018 ticket Notes are pointers only — no AC change until those PM lanes.

## Handoff

**Ready for:** QA spec re-review (round 2) on domain § APP-016 + ticket Expected files + APP-015/016 batch consistency.

**Escalate human if:** batch wants APP-016 implemented before APP-015 — implementers must still follow C2/T-015d for stale snapshot safety.
