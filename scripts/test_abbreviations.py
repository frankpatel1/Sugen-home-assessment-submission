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
    # Clinical common / noise words
    "patient", "doctor", "c", "o", "x", "yr", "yrs", "day", "days", "wk", "wks", "mo", "mos", "od", "bd", "tds",
    "qid", "prn", "po", "iv", "im", "mg", "tab", "tabs", "caps", "seen", "given", "reported", "started", "well",
    "good", "bad", "also", "per", "due", "without", "unspecified", "specified", "other", "site", "type", "non",
    "mild", "moderate", "severe", "acute", "chronic" # wait, acute and chronic might be informative, let's keep them!
}
# Keep acute and chronic
STOPWORDS.remove("acute")
STOPWORDS.remove("chronic")
STOPWORDS.remove("severe")
STOPWORDS.remove("mild")

ABBREVIATIONS = {
    "urti": "upper respiratory tract infection",
    "lrti": "lower respiratory tract infection",
    "tb": "tuberculosis respiratory tuberculosis",
    "ptb": "pulmonary tuberculosis",
    "dvt": "deep vein thrombosis",
    "pe": "pulmonary embolism",
    "uti": "urinary tract infection cystitis pyelonephritis",
    "htn": "essential hypertension high blood pressure",
    "t2dm": "type 2 diabetes mellitus",
    "t1dm": "type 1 diabetes mellitus",
    "dm": "diabetes mellitus",
    "copd": "chronic obstructive pulmonary disease",
    "af": "atrial fibrillation",
    "chf": "congestive heart failure",
    "hf": "heart failure",
    "gerd": "gastro-oesophageal reflux disease gastroesophageal",
    "pud": "peptic ulcer disease gastric duodenal ulcer",
    "pid": "pelvic inflammatory disease",
    "sti": "sexually transmitted infection",
    "uri": "upper respiratory tract infection",
    "al": "artemether lumefantrine malaria",
    "coartem": "malaria plasmodium falciparum",
    "mrdt": "malaria rapid diagnostic test",
    "bs": "blood slide malaria",
    "rhze": "tuberculosis antitubercular",
    "tld": "hiv human immunodeficiency virus",
    "arv": "hiv antiretroviral",
    "art": "antiretroviral therapy hiv",
    "chickenpox": "varicella",
    "shingles": "herpes zoster",
    "jiggers": "tungiasis",
    "fleas": "tungiasis",
    "ringworm": "dermatophytosis tinea",
    "thrush": "candidosis candidiasis",
    "flu": "influenza viral infection",
    "boil": "furuncle carbuncle cutaneous abscess",
    "bilharzia": "schistosomiasis",
    "typhoid": "typhoid fever salmonella",
    "worms": "helminthiasis ascariasis",
    "amoeba": "amoebiasis entamoeba",
    "malnutrition": "undernutrition kwashiorkor marasmus acute malnutrition",
    "rutf": "malnutrition severe acute malnutrition",
    "goitre": "thyrotoxicosis hyperthyroidism goitre",
    "preeclampsia": "pre-eclampsia preeclampsia hypertension pregnancy",
    "pre-eclampsia": "pre-eclampsia severe pre-eclampsia hypertension pregnancy",
    "mgso4": "pre-eclampsia eclampsia",
    "anc": "pregnancy antenatal care supervision pregnancy",
    "c-section": "caesarean delivery",
    "g1p0": "first pregnancy supervision pregnancy",
    "primigravida": "first pregnancy supervision pregnancy",
    "miscarriage": "spontaneous abortion",
    "eczema": "atopic dermatitis eczema",
    "scabies": "scabies sarcoptes",
    "stroke": "stroke cerebrovascular cerebral infarction",
    "cva": "cerebrovascular accident stroke",
    "tia": "transient ischaemic attack",
    "mi": "myocardial infarction acute coronary",
    "gout": "gout gouty arthritis hyperuricaemia",
    "pneumonia": "pneumonia lung infection",
    "tonsillitis": "acute tonsillitis pharyngitis",
    "otitis": "otitis media ear infection",
    "conjunctivitis": "conjunctivitis eye infection pink eye",
    "cellulitis": "cellulitis bacterial skin infection",
    "impetigo": "impetigo staphylococcal",
    "gastritis": "gastritis dyspepsia",
    "gastroenteritis": "infectious gastroenteritis diarrhoea diarrhea",
    "diarrhoea": "gastroenteritis infectious diarrhea",
    "diarrhea": "gastroenteritis infectious diarrhea",
    "dysentery": "amoebiasis shigellosis bacillary dysentery",
    "measles": "measles rubeola",
    "mumps": "mumps infectious parotitis",
    "rubella": "rubella german measles",
    "whooping": "whooping cough pertussis",
    "pertussis": "pertussis whooping cough",
    "asthma": "asthma bronchial asthma status asthmaticus",
    "bronchitis": "acute bronchitis",
    "sinusitis": "acute sinusitis rhinosinusitis",
    "epilepsy": "epilepsy seizure disorder convulsions",
    "seizure": "epilepsy convulsions",
    "migraine": "migraine headache",
    "depression": "depressive disorder major depression",
    "anxiety": "generalised anxiety disorder anxiety",
    "anaemia": "anaemia iron deficiency anaemia anemia",
    "anemia": "anaemia iron deficiency anaemia anemia",
}

