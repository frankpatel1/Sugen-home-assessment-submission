import json
from scripts.test_abbreviations import search, notes, mms

mms_map = {r["code"]: r["title"] for r in mms}

print("Notes missed at top 50:")
for i, n in enumerate(notes, 1):
    preds = search(n["text"], top_k=50)
    gset = set(n["gold"])
    if not any(c in gset for c in preds):
        print(f"\n[{i:02d}] {n['id']} style={n.get('style')}")
        print(f"  Gold: {n['gold']} -> {[mms_map.get(c) for c in n['gold']]}")
        print(f"  Snippet: {n['text'][:150]}...")
