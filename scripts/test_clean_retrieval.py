import json
import re
from collections import Counter
import math

with open("data/mms-2026-01.json", "r", encoding="utf-8") as f:
    mms = json.load(f)

with open("data/dev_notes.jsonl", "r", encoding="utf-8") as f:
    notes = [json.loads(l) for l in f]

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "each", "few", "for", "from", "further", "had", "has", "have", "having",
    "he", "her", "here", "him", "his", "how", "i", "if", "in", "into", "is", "it", "its",
    "me", "more", "most", "my", "no", "nor", "not", "of", "off", "on", "once",
    "only", "or", "other", "ought", "our", "out", "over", "own", "same", "she",
    "so", "some", "such", "than", "that", "the", "their", "them", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why", "with",
    "you", "your", "patient", "doctor", "c", "o", "x", "yr", "yrs", "day", "days", "wk", "wks", "mo", "mos"
}

# Key synonyms and colloquialisms
SYNONYMS = {
    "malaria": ["coartem", "al", "mrdt", "mps", "falciparum", "plasmodium"],
    "chickenpox": ["varicella"],
    "jiggers": ["tungiasis", "fleas"],
    "tb": ["tuberculosis", "ptb", "rhze", "tibu"],
    "urti": ["nasopharyngitis", "upper respiratory", "coryza", "cold"],
    "gerd": ["reflux", "heartburn", "acid reflux"],
    "bph": ["hyperplasia of prostate", "prostate enlargement"],
    "tonsillitis": ["tonsils", "tonsil"],
    "pneumonia": ["chest infection", "consolidation"],
    "schistosomiasis": ["bilharzia", "haematobium"],
    "candidosis": ["candidiasis", "thrush", "monilia", "curd"],
    "osteoarthritis": ["crepitus", "knee oa"],
    "hypertension": ["htn", "high bp"]
}

EXPANSIONS = {}
for canon, words in SYNONYMS.items():
    for w in words:
        EXPANSIONS[w] = canon

def tokenize(text):
    tokens = re.findall(r"\b[a-zA-Z0-9\.\-]+\b", text.lower())
    res = []
    for t in tokens:
        if t in STOPWORDS or len(t) <= 1 or t.isdigit():
            continue
        res.append(t)
        if t in EXPANSIONS:
            res.append(EXPANSIONS[t])
    return res

doc_tokens = [tokenize(item["title"]) for item in mms]
doc_lens = [len(dt) for dt in doc_tokens]
df = Counter()
for dt in doc_tokens:
    for t in set(dt):
        df[t] += 1
N = len(mms)
avgdl = sum(doc_lens) / max(1, N)
idf = {term: math.log(1 + (N - freq + 0.5) / (freq + 0.5)) for term, freq in df.items()}
k1 = 1.2
b = 0.75

inv_idx = {}
for doc_id, tokens in enumerate(doc_tokens):
    tf_map = Counter(tokens)
    for t, tf in tf_map.items():
        if t not in inv_idx:
            inv_idx[t] = []
        inv_idx[t].append((doc_id, tf))

def search(note_text, top_k=5):
    # Try finding Dx/Assessment lines
    dx_lines = []
    for line in note_text.splitlines():
        if re.search(r"\b(?:dx|assessment|a|impression)\b\s*[:\-]", line, re.IGNORECASE):
            dx_lines.append(line)
            
    q_counts = Counter(tokenize(note_text))
    if dx_lines:
        dx_tokens = tokenize(" ".join(dx_lines))
        for dt in dx_tokens:
            q_counts[dt] += 5  # Heavily prioritize diagnosis
            
    scores = {}
    for qt, qf in q_counts.items():
        if qt in inv_idx:
            cur_idf = idf[qt]
            for doc_id, tf in inv_idx[qt]:
                doc_len = doc_lens[doc_id]
                s = cur_idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avgdl)))
                scores[doc_id] = scores.get(doc_id, 0.0) + (s * (1 + 0.3 * math.log(1 + qf)))
                
    ranked = []
    for doc_id, score in scores.items():
        item = mms[doc_id]
        s = score
        if item.get("leaf"):
            s *= 1.2
        if item.get("residual") and ".z" in item["code"].lower():
            s *= 1.1
        ranked.append((item["code"], s))
        
    ranked.sort(key=lambda x: x[1], reverse=True)
    return [c for c, _ in ranked[:top_k]]

top1 = 0
top3 = 0
for n in notes:
    preds = search(n["text"], top_k=3)
    gset = set(n["gold"])
    if preds and preds[0] in gset:
        top1 += 1
    if any(c in gset for c in preds[:3]):
        top3 += 1

print(f"Top 1: {top1} / {len(notes)} ({top1/len(notes):.3f})")
print(f"Top 3: {top3} / {len(notes)} ({top3/len(notes):.3f})")
pts = 75.0 * (2/3 * (top1 / len(notes)) + 1/3 * (top3 / len(notes)))
print(f"Score out of 75: {pts:.2f}")

for k in [5, 10, 20, 30, 50]:
    hits = sum(1 for n in notes if any(c in set(n["gold"]) for c in search(n["text"], top_k=k)))
    print(f"Recall @ {k}: {hits} / {len(notes)} ({hits/len(notes):.3f})")
