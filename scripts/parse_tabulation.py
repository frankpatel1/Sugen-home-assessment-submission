import zipfile
import csv

with zipfile.ZipFile("data/SimpleTabulation-ICD-11-MMS-en.zip") as z:
    with z.open("SimpleTabulation-ICD-11-MMS-en.txt") as f:
        # Read first 20 lines
        lines = [f.readline().decode("utf-8-sig") for _ in range(20)]

for i, l in enumerate(lines[:10]):
    parts = l.strip().split("\t")
    print(f"Row {i}: len={len(parts)}")
    print(f"  Code: {parts[2] if len(parts) > 2 else ''} | Title: {parts[4] if len(parts) > 4 else ''} | Kind: {parts[5] if len(parts) > 5 else ''}")
