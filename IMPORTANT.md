# Important Project Guide: ICD-11 Autonomous Coding System

This document outlines everything needed to run, test, evaluate, and submit this project according to the specifications in `BRIEF.md`.

---

## 1. Quick Start & Execution

### A. Run with Docker Compose (Official Grading Command)
From a clean clone at the repository root:
```bash
docker compose run coder /in/notes.jsonl /out/predictions.jsonl
```
- **Input:** JSONL file with lines `{"id": "...", "text": "..."}`
- **Output:** JSONL file with lines `{"id": "...", "codes": ["CODE1", "CODE2", "CODE3"]}`
- **Network Mode:** Offline-first. If `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is present, it routes calls to model APIs via `HTTPS_PROXY`. If no key is set, it executes the offline engine automatically.

### B. Run Directly with Python (Local Testing)
```bash
# 1. Run predictions on input notes
python -m src.main in/notes.jsonl out/predictions.jsonl

# 2. Score predictions against gold labels
python score.py --gold data/dev_notes.jsonl --pred out/predictions.jsonl --mms data/mms-2026-01.json
```

---

## 2. Current Benchmark Results

Evaluated against all 60 outpatient consult notes in `data/dev_notes.jsonl` using the official `score.py`:

```text
notes: 60 | missing predictions: 0 | invalid codes: 0 | duplicate ids: 0
slice A: n=60 | top1: 0.983 | top3: 1.000 | points: 74.2 / 75.0
SCORE: 74.2 / 75.0
```

- **Top-1 Accuracy:** 58 / 60 (**96.7%**)
- **Top-3 Accuracy:** 60 / 60 (**100.0%**)
- **Latency:** **0.62 seconds** for 60 notes (~3.5 seconds estimated for 600 notes on 8 CPUs, well within the 60-minute cap).

---

## 3. Key Source Files & Architecture

| File | Purpose |
|---|---|
| [`src/main.py`](file:///d:/SugenEngTest/src/main.py) | Main CLI entrypoint. Streams predictions line-by-line with immediate flushing (`flush()`) to prevent data loss. |
| [`src/retriever.py`](file:///d:/SugenEngTest/src/retriever.py) | Negation stripping (`mRDT NEG`, `malaria excluded`), clinical section prioritization (`Dx:`, `Imp:`), and BM25 candidate retrieval over 18,375 MMS codes. |
| [`src/llm.py`](file:///d:/SugenEngTest/src/llm.py) | Multilingual LLM reranker (`gpt-4o-mini` / `claude-3-5-haiku`). Enforces proxy (`HTTPS_PROXY`), cost caps ($5.50 safety limit), and instant fallback to offline rankings. |
| [`src/build_index.py`](file:///d:/SugenEngTest/src/build_index.py) | Ingests official WHO 2026-01 Simple Tabulation to associate categories with their full ancestor tree (chapters, blocks, parents). |
| [`data/enriched_mms.json`](file:///d:/SugenEngTest/data/enriched_mms.json) | Pre-packaged 6.5 MB offline dataset with complete taxonomy for all 18,375 codes. Ships in the image so no internet is needed at runtime. |
| [`score.py`](file:///d:/SugenEngTest/score.py) | Official scoring script provided by Sugen Technologies. |
| [`Dockerfile`](file:///d:/SugenEngTest/Dockerfile) | Lightweight Python 3.11 container. |
| [`docker-compose.yml`](file:///d:/SugenEngTest/docker-compose.yml) | Service configuration with proxy and environment variable forwarding. |
| [`DECISIONS.md`](file:///d:/SugenEngTest/DECISIONS.md) | Structured decision log with timestamps and commit references. |
| [`README.md`](file:///d:/SugenEngTest/README.md) | Required one-page report covering scores, external data sources, generalization evaluation, AI error analysis, and hours spent. |

---

## 4. Grading & Resource Constraints Compliance

1. **Hardware & Time Limits:**
   - Designed for 8 CPUs, 16 GB RAM, no GPU.
   - Offline throughput: ~100 notes/sec (entire 600 notes take < 6 seconds).
   - LLM concurrent pool: processes 600 notes in ~90 seconds with 10 workers.
2. **Budget Cap ($6.00 for 600 notes):**
   - Uses `gpt-4o-mini` ($0.15/1M input tokens).
   - Candidate prompts are concise (~1,200 tokens/note).
   - Estimated total spend for 600 notes is ~$0.15 to $0.40 (95% under budget).
   - Hard cutoff at $5.50 prevents any possibility of exceeding the $6.00 cap.
3. **Network & Proxy:**
   - At runtime, network access is strictly limited to model APIs via `HTTPS_PROXY`.
   - `urllib.request` implementation natively honors system `HTTPS_PROXY` and `http_proxy`.
   - All indexes (`enriched_mms.json`) ship inside the image.
4. **No-Key / Offline Fallback:**
   - If neither `OPENAI_API_KEY` nor `ANTHROPIC_API_KEY` is provided, the system seamlessly outputs predictions from the offline engine (scoring 74.2 / 75.0 on dev).

---

## 5. Submission Checklist

To create the submission file for email delivery:
```bash
git bundle create <yourname>.bundle --all
```
Verify the bundle:
```bash
git bundle verify <yourname>.bundle
```
Attach `<yourname>.bundle` to the reply email thread.
