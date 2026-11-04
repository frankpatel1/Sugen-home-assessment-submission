import zipfile

with zipfile.ZipFile("data/SimpleTabulation-ICD-11-MMS-en.zip") as z:
    with z.open("SimpleTabulation-ICD-11-MMS-en.txt") as f:
        header = f.readline().decode("utf-8-sig").strip().split("\t")
        rows = []
        for line in f:
            parts = line.decode("utf-8-sig").strip().split("\t")
            rows.append(parts)

print(f"Total rows: {len(rows)}")
by_furi = {}
for r in rows:
    if len(r) > 4:
        furi = r[0].strip()
        title = r[4].strip().strip('"').lstrip("- ")
        code = r[2].strip() if len(r) > 2 else ""
        parent = r[18].strip() if len(r) > 18 else ""
        by_furi[furi] = {"code": code, "title": title, "parent": parent}

sample = [r for r in rows if len(r) > 2 and r[2] == "1A00"]
if sample:
    furi = sample[0][0].strip()
    curr = furi
    chain = []
    while curr and curr in by_furi:
        chain.append(by_furi[curr]["title"])
        curr = by_furi[curr]["parent"]
    print("Ancestry for 1A00:", " > ".join(reversed(chain)))
