import zipfile

with zipfile.ZipFile("data/SimpleTabulation-ICD-11-MMS-en.zip") as z:
    with z.open("SimpleTabulation-ICD-11-MMS-en.txt") as f:
        rows = [line.decode("utf-8-sig").strip().split("\t") for line in f]

by_furi = {}
code_to_furi = {}
for r in rows:
    if len(r) > 4:
        furi = r[0].strip()
        title = r[4].strip().strip('"').lstrip("- ")
        code = r[2].strip() if len(r) > 2 else ""
        parent = r[18].strip() if len(r) > 18 else ""
        by_furi[furi] = {"code": code, "title": title, "parent": parent}
        if code and code not in code_to_furi:
            code_to_furi[code] = furi

target_codes = ["1F23.10", "FA01.Z", "DA22.Z", "GA90", "BA00.0", "5A02.0", "BD90.0", "JA62.1"]
for tc in target_codes:
    furi = code_to_furi.get(tc)
    chain = []
    curr = furi
    while curr and curr in by_furi:
        chain.append(by_furi[curr]["title"])
        curr = by_furi[curr]["parent"]
    print(f"{tc}:", " > ".join(reversed(chain)))
