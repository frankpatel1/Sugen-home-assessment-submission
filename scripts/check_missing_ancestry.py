import json

with open("data/enriched_mms.json", "r", encoding="utf-8") as f:
    items = json.load(f)

missing_ancestry = [it for it in items if not it["ancestors"]]
print(f"Total missing ancestry: {len(missing_ancestry)}")
for it in missing_ancestry[:10]:
    print(f"  {it['code']}: {it['title']} (leaf={it['leaf']}, residual={it['residual']})")
