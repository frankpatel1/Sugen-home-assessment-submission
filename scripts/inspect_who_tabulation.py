import zipfile

with zipfile.ZipFile("data/SimpleTabulation-ICD-11-MMS-en.zip") as z:
    readme = z.read("readme.txt").decode("utf-8-sig")
    print("=== README ===")
    print(readme[:600])
    
    txt = z.read("SimpleTabulation-ICD-11-MMS-en.txt").decode("utf-8-sig")
    lines = txt.splitlines()
    print(f"\nTotal lines: {len(lines)}")
    print("=== HEADER ===")
    print(lines[0])
    print("=== ROW 1 ===")
    print(lines[1])
    print("=== ROW 2 ===")
    print(lines[2])
