import json
import re

with open("data/dev_notes.jsonl", "r", encoding="utf-8") as f:
    notes = [json.loads(l) for l in f]

found_dx = 0
for i, n in enumerate(notes, 1):
    text = n["text"]
    # Look for dx patterns
    matches = re.findall(r"(?:^|\n)\s*(?:dx|assessment|a|impression)\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    if matches:
        found_dx += 1
        print(f"[{i:02d}] {n['id']} ({n['style']}) -> {matches[0][:80]}")
    else:
        # Check last line or doctor line
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        last = lines[-1] if lines else ""
        print(f"[{i:02d}] {n['id']} ({n['style']}) [NO DX HEADER] -> Last: {last[:80]}")

print(f"\nTotal notes with explicit Dx header: {found_dx} / {len(notes)}")
