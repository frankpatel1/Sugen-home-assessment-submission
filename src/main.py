"""Main entrypoint for ICD-11 coding system.

Usage:
    python -m src.main <input_notes.jsonl> <output_predictions.jsonl>
Or via Docker:
    docker compose run coder /in/notes.jsonl /out/predictions.jsonl
"""
import sys
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.retriever import ICD11Retriever
from src.llm import LLMCoder

def process_single_note(note, retriever, llm_coder):
    note_id = note.get("id")
    note_text = note.get("text", "")
    candidates = retriever.get_candidates(note_text, top_k=25)

    if llm_coder.is_available():
        try:
            codes = llm_coder.predict_note(
                note_id=note_id,
                note_text=note_text,
                candidates=candidates,
                valid_codes=retriever.valid_codes
            )
        except Exception:
            codes = retriever.predict_offline(note_text)
    else:
        codes = retriever.predict_offline(note_text)

    # Sanity verification
    clean_codes = []
    for c in codes:
        if c in retriever.valid_codes and c not in clean_codes:
            clean_codes.append(c)
        if len(clean_codes) >= 3:
            break

    # If empty, backfill with default valid codes
    if not clean_codes:
        for c in [c["code"] for c in candidates]:
            if c in retriever.valid_codes and c not in clean_codes:
                clean_codes.append(c)
            if len(clean_codes) >= 3:
                break

    return {"id": note_id, "codes": clean_codes[:3]}

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input_notes.jsonl> <output_predictions.jsonl>", file=sys.stderr)
        sys.exit(1)

    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    print(f"[coder] Starting ICD-11 coding pipeline...")
    print(f"[coder] Input:  {in_path}")
    print(f"[coder] Output: {out_path}")
    t0 = time.time()

    if not in_path.exists():
        sys.exit(f"Input file not found: {in_path}")

    # Ensure parent output directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize components
    retriever = ICD11Retriever()
    llm_coder = LLMCoder(budget_cap=5.50)

    print(f"[coder] Valid MMS codes loaded: {len(retriever.valid_codes)}")
    print(f"[coder] LLM provider active: {llm_coder.provider if llm_coder.is_available() else 'None (offline mode)'}")

    # Read notes
    notes = []
    with open(in_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    notes.append(json.loads(line))
                except Exception as e:
                    print(f"[coder] Warning: skipping invalid json line: {e}", file=sys.stderr)

    total_notes = len(notes)
    print(f"[coder] Read {total_notes} notes to process.")

    # Process notes and write predictions streaming
    processed = 0
    with open(out_path, "w", encoding="utf-8") as out_f:
        if llm_coder.is_available() and total_notes > 1:
            # Parallel processing with ThreadPoolExecutor
            num_workers = min(10, total_notes)
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = {executor.submit(process_single_note, n, retriever, llm_coder): n["id"] for n in notes}
                for fut in as_completed(futures):
                    res = fut.result()
                    out_f.write(json.dumps(res, ensure_ascii=False) + "\n")
                    out_f.flush()
                    processed += 1
                    if processed % 50 == 0 or processed == total_notes:
                        print(f"[coder] Progress: {processed}/{total_notes} (Cost: ${llm_coder.total_cost:.4f})")
        else:
            # Sequential processing (fast offline mode)
            for n in notes:
                res = process_single_note(n, retriever, llm_coder)
                out_f.write(json.dumps(res, ensure_ascii=False) + "\n")
                out_f.flush()
                processed += 1
                if processed % 100 == 0 or processed == total_notes:
                    print(f"[coder] Progress: {processed}/{total_notes}")

    elapsed = time.time() - t0
    print(f"[coder] Completed {processed} predictions in {elapsed:.2f}s.")
    if llm_coder.calls_count > 0:
        print(f"[coder] LLM calls: {llm_coder.calls_count}, Fallbacks: {llm_coder.fallback_count}, Total cost: ${llm_coder.total_cost:.4f}")
    print(f"[coder] Output written to {out_path}")

if __name__ == "__main__":
    main()
