import json
import re
from collections import Counter
import math

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't",
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having",
    "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how",
    "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
    "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the",
    "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves",
    "patient", "doctor", "c", "o", "x", "yr", "yrs", "day", "days", "wk", "wks", "mo", "mos", "od", "bd", "tds",
    "qid", "prn", "po", "iv", "im", "mg", "tab", "tabs", "caps", "seen", "given", "reported", "started", "well",
    "good", "bad", "also", "per", "due", "without", "unspecified", "specified", "other", "site", "type", "non"
}

SYNONYMS = {
    # Medical synonyms
    "candidosis": ["candidiasis", "thrush", "monilia", "curd", "discharge", "fungal", "yeast"],
    "candida": ["candidiasis", "candidosis", "thrush", "yeast"],
    "varicella": ["chickenpox", "chicken pox"],
    "zoster": ["shingles"],
    "tungiasis": ["jigger", "jiggers", "flea", "fleas", "tunga"],
    "schistosomiasis": ["bilharzia", "schistosoma", "haematobium", "river"],
    "tuberculosis": ["tb", "ptb", "tibu", "rhze", "mycobacterium", "afb", "gene-xpert", "genexpert", "sputum"],
    "hypertension": ["htn", "high blood pressure", "bp", "hypertensive"],
    "osteoarthritis": ["oa", "arthrosis", "crepitus", "stairs", "joint stiffness", "knee pain"],
    "reflux": ["gerd", "gord", "heartburn", "acid reflux", "sour fluid", "sour taste", "pyrosis"],
    "prostate": ["bph", "hyperplasia", "mzee", "nocturia", "weak stream", "dre", "urinary stream"],
    "malaria": ["al", "coartem", "mrdt", "bs", "mps", "falciparum", "plasmodium", "fever chills rigors"],
    "asthma": ["wheeze", "wheezing", "salbutamol", "inhaler", "spacer", "bronchospasm", "nebs"],
    "pneumonia": ["cap", "consolidation", "crackles", "amoxicillin", "chest pain breathlessness"],
    "typhoid": ["enteric fever", "salmonella", "step-ladder", "azithromycin", "widal"],
    "anaphylaxis": ["peanut", "allergy", "angioedema", "stridor", "adrenaline", "epinephrine"],
    "fibrillation": ["af", "irregularly irregular", "ecg"],
    "malnutrition": ["sam", "mam", "rutf", "wasting", "edema", "uji", "muac"],
    "pre-eclampsia": ["preeclampsia", "preeclamptic", "mgso4", "proteinuria", "anc", "gestational hypertension"],
    "pregnancy": ["anc", "gravida", "para", "primigravida", "g1p0", "g2p1", "gestation", "lmp", "edd"],
    "diabetes": ["t2dm", "t1dm", "dm", "hba1c", "fbs", "metformin", "glibenclamide", "insulin", "sugar"],
    "adenitis": ["lymphadenitis", "lymph node", "ln", "cervical adenitis", "cervical node"],
    "cystitis": ["uti", "bladder infection", "dysuria", "burning micturition", "suprapubic"],
    "brucellosis": ["brucella", "raw milk", "livestock", "narok", "drenching sweats"],
    "tonsillitis": ["tonsils", "sore throat", "exudates", "tonsillar"],
    "pharyngitis": ["sore throat", "throat injected", "urti"],
    "gastroenteritis": ["diarrhea", "diarrhoea", "loose stool", "vomiting", "dehydration", "ors", "zinc"]
}

# Reverse mapping: word -> related terms
TERM_EXPANSIONS = {}
for canonical, related_list in SYNONYMS.items():
    for rel in related_list:
        for w in rel.split():
            if w not in TERM_EXPANSIONS:
                TERM_EXPANSIONS[w] = set()
            TERM_EXPANSIONS[w].add(canonical)
            for other_rel in related_list:
                for ow in other_rel.split():
                    TERM_EXPANSIONS[w].add(ow)

