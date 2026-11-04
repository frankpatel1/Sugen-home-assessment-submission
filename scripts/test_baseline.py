import json
import re
from collections import Counter
import math

def tokenize(text):
    return re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())

def run_bm25_baseline():
    with open("data/mms-2026-01.json", "r", encoding="utf-8") as f:
        mms = json.load(f)

    with open("data/dev_notes.jsonl", "r", encoding="utf-8") as f:
        notes = [json.loads(l) for l in f]

    # Build corpus of MMS codes
    doc_lens = []
    df = Counter()
    doc_tokens = []
    
    for item in mms:
        tokens = tokenize(item["title"])
        doc_tokens.append(tokens)
        doc_lens.append(len(tokens))
        for t in set(tokens):
            df[t] += 1
            
    N = len(mms)
    avgdl = sum(doc_lens) / max(1, N)
    
    # Precalculate IDF
    idf = {}
    for term, freq in df.items():
        idf[term] = math.log(1 + (N - freq + 0.5) / (freq + 0.5))
        
    k1 = 1.5
    b = 0.75
    
    top1_correct = 0
    top3_correct = 0
    
    for note in notes:
        q_tokens = tokenize(note["text"])
        q_counts = Counter(q_tokens)
        
        # Score against all mms
        scores = []
        for i, doc in enumerate(doc_tokens):
            score = 0.0
            doc_len = doc_lens[i]
            d_counts = Counter(doc)
            for qt, qf in q_counts.items():
                if qt in d_counts:
                    tf = d_counts[qt]
                    score += idf.get(qt, 0) * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avgdl)))
            if score > 0:
                scores.append((score, mms[i]["code"]))
                
        scores.sort(key=lambda x: x[0], reverse=True)
        pred_codes = [c for _, c in scores[:3]]
        
        gold_set = set(note["gold"])
        t1 = bool(pred_codes) and pred_codes[0] in gold_set
        t3 = any(c in gold_set for c in pred_codes)
        if t1:
            top1_correct += 1
        if t3:
            top3_correct += 1
            
    print(f"BM25 baseline (naive note text -> title):")
    print(f"Top 1: {top1_correct} / {len(notes)} ({top1_correct/len(notes):.3f})")
    print(f"Top 3: {top3_correct} / {len(notes)} ({top3_correct/len(notes):.3f})")
    score_75 = 75.0 * (2/3 * (top1_correct / len(notes)) + 1/3 * (top3_correct / len(notes)))
    print(f"Score out of 75: {score_75:.2f}")

if __name__ == "__main__":
    run_bm25_baseline()

