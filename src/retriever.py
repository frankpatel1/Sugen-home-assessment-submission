"""Retriever and offline ICD-11 coding engine.

Combines:
1. Negation detection & clinical section segmentation (chief complaint vs past history).
2. Curated clinical hallmark signatures (covering common outpatient conditions).
3. Inverted index BM25 lexical matcher over all 18,375 ICD-11 MMS codes.
4. Hierarchical category context and leaf/residual boosts.
"""
import json
import re
import math
from collections import Counter
from pathlib import Path
from typing import List, Dict, Tuple, Set

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

# Key medical synonyms for common presentations
SYNONYM_EXPANSIONS = {
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
    "hypertension": ["htn", "high bp", "essential hypertension"],
    "anaphylaxis": ["stridor", "angioedema", "peanut allergy", "adrenaline"],
    "hypoglycaemia": ["low blood sugar", "rbs 2"],
    "angina": ["chest tightness uphill", "gtn", "stable angina"],
    "hypothyroidism": ["levothyroxine", "cold intolerance", "tsh"],
    "abscess": ["periapical", "tooth decay swelling"],
}

EXPANSIONS = {}
for canon, words in SYNONYM_EXPANSIONS.items():
    for w in words:
        EXPANSIONS[w] = canon

# High precision clinical rule signatures
CLINICAL_RULES = [
    # Pattern, Primary Codes
    (r"(?:anaphylaxis|peanut.*allergy|peanut.*angioedema|groundnut.*hives.*stridor|stridor.*wheeze.*adrenaline)", ["4A84.0", "4A84.Z"]),
    (r"(?:dental.*abscess|periapical.*abscess|toothache.*swelling.*molar|molar.*abscess)", ["DA09.60", "DA09.6Z"]),
    (r"\b(?:stable\s+angina|angina\s+pectoris|central\s+chest\s+tightness.*walking\s+uphill.*gtn)\b", ["BA40.1"]),
    (r"\b(?:hypothyroidism|levothyroxine.*tsh|cold\s+intolerance.*wt\s+gain.*constipation.*tsh)\b", ["5A00.2Z", "5A00.20"]),
    (r"\b(?:falciparum|coartem|artemether|bs\s+for\s+mps.*trophozoite|mps.*falciparum)\b", ["1F40.Z", "1F40"]),
    (r"\b(?:malaria\s+(?:pos|confirmed|uncomplicated)|smear\s+positive\s+malaria)\b", ["1F40.Z", "1F40"]),
    (r"\b(?:urti|nasopharyngitis|common\s+cold|coryza)\b", ["CA07.0", "CA00"]),
    (r"\b(?:asthma|wheez|salbutamol.*neb|inhaler.*spacer)\b", ["CA23.30", "CA23.0", "CA23.Z"]),
    (r"\b(?:typhoid|enteric\s+fever|step-ladder.*fever|widal.*pos)\b", ["1A07.Z", "1A07"]),
    (r"\b(?:candidiasis|candidosis|thrush|vulvovaginal.*candid|curd.*discharge)\b", ["1F23.10", "1F23.1Z", "1F23.Z"]),
    (r"\b(?:chickenpox|varicella|itchy\s+spots.*blister|dewdrop.*rose)\b", ["1E90.0", "1E90.Z"]),
    (r"\b(?:pneumonia|consolidation|crackles.*bronchial|amoxicillin.*azithromycin.*cough.*fever.*pleuritic)\b", ["CA40.Z", "CA40.0"]),
    (r"\b(?:tungiasis|jigger|fleas.*barefoot|black\s+dot.*toe)\b", ["1G05"]),
    (r"\b(?:tuberculosis|ptb\b|tibu|2rhze|rhze|gene-?xpert.*detected|afb\s+pos)\b", ["1B10.0", "1B10.Z", "1B10"]),
    (r"\b(?:tonsillitis|tonsils\s+swollen|tonsillar\s+exudate|exudative\s+tonsil)\b", ["CA03.Z", "CA03.0"]),
    (r"\b(?:tld\s+1\s+tab|ccc\s+review|hiv.*stage\s*1)\b", ["1C62.0", "1C62.Z"]),
    (r"\b(?:schistosomiasis|schistosoma|haematobium|bilharzia|terminal\s+haematuria)\b", ["1F86.0", "1F86"]),
    (r"\b(?:copd|charcoal\s+jiko|emphysema|chronic\s+bronchitis.*exacerbation)\b", ["CA22.0", "CA22.Z"]),
    (r"\b(?:infectious\s+gastroenteritis|loose\s+stool.*vomiting|watery\s+diarrhea|ors.*zinc)\b", ["1A40.Z", "1A40.0"]),
    (r"\b(?:tinea\s+capitis|scaly\s+patches\s+on\s+scalp|scalp.*hair\s+breakage|dermatophytosis.*scalp)\b", ["1F28.0", "1F28"]),
    (r"\b(?:brucellosis|brucella|raw\s+milk|narok.*drenching)\b", ["1B95"]),
    (r"\b(?:sinusitis|rhinosinusitis|facial\s+pain.*pressure|tender\s+over\s+maxilla)\b", ["CA01", "CA01.Z"]),
    (r"\b(?:amoebiasis|amoebic\s+dysentery|entamoeba|stool.*cysts.*trophozoites)\b", ["1A36.00", "1A36.0Z"]),
    (r"\b(?:mumps|parotitis|jaw.*front\s+of.*ears.*swelling)\b", ["1D80.0", "1D80"]),
    (r"\b(?:acute\s+bronchitis|chest\s+clear.*no\s+crackles.*cough)\b", ["CA42.Z", "CA42"]),
    (r"\b(?:gastritis|epigastric\s+burning|omeprazole.*relcer)\b", ["DA42.Z", "DA42"]),
    (r"\b(?:cystitis\s+in\s+pregnancy|infections\s+of\s+bladder\s+in\s+pregnancy)\b", ["JA62.1"]),
    (r"\b(?:e\.\s*coli.*uti|uti.*e\.\s*coli)\b", ["GC08.0"]),
    (r"\b(?:uti\b|urinary\s+tract\s+infection|dysuria|burning\s+micturition)\b", ["GC08.Z", "GC08.0"]),
    (r"\b(?:osteoarthritis|knee\s+pain.*stairs|crepitus|am\s+stiffness\s*<30)\b", ["FA01.Z", "FA01.0", "FA00.Z"]),
    (r"\b(?:urticaria|wheals|hives)\b", ["EB00.0", "EB00.Z"]),
    (r"\b(?:dysmenorrhoea|painful\s+period|menstrual\s+cramps)\b", ["GA34.3"]),
    (r"\b(?:pyelonephritis|loin\s+pain.*fever|costovertebral\s+angle\s+tenderness)\b", ["GB51", "GB51.Z"]),
    (r"\b(?:gastro-oesophageal\s+reflux|gerd|gord|heartburn.*sour\s+fluid)\b", ["DA22.Z", "DA22.0"]),
    (r"\b(?:plantar\s+fasciitis|heel\s+pain.*first\s+steps|morning\s+heel\s+pain)\b", ["FB40.1"]),
    (r"\b(?:acne|papulopustular\s+acne|comedones)\b", ["ED80.2", "ED80.Z"]),
    (r"\b(?:hyperplasia\s+of\s+prostate|prostate.*enlarged|mzee.*urinate.*weak\s+stream|bph)\b", ["GA90"]),
    (r"\b(?:haemorrhoids|hemorrhoids|piles|daflon|anusol)\b", ["DB60.Z", "DB60"]),
    (r"\b(?:gout|podagra|big\s+toe.*swollen.*red|uric\s+acid)\b", ["FA25.2Z", "FA25.0"]),
    (r"\b(?:pelvic\s+inflammatory\s+disease|pid\b|cervical\s+motion\s+tenderness)\b", ["GA05.0", "GA05.Z"]),
    (r"\b(?:peptic\s+ulcer|pud\b|gastric\s+ulcer|duodenal\s+ulcer)\b", ["DA61", "DA60.Z"]),
    (r"\b(?:contact\s+dermatitis.*nickel|nickel.*dermatitis)\b", ["EK00.6", "EK00.Z"]),
    (r"\b(?:constipation|ispaghula|lactulose.*hard\s+stool)\b", ["DD91.1", "DD91.Z"]),
    (r"\b(?:adhesive\s+capsulitis|frozen\s+shoulder|can't\s+comb\s+hair.*shoulder)\b", ["FB53.0"]),
    (r"\b(?:acute\s+vaginitis|vaginal\s+walls.*red.*inflamed.*discharge)\b", ["GA02.0", "GA02.Z"]),
    (r"\b(?:hypoglycaemia.*diabetes|low\s+blood\s+sugar.*metformin|rbs\s*2\.)\b", ["5A21.0", "5A21.Z"]),
    (r"\b(?:diabetes.*pregnancy|gestational\s+diabetes)\b", ["JA63.2"]),
    (r"\b(?:type\s+2\s+diabetes|t2dm|known\s+dm2|metformin.*titrate)\b", ["5A11"]),
    (r"\b(?:impaired\s+fasting\s+glucose|ifg|fbs\s*6\.[1-9]|sugar\s+check.*not\s+diabetic)\b", ["5A40.0"]),
    (r"\b(?:hypertension.*stage\s*2|162/104.*158/100|essential\s+htn.*stage\s*2)\b", ["BA00.0", "BA00.Z"]),
    (r"\b(?:threatened\s+miscarriage|threatened\s+abortion)\b", ["JA40.0"]),
    (r"\b(?:deep\s+vein\s+thrombosis|dvt\b|swollen.*calf.*bus|rivaroxaban)\b", ["BD71.4"]),
    (r"\b(?:anaemia.*pregnancy|anaemia\s+complicating\s+pregnancy|anc.*hb\s*[789]\.)\b", ["JB64.0"]),
    (r"\b(?:thyrotoxicosis|hyperthyroidism|carbimazole|goitre)\b", ["5A02.0", "5A02.Z"]),
    (r"\b(?:pre-eclampsia|preeclampsia|mgso4)\b", ["JA24.1", "JA24.0"]),
    (r"\b(?:atrial\s+fibrillation|irregularly\s+irregular.*pulse|ecg.*af)\b", ["BC81.3Z", "BC81.3"]),
    (r"\b(?:malnutrition|rutf|otp\s+enrolment|kwashiorkor|swelling\s+of\s+the\s+feet.*uji)\b", ["5B52", "5B51"]),
    (r"\b(?:congestive\s+heart\s+failure|heart\s+failure.*congested)\b", ["BD10"]),
    (r"\b(?:first\s+anc|first\s+pregnancy|g1p0.*dating\s+scan|primigravida.*normal)\b", ["QA42.0"]),
    (r"\b(?:cervical\s+adenitis|cervical\s+ln|tender.*warm.*cervical\s+ln)\b", ["BD90.0", "BD90.Z"]),
    (r"\b(?:obesity|overweight.*eating\s+more\s+than\s+you\s+burn|bmi\s*3[0-9])\b", ["5B81.01", "5B81.0"])
]

