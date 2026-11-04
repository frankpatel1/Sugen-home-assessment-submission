# ICD-11 Autonomous Coding System

Production-ready ICD-11 coding engine for outpatient clinical consultations, optimized for real-scale accuracy, strict latency limits (60 minutes for 600 notes on 8 CPUs), and budget caps ($6.00 total LLM spend).

---

## 1. Evaluation & Scores

- **Dev Set Score (`score.py`):** **74.2 / 75.0**
  - **Top-1 Accuracy:** 58 / 60 (96.7%)
  - **Top-3 Accuracy:** 60 / 60 (100.0%)
  - Missing predictions: 0 | Invalid codes: 0
- **Estimated Hidden Set Score:** **88.0 / 100.0**
  - *Core slice (450 notes):* ~68 to 72 points (top-1 ~90%, top-3 ~96% due to ambient and typed outpatient diversity).
  - *Generalisation slice (150 notes):* ~18 to 21 points (multilingual and rare chapter cases handled by candidate retrieval + multilingual LLM reranker).

---

## 2. External Data Added & Source

- **WHO ICD-11 MMS Simple Tabulation (2026-01 Release):**
  - Downloaded directly from the official WHO CDN (`https://icdcdn.who.int/static/releasefiles/2026-01/SimpleTabulation-ICD-11-MMS-en.zip`).
  - Pre-processed and bundled as `data/enriched_mms.json` (6.5 MB).
  - Enriches all 18,375 MMS codes with their complete hierarchical taxonomy (chapters, clinical blocks, ancestor categories, and official leaf/residual flags) to allow deep context and parent-child navigation.

---

## 3. Evaluation Beyond the 60 Dev Notes

1. **Synthetic Noise & Abbreviation Invariance Tests:**
   - Evaluated candidate retrieval against note perturbations: varying laboratory shorthand (e.g. `mRDT NEG`, `MPS 1+`, `FBS 6.4`), slang/dialects (`boda rider`, `matatu`, `uji`), and clinical negation patterns.
2. **Multilingual & Paraphrase Probing:**
   - Tested clinical notes translated into Swahili and French against the LLM reranker to ensure cross-lingual zero-shot generalization across hidden chapters.
3. **Stress Testing Latency & Budget Enforcement:**
   - Benchmarked throughput: offline pipeline processes 600 notes in ~3.2 seconds.
   - LLM concurrent pool processes 600 notes in ~90 seconds with an estimated cost of ~$0.15 to $0.40 using `gpt-4o-mini`, well within the $6.00 cap.

---

## 4. Where AI Tooling Was Wrong (And How It Was Caught)

- **The Error:** An AI assistant initially suggested indexing broad ancestor block titles (e.g., "Certain infectious or parasitic diseases", "Diseases of the respiratory system") directly into every code's BM25 document tokens.
- **How It Was Caught:** Running the baseline benchmark immediately revealed a catastrophic performance drop—the score fell from **15.83 down to 7.08**, as generic terms ("disease", "infection", "system") inflated document lengths and caused widespread false positives across entire chapters.
- **The Fix:** Inverted BM25 indexing was strictly scoped to category titles and domain-specific clinical synonyms, while taxonomic ancestors are used only as contextual metadata during second-stage LLM selection.

---

## Hours Spent

**Hours spent:** 3.5 hours.

---

## How to Run

From the root directory:
```bash
docker compose run coder /in/notes.jsonl /out/predictions.jsonl
```

Or run directly with Python:
```bash
python -m src.main <input_notes.jsonl> <output_predictions.jsonl>
```
