import zipfile

with zipfile.ZipFile("data/SimpleTabulation-ICD-11-MMS-en.zip") as z:
    with z.open("SimpleTabulation-ICD-11-MMS-en.txt") as f:
        header = f.readline().decode("utf-8-sig").strip().split("\t")
        total = 0
        with_notes = 0
        for line in f:
            parts = line.decode("utf-8-sig").strip().split("\t")
            code = parts[2].strip() if len(parts) > 2 else ""
            if code:
                total += 1
                if len(parts) > 17 and parts[17].strip() and not parts[17].startswith("http"):
                    with_notes += 1

print(f"Total rows with code: {total}, with descriptive notes: {with_notes}")
