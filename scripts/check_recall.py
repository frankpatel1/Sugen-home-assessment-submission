import json
from scripts.test_abbreviations import search, notes

for k in [5, 10, 20, 30, 50]:
    hits = 0
    for n in notes:
        preds = search(n["text"], top_k=k)
        gset = set(n["gold"])
        if any(c in gset for c in preds):
            hits += 1
    print(f"Recall @ {k}: {hits} / {len(notes)} ({hits/len(notes):.3f})")