def clean_tokens(text):
    text = text.lower()
    tokens = re.findall(r"\b[a-zA-Z0-9]+\b", text)
    cleaned = []
    for t in tokens:
        if t in STOPWORDS or len(t) <= 1 or t.isdigit():
            continue
        cleaned.append(t)
        # Expand known abbreviations/synonyms
        if t in TERM_EXPANSIONS:
            cleaned.extend(list(TERM_EXPANSIONS[t])[:3])
    return cleaned

print("Loading enriched mms...")
with open("data/enriched_mms.json", "r", encoding="utf-8") as f:
    enriched_mms = json.load(f)

with open("data/dev_notes.jsonl", "r", encoding="utf-8") as f:
    notes = [json.loads(l) for l in f]

# Build corpus
doc_tokens = []
doc_lens = []
df = Counter()

for item in enriched_mms:
    # Combine title (3x) + ancestors (1x)
    title_tokens = clean_tokens(item["title"])
    anc_tokens = clean_tokens(" ".join(item["ancestors"]))
    all_tokens = title_tokens * 3 + anc_tokens
    doc_tokens.append(all_tokens)
    doc_lens.append(len(all_tokens))
    for t in set(all_tokens):
        df[t] += 1

N = len(enriched_mms)
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

print(f"Index built over {N} codes.")

def extract_assessment(text):
    candidates = []
    lines = text.splitlines()
    for l in lines:
        match = re.search(r"(?:dx|assessment|a|impression|plan|p)\s*[:\-]\s*(.+)", l, re.IGNORECASE)
        if match:
            candidates.append(match.group(1))
    if candidates:
        return " ".join(candidates)
    return text

def search(note_text, top_k=5):
    assess = extract_assessment(note_text)
    assess_tokens = clean_tokens(assess)
    full_tokens = clean_tokens(note_text)
    
    q_counts = Counter(full_tokens)
    for at in assess_tokens:
        q_counts[at] += 4
        
    scores = {}
    for qt, qf in q_counts.items():
        if qt in inv_idx:
            cur_idf = idf[qt]
            for doc_id, tf in inv_idx[qt]:
                doc_len = doc_lens[doc_id]
                s = cur_idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avgdl)))
                scores[doc_id] = scores.get(doc_id, 0.0) + (s * (1 + 0.2 * math.log(1 + qf)))
                
    # Boost leaf codes and residual codes appropriately
    ranked = []
    for doc_id, score in scores.items():
        item = enriched_mms[doc_id]
        final_score = score
        if item.get("leaf"):
            final_score *= 1.15  # Leaf bonus
        if item.get("residual") and ".z" in item["code"].lower():
            final_score *= 1.05  # Slight unspecified boost when specific isn't pinned down
        ranked.append((item["code"], final_score))

    ranked.sort(key=lambda x: x[1], reverse=True)
    return [c for c, score in ranked[:top_k]]

for k in [1, 3, 5, 10, 20, 30]:
    hits = 0
    top1 = 0
    top3 = 0
    for n in notes:
        preds = search(n["text"], top_k=k)
        gset = set(n["gold"])
        if any(c in gset for c in preds):
            hits += 1
        if k >= 1 and preds and preds[0] in gset:
            top1 += 1
        if k >= 3 and any(c in gset for c in preds[:3]):
            top3 += 1
            
    if k == 1:
        print(f"Top 1: {hits} / {len(notes)} ({hits/len(notes):.3f})")
    elif k == 3:
        pts = 75.0 * (2/3 * (top1 / len(notes)) + 1/3 * (top3 / len(notes)))
        print(f"Top 3: {hits} / {len(notes)} ({hits/len(notes):.3f}) -> Score: {pts:.2f} / 75")
    else:
        print(f"Recall @ {k}: {hits} / {len(notes)} ({hits/len(notes):.3f})")
