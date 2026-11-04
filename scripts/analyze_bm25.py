import json
import re
from collections import Counter
import math

def tokenize(text):
    return [t.lower() for t in re.findall(r"\b[a-zA-Z0-9]+\b", text)]

with open("data/mms-2026-01.json", "r", encoding="utf-8") as f:
    mms = json.load(f)

with open("data/dev_notes.jsonl", "r", encoding="utf-8") as f:
    notes = [json.loads(l) for l in f]

mms_map = {r["code"]: r for r in mms}

# Build BM25 index on titles
doc_tokens = [tokenize(item["title"]) for item in mms]
doc_lens = [len(dt) for dt in doc_tokens]
df = Counter()
for dt in doc_tokens:
    for t in set(dt):
        df[t] += 1
N = len(mms)
avgdl = sum(doc_lens) / max(1, N)
idf = {term: math.log(1 + (N - freq + 0.5) / (freq + 0.5)) for term, freq in df.items()}
k1 = 1.5
b = 0.75

# Inverted index for fast lookup
inv_idx = {}
for doc_id, tokens in enumerate(doc_tokens):
    tf_map = Counter(tokens)
    for t, tf in tf_map.items():
        if t not in inv_idx:
            inv_idx[t] = []
        inv_idx[t].append((doc_id, tf))

print(f"Index built over {N} codes.")

def search_bm25(query_text, top_k=5):
    q_tokens = tokenize(query_text)
    scores = {}
    for qt in q_tokens:
        if qt in inv_idx:
            cur_idf = idf.get(qt, 0)
            for doc_id, tf in inv_idx[qt]:
                doc_len = doc_lens[doc_id]
                s = cur_idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avgdl)))
                scores[doc_id] = scores.get(doc_id, 0.0) + s
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [(mms[doc_id]["code"], score) for doc_id, score in ranked]

# Test first 10 notes
for i, n in enumerate(notes[:10], 1):
    preds = search_bm25(n["text"], top_k=3)
    pred_codes = [c for c, s in preds]
    gset = set(n["gold"])
    hit = any(c in gset for c in pred_codes)
    print(f"\nNote {i} ({n['id']}): hit={hit}")
    print(f"  Gold: {n['gold']} -> {[mms_map.get(c, {}).get('title') for c in n['gold']]}")
    print(f"  Preds: {pred_codes} -> {[mms_map.get(c, {}).get('title') for c in pred_codes]}")
