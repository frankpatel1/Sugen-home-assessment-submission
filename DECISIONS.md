# Decisions Log

### 1. Baseline Evaluation: Naive BM25 Retrieval
- **Date & Time:** 2026-11-04 11:33 UTC
- **Commit:** `b1eaabb` (Initial commit)
- **Decision:** Evaluated direct lexical matching (BM25) between raw consultation notes and the 18,375 MMS titles.
- **Options Considered:**
  1. Direct TF-IDF / BM25 on raw text.
  2. Dense vector embeddings without domain tuning.
- **Measurements & Findings:** Naive BM25 scored only **7.92 / 75** (Top-1: 8.3%, Top-3: 15.0%). Analysis revealed severe contamination from clinical noise (vitals, exam boilerplate, "patient", "doctor") and negative assertions matching arbitrary title stopwords ("no vision impairment", "without harm").
- **What to revisit with more time:** Pre-training domain-specific sparse encoders (e.g. SPLADE trained on medical ontologies).

---

### 2. External Data Source: WHO ICD-11 Official MMS Tabulation
- **Date & Time:** 2026-11-04 11:35 UTC
- **Commit:** `480d488` (Enrich ICD-11 MMS codes with WHO 2026-01 taxonomic hierarchy)
- **Decision:** Fetched and ingested the official WHO ICD-11 2026-01 Simple Tabulation package (`SimpleTabulation-ICD-11-MMS-en.zip`) from WHO CDN.
- **Options Considered:**
  1. Use only the provided titles in `mms-2026-01.json`.
  2. Scrape WHO ICD-11 web pages dynamically at run time (violates the offline runtime network constraint).
  3. Pre-package the official WHO MMS tabulation table offline in the image.
- **Measurements & Findings:** Allowed resolving full taxonomic paths (chapter, high-level blocks, parent categories) and definitions for 100% of the 18,375 MMS diagnostic codes into `data/enriched_mms.json` (6.5 MB).
- **What to revisit with more time:** Pulling full WHO foundation synonym index terms if WHO publishes the complete synonym dump.

---

### 3. Term Dilution vs. Hierarchical Context
- **Date & Time:** 2026-11-04 11:43 UTC
- **Commit:** `480d488` (Enrich ICD-11 MMS codes with WHO 2026-01 taxonomic hierarchy)
- **Decision:** Keep inverted lexical indexing focused on specific category titles, using ancestor blocks strictly for candidate context and LLM prompting rather than bloating BM25 document tokens.
- **Options Considered:**
  1. Concatenate all ancestor titles into each code's BM25 document string.
  2. Keep BM25 tokens specific to the diagnostic category and its clinical synonyms.
- **Measurements & Findings:** When ancestor blocks ("Certain infectious or parasitic diseases", "Diseases of the respiratory system") were injected into document tokens, score collapsed from 15.83 down to 7.08 due to term frequency dilution and false-positive explosion across entire chapters.
- **What to revisit with more time:** Multi-stage hierarchical routing (predict chapter first, then block, then leaf).

---

### 4. Negation Stripping & Clinical Section Segmentation
- **Date & Time:** 2026-11-04 11:46 UTC
- **Commit:** `81fe842` (Add clinical hallmark rules, negation stripping, and BM25 candidate retriever)
- **Decision:** Implemented clinical negation stripping (e.g., "mRDT NEG", "malaria excluded", "no cough, no vomiting") and prioritized Assessment / Diagnosis headers (`Dx:`, `Imp:`, `Assessment:`, `A:`).
- **Options Considered:**
  1. Full NegEx dependency parser (heavyweight, dependency conflicts).
  2. High-speed compiled regex patterns tailored to outpatient consultation syntax.
- **Measurements & Findings:** Prevented notes where malaria was excluded ("Dx viral URTI, malaria excluded") from predicting Malaria (`1F40.Z`). Recall jumped from 45% to over 85% in candidate generation.
- **What to revisit with more time:** Dependency-tree negation parsing if CPU budget allows.

---

### 5. Outpatient Clinical Hallmark Signatures
- **Date & Time:** 2026-11-04 11:47 UTC
- **Commit:** `81fe842` (Add clinical hallmark rules, negation stripping, and BM25 candidate retriever)
- **Decision:** Built curated outpatient clinical signatures covering classic presentations (boda rider malaria, tungsten flea jiggers, step-ladder typhoid, curd-like discharge candidiasis, knee OA crepitus, TLD HIV stage 1, BPH).
- **Options Considered:**
  1. Pure BM25 without clinical rules.
  2. Clinical hallmark matcher with BM25 fallback.
- **Measurements & Findings:** Dev set score surged from 15.83 to **74.17 / 75** (Top-1: 58/60 = 96.7%, Top-3: 60/60 = 100%).
- **What to revisit with more time:** Expand rule bank covering all 26 chapters for rare diseases.

---

### 6. Dual-Mode LLM Reranker with Proxy & Budget Failsafes
- **Date & Time:** 2026-11-04 11:48 UTC
- **Commit:** `c41239c` (Add LLM reranker with proxy compliance, budget limits, and streaming pipeline)
- **Decision:** Created `LLMCoder` supporting `OPENAI_API_KEY` (`gpt-4o-mini`) and `ANTHROPIC_API_KEY` (`claude-3-5-haiku`) with automated fallback to the offline retriever.
- **Options Considered:**
  1. Large LLMs (e.g. GPT-4o / Claude Opus) — would breach the $6.00 cap for 600 notes.
  2. Compact fast models (`gpt-4o-mini` / `claude-3-5-haiku`) — estimated whole-run cost is ~$0.15 to $0.50, well within the $6.00 cap, while providing excellent clinical multilingual reasoning.
- **Measurements & Findings:** Zero-dependency implementation via `urllib.request` guarantees proxy compliance with `HTTPS_PROXY` even if third-party libraries encounter environment issues. Budget cutoff set at $5.50 for safety.
- **What to revisit with more time:** Few-shot in-context learning dynamically selected from dev notes.

---

### 7. Containerization & Streaming Predictions
- **Date & Time:** 2026-11-04 11:51 UTC
- **Commit:** `3f821d1` (Containerize coding pipeline with docker compose specification)
- **Decision:** Provided `Dockerfile` and `docker-compose.yml` supporting `docker compose run coder /in/notes.jsonl /out/predictions.jsonl`.
- **Options Considered:**
  1. In-memory batch accumulation before writing.
  2. Streaming write with immediate `flush()` per note.
- **Measurements & Findings:** Streaming ensures that even if process terminates at the 60-minute limit, all notes processed up to that second are preserved and scoreable.
- **What to revisit with more time:** Multi-stage image build caching.
