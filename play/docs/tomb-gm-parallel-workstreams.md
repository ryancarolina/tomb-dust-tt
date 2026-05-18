# Tomb Dust AI GM — parallel workstreams

**Normative detail:** [tomb-gm-implementation-spec.md](tomb-gm-implementation-spec.md)

## Execution waves

| Wave | Streams | Can run in parallel |
|------|---------|---------------------|
| **0** | WS-0 Foundation | Solo (blocks all) |
| **1** | WS-1 … WS-7, WS-10 | Yes — disjoint `play/tomb_gm/` subtrees |
| **2** | WS-8 Beat | After WS-1,2,3,6,7 register handlers |
| **3** | WS-9 TTS | Anytime after WS-0; integrate `speak` in wave 2 |

## Workstreams (file ownership)

| ID | Name | Owns | CLI commands |
|----|------|------|--------------|
| **WS-0** | Foundation | `db/`, `cli/parser.py`, `cli/output.py`, `__main__.py`, `check.py`, `suggest.py`, `tests/test_foundation.py` | `init`, `status`, `check`, `suggest` |
| **WS-1** | Campaign & session | `domain/campaign.py`, `domain/session.py`, `cli/cmd_campaign.py`, `cli/cmd_session.py` | `campaign *`, `session *` |
| **WS-2** | World & content | `services/content.py`, `services/world.py`, `cli/cmd_world.py`, `cli/cmd_content.py` | `world *`, `content cell` |
| **WS-3** | Memory | `services/memory/`, `cli/cmd_memory.py` | `memory *` |
| **WS-4** | Characters | `domain/character.py`, `cli/cmd_character.py`, `cli/cmd_roster.py` | `character *`, `roster *` |
| **WS-5** | RAG | `services/rag/`, `cli/cmd_rules.py` | `rules search`, extended `content *` |
| **WS-6** | Simulation | `rules/bridge.py`, `services/simulation/`, `cli/cmd_roll.py`, `cli/cmd_combat.py` | `roll *`, `combat *` |
| **WS-7** | Sites & extraction | `domain/clock.py`, `domain/stamp.py`, `services/site.py`, `services/extraction.py`, `cli/cmd_site.py`, `cli/cmd_phase.py` | `site *`, `phase *`, `clock *`, `registry *` |
| **WS-8** | Beat | `services/beat.py`, `cli/cmd_beat.py` | `beat` |
| **WS-9** | TTS | `services/tts/`, `cli/cmd_speak.py` | `speak` |
| **WS-10** | Cursor | `.cursor/hooks/tomb_gm_*.py`, `.cursor/rules/tomb-gm-active.mdc`, `hooks.json` | — |

**Do not edit** another stream's files. Register CLI via `register(subparsers)` in your `cli/cmd_*.py`.

## Integration contract

```python
# cli/cmd_example.py
def register(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("example", help="...")
    p.set_defaults(handler=handle_example)

def handle_example(args, ctx: CommandContext) -> dict:
    return {"ok": True, ...}
```

`CommandContext` provides: `config: GameplayConfig`, `conn: sqlite3.Connection`.

## Merge order (if conflicts)

WS-0 → WS-1,2,3,4,5,6,7,10 (any) → WS-8 → WS-9

## Current run (2026-05-18)

| Stream | Status |
|--------|--------|
| **WS-0** Foundation | **Done** — `init`, `status`, `check`, `suggest`, DB schema |
| **WS-1** Campaign/session | **Done** |
| **WS-2** World/content | **Done** |
| **WS-3** Memory | **Done** |
| **WS-4** Characters/roster | **Done** |
| **WS-5** RAG | **Done** |
| **WS-6** Rolls/combat | **Done** |
| **WS-7** Sites/extraction | **Done** |
| **WS-8** Beat | **Done** — `beat`, session end → `memory compact` |
| **WS-9** TTS | **Done** — `speak --text`, `--beat-id`, `--stop` (needs `pip install edge-tts`) |
| **WS-10** Cursor hooks | **Done** |

**CLI from repo:** `cd play` then `python -m tomb_gm --workspace workspace init`

---

## Verification (each stream)

```powershell
python -m pytest play/tomb_gm/tests -q
python -m tomb_gm --workspace play/workspace init
python -m tomb_gm --workspace play/workspace check
```
