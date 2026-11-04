import json
from src.retriever import ICD11Retriever

with open("data/dev_notes.jsonl", "r", encoding="utf-8") as f:
    notes = [json.loads(l) for l in f]

retriever = ICD11Retriever()

top1 = 0
top3 = 0
out_preds = []

for n in notes:
    preds = retriever.predict_offline(n["text"])
    out_preds.append({"id": n["id"], "codes": preds})
    gset = set(n["gold"])
    if preds and preds[0] in gset:
        top1 += 1
    if any(c in gset for c in preds[:3]):
        top3 += 1

print(f"Retriever Offline Performance on {len(notes)} dev notes:")
print(f"Top 1: {top1} / {len(notes)} ({top1/len(notes):.3f})")
print(f"Top 3: {top3} / {len(notes)} ({top3/len(notes):.3f})")
pts = 75.0 * (2/3 * (top1 / len(notes)) + 1/3 * (top3 / len(notes)))
print(f"Score out of 75: {pts:.2f} / 75")

# Save predictions and run score.py
with open("out/predictions_offline.jsonl", "w", encoding="utf-8") as f:
    for op in out_preds:
        f.write(json.dumps(op) + "\n")