def clean_tokens(text):
    text = text.lower()
    for abbr, expanded in ABBREVIATIONS.items():
        pattern = r"\b" + re.escape(abbr) + r"\b"
        text = re.sub(pattern, f"{abbr} {expanded}", text)
    tokens = re.findall(r"\b[a-zA-Z0-9]+\b", text)
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1 and not t.isdigit()]

with open("data/mms-2026-01.json", "r", encoding="utf-8") as f:
    mms = json.load(f)

with open("data/dev_notes.jsonl", "r", encoding="utf-8") as f:
    notes = [json.loads(l) for l in f]

doc_tokens = [clean_tokens(item["title"]) for item in mms]
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

def extract_assessment(text):
    # Try finding Dx:, Assessment:, A:, Impression:, Plan:
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
    # Extract assessment section and give it 3x weight
    assess = extract_assessment(note_text)
    assess_tokens = clean_tokens(assess)
    full_tokens = clean_tokens(note_text)
    
    q_counts = Counter(full_tokens)
    for at in assess_tokens:
        q_counts[at] += 3
        
    scores = {}
    for qt, qf in q_counts.items():
        if qt in inv_idx:
            cur_idf = idf[qt]
            for doc_id, tf in inv_idx[qt]:
                doc_len = doc_lens[doc_id]
                s = cur_idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avgdl)))
                scores[doc_id] = scores.get(doc_id, 0.0) + (s * (1 + 0.2 * math.log(1 + qf)))
                
    # Prioritize leaf or residual codes when tied, or adjust depth
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [mms[doc_id]["code"] for doc_id, score in ranked]

top1_correct = 0
top3_correct = 0
for n in notes:
    preds = search(n["text"], top_k=3)
    gset = set(n["gold"])
    t1 = bool(preds) and preds[0] in gset
    t3 = any(c in gset for c in preds)
    if t1:
        top1_correct += 1
    if t3:
        top3_correct += 1

print(f"BM25 + Medical Abbreviations + Assessment Weighting:")
print(f"Top 1: {top1_correct} / {len(notes)} ({top1_correct/len(notes):.3f})")
print(f"Top 3: {top3_correct} / {len(notes)} ({top3_correct/len(notes):.3f})")
score_75 = 75.0 * (2/3 * (top1_correct / len(notes)) + 1/3 * (top3_correct / len(notes)))
print(f"Score out of 75: {score_75:.2f}")
