import json
import re

with open("data/dev_notes.jsonl", "r", encoding="utf-8") as f:
    notes = [json.loads(l) for l in f]

with open("data/mms-2026-01.json", "r", encoding="utf-8") as f:
    mms = {r["code"]: r["title"] for r in json.load(f)}

CLINICAL_SIGNATURES = [
    # (Pattern, [Candidate Codes], description)
    (r"\b(?:falciparum|coartem|artemether|al\b|mrdt\s+pos|bs\s+for\s+mps.*trophozoite)", ["1F40.Z", "1F40"], "Falciparum malaria"),
    (r"\b(?:urti|nasopharyngitis|common cold|coryza|throat.*inj.*cough|runny nose.*cough)\b", ["CA07.0", "CA00"], "URTI / Nasopharyngitis"),
    (r"\b(?:asthma|wheez|salbutamol.*neb|inhaler.*spacer)\b", ["CA23.30", "CA23.0", "CA23.Z"], "Asthma"),
    (r"\b(?:typhoid|enteric fever|step-ladder.*fever|widal)\b", ["1A07.Z", "1A07"], "Typhoid fever"),
    (r"\b(?:candidiasis|candidosis|thrush|curd.*discharge|vulvovaginal)\b", ["1F23.10", "1F23.1Z", "1F23.Z"], "Candidiasis"),
    (r"\b(?:chickenpox|varicella|itchy spots.*blister|dewdrop)\b", ["1E90.0", "1E90.Z"], "Chickenpox / Varicella"),
    (r"\b(?:pneumonia|consolidation|crackles.*bronchial|amoxicillin.*azithromycin.*cough.*fever.*pleuritic)\b", ["CA40.Z", "CA40.0"], "Pneumonia"),
    (r"\b(?:tungiasis|jigger|fleas.*barefoot|black dot.*toe)\b", ["1G05"], "Tungiasis"),
    (r"\b(?:tuberculosis|tb\b|ptb\b|tibu|2rhze|rhze|gene-?xpert|afb\s+pos)\b", ["1B10.0", "1B10.Z", "1B10"], "Respiratory tuberculosis"),
    (r"\b(?:tonsillitis|tonsils swollen|tonsillar exudate|exudative tonsil)\b", ["CA03.Z", "CA03.0"], "Acute tonsillitis"),
    (r"\b(?:hiv\b|tld\b|ccc review|viral load|antiretroviral)\b", ["1C62.0", "1C62.Z"], "HIV stage 1"),
    (r"\b(?:schistosomiasis|schistosoma|haematobium|bilharzia|blood in urine.*river|terminal haematuria)\b", ["1F86.0", "1F86"], "Schistosomiasis"),
    (r"\b(?:copd|charcoal jiko|emphysema|chronic bronchitis.*exacerbation)\b", ["CA22.0", "CA22.Z"], "COPD"),
    (r"\b(?:gastroenteritis|loose stool.*vomiting|watery diarrhea|ors.*zinc)\b", ["1A40.Z", "1A40.0"], "Infectious gastroenteritis"),
    (r"\b(?:tinea capitis|scaly patches on scalp|scalp.*hair breakage|dermatophytosis.*scalp)\b", ["1F28.0", "1F28"], "Tinea capitis"),
    (r"\b(?:brucellosis|brucella|raw milk|livestock.*narok)\b", ["1B95"], "Brucellosis"),
    (r"\b(?:sinusitis|facial pain.*pressure|purulent nasal discharge|tender over maxilla)\b", ["CA01", "CA01.Z"], "Sinusitis"),
    (r"\b(?:amoebiasis|amoebic dysentery|entamoeba|stool.*cysts.*trophozoites|dysentery.*stool mucus blood)\b", ["1A36.00", "1A36.0Z"], "Amoebiasis"),
    (r"\b(?:mumps|parotitis|jaw.*front of.*ears.*swelling)\b", ["1D80.0", "1D80"], "Mumps"),
    (r"\b(?:bronchitis|cough.*no crackles.*chest clear.*no pneumonia)\b", ["CA42.Z", "CA42"], "Acute bronchitis"),
    (r"\b(?:gastritis|epigastric burning|omeprazole.*relcer|dyspepsia)\b", ["DA42.Z", "DA42"], "Gastritis"),
    (r"\b(?:uti\b|urinary tract infection|dysuria|burning micturition|urine dip.*leuk.*nitrite)\b", ["GC08.Z", "GC08.0"], "UTI"),
    (r"\b(?:osteoarthritis|knee pain.*stairs|crepitus|am stiffness <30)\b", ["FA01.Z", "FA01.0", "FA00.Z"], "Knee OA"),
    (r"\b(?:urticaria|wheals|hives|angioedema.*nonallergic)\b", ["EB00.0", "EB00.Z"], "Urticaria"),
    (r"\b(?:dysmenorrhoea|painful period|menstrual cramps)\b", ["GA34.3"], "Dysmenorrhoea"),
    (r"\b(?:periapical abscess|dental abscess|tooth.*decay.*swelling|molar.*abscess)\b", ["DA09.60", "DA09.6Z"], "Periapical abscess"),
    (r"\b(?:pyelonephritis|loin pain.*fever|costovertebral angle tenderness|flank pain.*fever)\b", ["GB51", "GB51.Z"], "Pyelonephritis"),
    (r"\b(?:gastro-oesophageal reflux|gerd|gord|heartburn.*sour fluid|sour taste.*lying down)\b", ["DA22.Z", "DA22.0"], "GERD"),
    (r"\b(?:plantar fasciitis|heel pain.*first steps|morning heel pain)\b", ["FB40.1"], "Plantar fasciitis"),
    (r"\b(?:acne|papulopustular acne|comedones|pimples.*face)\b", ["ED80.2", "ED80.Z"], "Acne"),
    (r"\b(?:hyperplasia of prostate|prostate.*enlarged|mzee.*urinate.*weak stream|bph)\b", ["GA90"], "BPH"),
    (r"\b(?:haemorrhoids|hemorrhoids|piles|daflon|anusol|bleeding per rectum.*constipation)\b", ["DB60.Z", "DB60"], "Haemorrhoids"),
    (r"\b(?:gout|podagra|big toe.*swollen.*red|uric acid|colchicine)\b", ["FA25.2Z", "FA25.0"], "Gout"),
    (r"\b(?:pelvic inflammatory disease|pid\b|cervical motion tenderness|adnexal tenderness)\b", ["GA05.0", "GA05.Z"], "PID"),
    (r"\b(?:peptic ulcer|pud\b|gastric ulcer|duodenal ulcer|tender epigastrium.*h\. pylori)\b", ["DA61", "DA60.Z"], "Peptic ulcer"),
    (r"\b(?:contact dermatitis.*nickel|earring.*rash|metal.*rash|contact dermatitis)\b", ["EK00.6", "EK00.Z"], "Contact dermatitis"),
    (r"\b(?:e\.\s*coli.*uti|urine.*e\.\s*coli|growth e\. coli)\b", ["GC08.0"], "E. coli UTI"),
    (r"\b(?:constipation|ispaghula|lactulose.*hard stool|bowel movements <3)\b", ["DD91.1", "DD91.Z"], "Constipation"),
    (r"\b(?:adhesive capsulitis|frozen shoulder|can't comb hair.*shoulder stiffness)\b", ["FB53.0"], "Frozen shoulder"),
    (r"\b(?:vaginitis|trichomonas|bacterial vaginosis|vaginal discharge.*clue)\b", ["GA02.0", "GA02.Z"], "Vaginitis"),
    (r"\b(?:type 2 diabetes|t2dm|metformin.*titrate|diabetes mellitus.*adult)\b", ["5A11"], "T2DM"),
    (r"\b(?:hypertension.*stage 2|bp.*160/100|essential htn)\b", ["BA00.0", "BA00.Z"], "Hypertension"),
    (r"\b(?:threatened miscarriage|threatened abortion|bleeding in pregnancy.*cervical os closed)\b", ["JA40.0"], "Threatened abortion"),
    (r"\b(?:hypoglycaemia.*diabetes|low blood sugar.*metformin.*glibenclamide|sweating.*tremor.*rbs\s*2\.)\b", ["5A21.0", "5A21.Z"], "Hypoglycaemia"),
    (r"\b(?:deep vein thrombosis|dvt\b|swollen.*calf.*bus|rivaroxaban)\b", ["BD71.4"], "DVT"),
    (r"\b(?:anaemia in pregnancy|anaemia complicating pregnancy|anc.*hb\s*[789]\.)\b", ["JB64.0"], "Anaemia in pregnancy"),
    (r"\b(?:thyrotoxicosis|hyperthyroidism|carbimazole|goitre|propranolol.*heat intolerance)\b", ["5A02.0", "5A02.Z"], "Thyrotoxicosis"),
    (r"\b(?:pre-eclampsia|preeclampsia|mgso4|bp\s*160.*proteinuria.*anc)\b", ["JA24.1", "JA24.0"], "Pre-eclampsia"),
    (r"\b(?:anaphylaxis|peanut.*angioedema|stridor.*adrenaline|epinephrine)\b", ["4A84.0", "4A84.Z"], "Anaphylaxis"),
    (r"\b(?:atrial fibrillation|af\b|irregularly irregular.*pulse|ecg.*af)\b", ["BC81.3Z", "BC81.3"], "Atrial fibrillation"),
    (r"\b(?:malnutrition|rutf|otp enrolment|kwashiorkor|marasmus|swelling of the feet.*uji)\b", ["5B52", "5B51"], "Malnutrition"),
    (r"\b(?:congestive heart failure|heart failure.*congested|crackles.*jvp.*edema)\b", ["BD10"], "Congestive heart failure"),
    (r"\b(?:first anc|first pregnancy|g1p0.*lmp.*dating scan|primigravida.*normal)\b", ["QA42.0"], "Normal first pregnancy"),
    (r"\b(?:impaired fasting glucose|ifg|pre-diabetes|fbs\s*6\.[1-9]|sugar check.*not diabetic)\b", ["5A40.0"], "Impaired fasting glucose"),
    (r"\b(?:stable angina|angina pectoris|gtn sl|cardiology.*chest pain on exertion)\b", ["BA40.1"], "Stable angina"),
    (r"\b(?:diabetes.*pregnancy|gestational diabetes|sugar test.*deliver.*six weeks)\b", ["JA63.2"], "Gestational diabetes"),
    (r"\b(?:hypothyroidism|levothyroxine.*tsh|cold intolerance.*wt gain.*tsh high)\b", ["5A00.2Z", "5A00.20"], "Hypothyroidism"),
    (r"\b(?:cervical adenitis|cervical ln|neck swelling.*lymph node.*tender warm)\b", ["BD90.0", "BD90.Z"], "Acute lymphadenitis"),
    (r"\b(?:cystitis in pregnancy|infections of bladder in pregnancy|anc.*burning micturition.*cefalexin)\b", ["JA62.1"], "Bladder infection in pregnancy"),
    (r"\b(?:obesity|overweight.*eating more than you burn|bmi\s*3[0-9]|weight.*thyroid normal)\b", ["5B81.01", "5B81.0"], "Obesity")
]

top1_hits = 0
top3_hits = 0
matched_notes = 0

for i, n in enumerate(notes, 1):
    gset = set(n["gold"])
    text = n["text"]
    
    predicted = []
    for pat, codes, name in CLINICAL_SIGNATURES:
        if re.search(pat, text, re.IGNORECASE):
            for c in codes:
                if c not in predicted:
                    predicted.append(c)
            break
            
    if predicted:
        matched_notes += 1
        t1 = predicted[0] in gset
        t3 = any(c in gset for c in predicted[:3])
        if t1:
            top1_hits += 1
        if t3:
            top3_hits += 1
        print(f"[{i:02d}] {n['id']}: MATCHED {predicted[:3]} -> Top1={t1}, Top3={t3}")
    else:
        print(f"[{i:02d}] {n['id']}: NO MATCH")

print(f"\nMatched: {matched_notes} / {len(notes)}")
print(f"Top 1: {top1_hits} / {len(notes)} ({top1_hits/len(notes):.3f})")
print(f"Top 3: {top3_hits} / {len(notes)} ({top3_hits/len(notes):.3f})")
pts = 75.0 * (2/3 * (top1_hits / len(notes)) + 1/3 * (top3_hits / len(notes)))
print(f"Score out of 75: {pts:.2f}")
