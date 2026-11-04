import json

with open("data/dev_notes.jsonl", "r", encoding="utf-8") as f:
    notes = [json.loads(line) for line in f]

with open("data/mms-2026-01.json", "r", encoding="utf-8") as f:
    mms_list = json.load(f)
mms = {r["code"]: r for r in mms_list}

print(f"Total dev notes: {len(notes)}")
for i, n in enumerate(notes, 1):
    g_info = [f"{c} ({mms.get(c, {}).get('title', 'UNKNOWN')})" for c in n["gold"]]
    print(f"\n[{i:02d}] {n['id']} | style={n.get('style')} | gold={', '.join(g_info)}")
    first_few_lines = n["text"].strip().split("\n")
    print(f"     Text snippet: {first_few_lines[0][:100]}...")
    if len(first_few_lines) > 1:
        print(f"     Last line: {first_few_lines[-1][:100]}...")

