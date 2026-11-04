import json

with open("data/dev_notes.jsonl", "r", encoding="utf-8") as f:
    notes = [json.loads(l) for l in f]

with open("data/mms-2026-01.json", "r", encoding="utf-8") as f:
    mms = {r["code"]: r["title"] for r in json.load(f)}

for i, n in enumerate(notes, 1):
    gold_str = ", ".join(f"{c} [{mms.get(c, 'MISSING')}]" for c in n["gold"])
    print(f"[{i:02d}] {n['id']} ({n['style']}): {gold_str}")