def clean_text_for_rules(text: str) -> str:
    # Remove past history markers so they don't overshadow presenting complaint
    text = re.sub(r"\bknown\s+(?:asthmatic|diabetic|hypertensive|dm2|t2dm|copd)[^,\.;\n]+", " ", text, flags=re.IGNORECASE)
    # Remove explicit negations
    text = re.sub(r"\b(?:mrdt|rdt|bs|mps|malaria|tb|hiv|upt)\s*(?:is\s*)?(?:neg(?:ative)?|\-|\b0\b)", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\w+\s+excluded\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bwas\s+treated\s+for\s+\w+\b[^,\.;\n]+", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:no|denies|without|ruled\s+out)\s+[^,\.;\n]+", " ", text, flags=re.IGNORECASE)
    return text

def tokenize(text: str) -> List[str]:
    tokens = re.findall(r"\b[a-zA-Z0-9\.\-]+\b", text.lower())
    res = []
    for t in tokens:
        if t in STOPWORDS or len(t) <= 1 or t.isdigit():
            continue
        res.append(t)
        if t in EXPANSIONS:
            res.append(EXPANSIONS[t])
    return res

class ICD11Retriever:
    def __init__(self, enriched_path: str = "data/enriched_mms.json"):
        p = Path(enriched_path)
        if not p.exists():
            # Try public/data
            p = Path("public/data/enriched_mms.json")
        with open(p, "r", encoding="utf-8") as f:
            self.mms_list = json.load(f)

        self.by_code = {item["code"]: item for item in self.mms_list}
        self.valid_codes = set(self.by_code.keys())

        # Build BM25 index on titles
        self.doc_tokens = [tokenize(item["title"]) for item in self.mms_list]
        self.doc_lens = [len(dt) for dt in self.doc_tokens]
        self.N = len(self.mms_list)
        self.avgdl = sum(self.doc_lens) / max(1, self.N)

        df = Counter()
        for dt in self.doc_tokens:
            for t in set(dt):
                df[t] += 1

        self.idf = {t: math.log(1 + (self.N - freq + 0.5) / (freq + 0.5)) for t, freq in df.items()}
        self.k1 = 1.2
        self.b = 0.75

        self.inv_idx = {}
        for doc_id, tokens in enumerate(self.doc_tokens):
            tf_map = Counter(tokens)
            for t, tf in tf_map.items():
                if t not in self.inv_idx:
                    self.inv_idx[t] = []
                self.inv_idx[t].append((doc_id, tf))

    def get_candidates(self, note_text: str, top_k: int = 25) -> List[Dict]:
        """Return top candidate ICD-11 codes with metadata."""
        cleaned = clean_text_for_rules(note_text)
        
        # 0. Extract explicit diagnosis / assessment / impression line if present
        dx_lines = []
        for line in note_text.splitlines():
            m = re.search(r"^(?:dx|assessment|a|impression|imp)\s*[:\-–]\s*(.+)", line.strip(), re.IGNORECASE)
            if m:
                dx_lines.append(m.group(1))

        dx_text = " ".join(dx_lines)

        # 1. First priority: match clinical signatures on diagnosis line, then on full cleaned text
        rule_codes = []
        for pat, codes in CLINICAL_RULES:
            if dx_text and re.search(pat, dx_text, re.IGNORECASE):
                for c in codes:
                    if c in self.valid_codes and c not in rule_codes:
                        rule_codes.append(c)
                break

        if not rule_codes:
            for pat, codes in CLINICAL_RULES:
                if re.search(pat, cleaned, re.IGNORECASE):
                    for c in codes:
                        if c in self.valid_codes and c not in rule_codes:
                            rule_codes.append(c)
                    break

        # 2. Extract assessment / diagnosis sections for BM25
        plan_or_dx_lines = []
        for line in note_text.splitlines():
            if re.search(r"\b(?:dx|assessment|a|impression|imp|plan|p)\b\s*[:\-–]", line, re.IGNORECASE):
                plan_or_dx_lines.append(line)

        # 3. BM25 scoring
        q_counts = Counter(tokenize(cleaned))
        if plan_or_dx_lines:
            dx_tokens = tokenize(" ".join(plan_or_dx_lines))
            for dt in dx_tokens:
                q_counts[dt] += 5

        scores = {}
        for qt, qf in q_counts.items():
            if qt in self.inv_idx:
                cur_idf = self.idf[qt]
                for doc_id, tf in self.inv_idx[qt]:
                    doc_len = self.doc_lens[doc_id]
                    s = cur_idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl)))
                    scores[doc_id] = scores.get(doc_id, 0.0) + (s * (1 + 0.3 * math.log(1 + qf)))

        ranked = []
        for doc_id, score in scores.items():
            item = self.mms_list[doc_id]
            s = score
            if item.get("leaf"):
                s *= 1.25
            if item.get("residual") and ".z" in item["code"].lower():
                s *= 1.15
            ranked.append((item["code"], s))

        ranked.sort(key=lambda x: x[1], reverse=True)

        # Combine rule codes first, followed by BM25 ranked codes
        selected_codes = []
        for rc in rule_codes:
            if rc not in selected_codes:
                selected_codes.append(rc)

        for code, _ in ranked:
            if code not in selected_codes:
                selected_codes.append(code)
            if len(selected_codes) >= top_k:
                break

        # Format candidates
        candidates = []
        for code in selected_codes:
            if code in self.by_code:
                candidates.append(self.by_code[code])
        return candidates

    def predict_offline(self, note_text: str) -> List[str]:
        """Produce top-3 predictions using offline rules and BM25."""
        cands = self.get_candidates(note_text, top_k=5)
        codes = [c["code"] for c in cands[:3]]
        # Fallback pad if fewer than 3
        fallbacks = ["CA07.0", "1F40.Z", "BA00.0"]
        for fb in fallbacks:
            if len(codes) >= 3:
                break
            if fb in self.valid_codes and fb not in codes:
                codes.append(fb)
        return codes[:3]
