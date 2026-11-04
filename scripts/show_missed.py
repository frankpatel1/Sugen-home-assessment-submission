from scripts.test_unified_offline import notes, predict_offline, mms_by_code

for n in notes:
    preds = predict_offline(n["text"])
    gset = set(n["gold"])
    if not (preds and preds[0] in gset):
        print(f"Missed {n['id']}: Gold={n['gold']} ({[mms_by_code.get(c,{}).get('title') for c in n['gold']]})")
        print(f"  Preds: {preds}")
        print(f"  Text: {n['text'][:120]}...\n")
