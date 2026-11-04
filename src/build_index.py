"""Build enriched index from mms-2026-01.json and WHO tabulation.

Extracts hierarchy (chapter, blocks, parent categories) and associates them
with each of the 18,375 valid MMS diagnostic codes.
"""
import json
import zipfile
import re
from pathlib import Path

def clean_title(title: str) -> str:
    return title.strip().strip('"').lstrip("- ")

def build():
    data_dir = Path("data")
    mms_path = data_dir / "mms-2026-01.json"
    zip_path = data_dir / "SimpleTabulation-ICD-11-MMS-en.zip"
    out_path = data_dir / "enriched_mms.json"

    with open(mms_path, "r", encoding="utf-8") as f:
        mms_raw = json.load(f)

    # Read tabulation
    rows = []
    with zipfile.ZipFile(zip_path) as z:
        with z.open("SimpleTabulation-ICD-11-MMS-en.txt") as f:
            for line in f:
                parts = line.decode("utf-8-sig").strip().split("\t")
                rows.append(parts)

    print(f"Loaded {len(rows)} rows from WHO tabulation")

    # Index entities by URI, code, blockId, and chapter
    entity_by_uri = {}
    code_to_entity = {}
    block_to_title = {}
    chapter_map = {}

    for r in rows:
        if len(r) > 5:
            furi = r[0].strip()
            luri = r[1].strip()
            code = r[2].strip() if len(r) > 2 else ""
            block_id = r[3].strip() if len(r) > 3 else ""
            title = clean_title(r[4])
            kind = r[5].strip() if len(r) > 5 else ""
            chap_no = r[8].strip() if len(r) > 8 else ""
            parent = r[18].strip() if len(r) > 18 else ""

            if kind == "chapter" and chap_no:
                chapter_map[chap_no] = title

            ent = {
                "furi": furi,
                "luri": luri,
                "code": code,
                "block_id": block_id,
                "title": title,
                "kind": kind,
                "chap_no": chap_no,
                "parent": parent
            }

            if furi:
                entity_by_uri[furi] = ent
            if luri:
                entity_by_uri[luri] = ent
            if block_id:
                block_to_title[block_id] = title
            if code:
                code_to_entity[code] = ent

    print(f"Found {len(chapter_map)} chapters in tabulation.")

    def get_ancestry(code, title, chapter):
        chain = []
        ent = code_to_entity.get(code)
        
        # If not found directly, try base code (e.g. 1A07.Z -> 1A07)
        if not ent:
            base_code = re.sub(r"\.[YZ0-9]+$", "", code)
            ent = code_to_entity.get(base_code)
            if ent and ent["title"] and ent["title"] != title:
                chain.append(ent["title"])
                
        if ent:
            curr = ent.get("parent")
            visited = set()
            while curr and curr in entity_by_uri and curr not in visited:
                visited.add(curr)
                p_ent = entity_by_uri[curr]
                if p_ent["title"] and p_ent["title"] != title and p_ent["title"] not in chain:
                    chain.append(p_ent["title"])
                curr = p_ent.get("parent")

        res = list(reversed(chain))
        # Ensure chapter title is first if available and not present
        chap_title = chapter_map.get(chapter)
        if chap_title and chap_title != title:
            if not res or res[0] != chap_title:
                res.insert(0, chap_title)

        return res

    enriched = []
    found_ancestry = 0

    for item in mms_raw:
        code = item["code"]
        title = item["title"]
        chapter = item.get("chapter", "")
        ancestors = get_ancestry(code, title, chapter)
        if ancestors:
            found_ancestry += 1

        enriched.append({
            "code": code,
            "title": title,
            "chapter": chapter,
            "leaf": item.get("leaf", False),
            "residual": item.get("residual", False),
            "depth": item.get("depth", 0),
            "ancestors": ancestors
        })

    print(f"Enriched {len(enriched)} codes. {found_ancestry} / {len(enriched)} ({found_ancestry/len(enriched)*100:.1f}%) have hierarchical ancestry.")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=1, ensure_ascii=False)
    print(f"Saved enriched codes to {out_path}")

if __name__ == "__main__":
    build()
