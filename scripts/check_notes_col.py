import zipfile

with zipfile.ZipFile("data/SimpleTabulation-ICD-11-MMS-en.zip") as z:
    with z.open("SimpleTabulation-ICD-11-MMS-en.txt") as f:
        header = f.readline().decode("utf-8-sig").strip().split("\t")
        print("Header fields:", header)
        notes_found = 0
        for line in f:
            parts = line.decode("utf-8-sig").strip().split("\t")
            if len(parts) > 17 and parts[17].strip():
                print(f"Code {parts[2]}: {parts[4]} -> Note: {parts[17][:100]}")
                notes_found += 1
                if notes_found >= 5:
                    break
