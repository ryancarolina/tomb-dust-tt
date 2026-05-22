import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

path = Path(r"c:\Users\PC\Desktop\development\ttTomb-Dust\app\logs\session-2026-05-20.jsonl")
events = []
with path.open(encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as ex:
            print(f"JSON error line {i}: {ex}")

print(f"Total events: {len(events)}")
if not events:
    raise SystemExit(0)

types = Counter(e["type"] for e in events)
print("\nEvent types:")
for t, c in types.most_common():
    print(f"  {t}: {c}")

ts0 = datetime.fromisoformat(events[0]["ts"])
ts1 = datetime.fromisoformat(events[-1]["ts"])
print(f"\nSession span: {ts0} -> {ts1} ({ts1 - ts0})")

models = Counter(e["data"].get("model") for e in events if e["type"] == "llm_request")
print("\nLLM models:")
for m, c in models.most_common():
    print(f"  {m}: {c} requests")

pending = []
lat = []
finish = Counter()
for e in events:
    if e["type"] == "llm_request":
        pending.append(datetime.fromisoformat(e["ts"]))
    elif e["type"] == "llm_response":
        if pending:
            t0 = pending.pop(0)
            t1 = datetime.fromisoformat(e["ts"])
            lat.append((t1 - t0).total_seconds())
        finish[e["data"].get("finish_reason", "?")] += 1

if lat:
    lat.sort()
    print(
        f"\nLLM latency (n={len(lat)}): min={lat[0]:.2f}s "
        f"med={lat[len(lat) // 2]:.2f}s max={lat[-1]:.2f}s avg={sum(lat) / len(lat):.2f}s"
    )
print("Finish reasons:", dict(finish))

tools = Counter()
tool_fail = []
for e in events:
    if e["type"] == "tool_call":
        name = e["data"]["name"]
        tools[name] += 1
        res = e["data"].get("result", {})
        if isinstance(res, dict) and res.get("ok") is False:
            tool_fail.append((e["ts"], name, res))
print("\nTool calls:")
for t, c in tools.most_common():
    print(f"  {t}: {c}")
print(f"Tool failures: {len(tool_fail)}")
for ts, name, res in tool_fail[:10]:
    err = res.get("error", res)
    print(f"  {ts} {name}: {err}")

inputs = [e["data"]["text"] for e in events if e["type"] == "player_input"]
print(f"\nPlayer inputs: {len(inputs)}")
print("First 5:", inputs[:5])
print("Last 5:", inputs[-5:])
new_games = sum(1 for t in inputs if t.strip().lower() == "new game")
print(f"New game commands: {new_games}")

error_types = [
    e
    for e in events
    if "error" in e["type"].lower() or "fail" in e["type"].lower() or "drift" in e["type"].lower()
]
print(f"\nError/drift event types: {len(error_types)}")
for t, c in Counter(e["type"] for e in error_types).most_common(20):
    print(f"  {t}: {c}")

issues = []
for e in events:
    data = e.get("data", {})
    if not isinstance(data, dict):
        continue
    if data.get("ok") is False:
        issues.append((e["ts"], e["type"], data))
    if data.get("error"):
        issues.append((e["ts"], e["type"], data.get("error")))
    if data.get("character_create_error"):
        issues.append((e["ts"], e["type"], data["character_create_error"]))
print(f"\nok:false / error field events: {len(issues)}")
for item in issues[:15]:
    print(" ", item)

trunc = [
    e for e in events if e["type"] == "llm_response" and e["data"].get("finish_reason") == "length"
]
print(f"\nTruncated LLM responses (finish_reason=length): {len(trunc)}")

depths = Counter(e["data"].get("depth", 0) for e in events if e["type"] == "llm_request")
print("LLM request depths:", dict(depths))

awaiting_tags = Counter()
for e in events:
    if e["type"] == "gm_narration":
        text = e["data"].get("text", "")
        for m in re.findall(r"Awaiting:\s*(\S+)", text):
            awaiting_tags[m] += 1
        if re.search(r"\[Location:", text):
            awaiting_tags["[Location tag]"] += 1
print("\nAwaiting tags in narration (top):")
for t, c in awaiting_tags.most_common(15):
    print(f"  {t}: {c}")

# Latest run after last new game
last_ng_event_idx = None
for i in range(len(events) - 1, -1, -1):
    e = events[i]
    if e["type"] == "player_input" and e["data"]["text"].strip().lower() == "new game":
        last_ng_event_idx = i
        break
if last_ng_event_idx is not None:
    segment = events[last_ng_event_idx:]
    print(f"\nLatest run (from last new game): {len(segment)} events")
    for t, c in Counter(e["type"] for e in segment).most_common():
        print(f"  {t}: {c}")

    seg_lat = []
    pending = []
    for e in segment:
        if e["type"] == "llm_request":
            pending.append(datetime.fromisoformat(e["ts"]))
        elif e["type"] == "llm_response" and pending:
            t0 = pending.pop(0)
            t1 = datetime.fromisoformat(e["ts"])
            seg_lat.append((t1 - t0).total_seconds())
    if seg_lat:
        seg_lat.sort()
        print(
            f"Latest run LLM latency: min={seg_lat[0]:.2f}s med={seg_lat[len(seg_lat)//2]:.2f}s "
            f"max={seg_lat[-1]:.2f}s avg={sum(seg_lat)/len(seg_lat):.2f}s"
        )

    adv = [e["data"] for e in segment if e["type"] == "creation_advanced"]
    print("Latest run creation steps:")
    for a in adv:
        print(f"  {a.get('completed_step')} -> {a.get('advanced_to')}")

    print(f"Latest run drift: {sum(1 for e in segment if e['type'] == 'creation_drift')}")
    print(f"Latest run errors: {sum(1 for e in segment if e['type'] == 'error')}")

earlier = events[:last_ng_event_idx] if last_ng_event_idx else events
print("\n=== EARLIER SESSION ===")
print(f"Drift events: {sum(1 for e in earlier if e['type'] == 'creation_drift')}")
print(f"Errors: {sum(1 for e in earlier if e['type'] == 'error')}")
print(f"Finalizes: {sum(1 for e in earlier if e['type'] == 'creation_finalize')}")

errs = Counter(str(e["data"]) for e in events if e["type"] == "error")
print("\nError messages:")
for msg, c in errs.most_common():
    print(f"  {c}x {msg}")

reasons = Counter()
for e in events:
    if e["type"] == "creation_drift":
        for r in e["data"].get("reasons", []):
            reasons[r] += 1
print("\nDrift reasons:")
for r, c in reasons.most_common():
    print(f"  {r}: {c}")

ng_idxs = [
    i
    for i, e in enumerate(events)
    if e["type"] == "player_input" and e["data"]["text"].strip().lower() == "new game"
]
fin_idxs = [i for i, e in enumerate(events) if e["type"] == "creation_finalize"]
completed = 0
for ng in ng_idxs:
    nxt_fin = next((f for f in fin_idxs if f > ng), None)
    nxt_ng = next((n for n in ng_idxs if n > ng), None)
    if nxt_fin and (nxt_ng is None or nxt_fin < nxt_ng):
        completed += 1
print(
    f"\nNew game -> finalize: {completed} completed / {len(ng_idxs)} total "
    f"({100 * completed / len(ng_idxs):.1f}%)"
)

creation_durations = []
for ng in ng_idxs:
    nxt_fin = next((f for f in fin_idxs if f > ng), None)
    nxt_ng = next((n for n in ng_idxs if n > ng), None)
    if nxt_fin and (nxt_ng is None or nxt_fin < nxt_ng):
        t0 = datetime.fromisoformat(events[ng]["ts"])
        t1 = datetime.fromisoformat(events[nxt_fin]["ts"])
        creation_durations.append((t1 - t0).total_seconds())
if creation_durations:
    creation_durations.sort()
    print(
        f"Creation duration: min={creation_durations[0]:.0f}s "
        f"med={creation_durations[len(creation_durations) // 2]:.0f}s "
        f"max={creation_durations[-1]:.0f}s"
    )

explore = [
    e
    for e in events
    if e["type"] == "tool_call"
    and e["data"]["name"] in ("enter_dungeon", "compass_exits", "travel_to")
]
print(f"\nExploration tool calls total: {len(explore)}")
for e in explore:
    print(" ", e["ts"], e["data"]["name"], e["data"].get("args"))

cutoff = datetime.fromisoformat("2026-05-20T18:30:00")
recent_drift = [
    e
    for e in events
    if e["type"] == "creation_drift" and datetime.fromisoformat(e["ts"]) >= cutoff
]
print(f"\nDrift after 18:30: {len(recent_drift)}")
