# Mutual Fund FAQ Chatbot (Groww × HDFC AMC)

A Retrieval-Augmented Generation (RAG) assistant that answers factual questions about select HDFC Mutual Fund schemes listed on Groww. The stack now uses OpenAI GPT‑4o for grounded answers, `text-embedding-3-small` vectors in Pinecone, and a React UI that enforces ≤3 sentence answers, cites a single official URL, and shows the “Last updated from sources: …” timestamp.

> **Working prototype:** run the backend on `http://127.0.0.1:8001` and the Vite frontend on `http://127.0.0.1:5173`. See setup instructions below.

## Scope
- **AMC:** HDFC Mutual Fund
- **Distribution Product:** Groww
- **Schemes covered today:**
  1. HDFC ELSS Tax Saver Fund Direct Plan Growth
  2. HDFC Flexi Cap Fund Direct Plan Growth (Groww equity slug)
  3. HDFC Large & Mid Cap Fund Direct Growth
  4. HDFC Small Cap Fund Direct Growth
  5. HDFC Multi Cap Fund Direct Growth
- **Help-center coverage:** Groww capital-gains statement guide

## Architecture Overview
1. **Data Pipeline (`data-pipeline/`)**
   - Scrapes Groww scheme/help URLs from `src/constants.py`
   - Cleans & chunks HTML via Docling fallback utilities
   - Stores documents/chunks in MongoDB (`mutual_fund_faq` DB) and upserts embeddings (dim 1536) into Pinecone index `mf-assistant-index`
2. **Backend (`backend/`)**
   - FastAPI + Uvicorn with lifespan-managed services
   - Advice guard (regex) blocks advisory/return/performance questions
   - Retriever → OpenAI client (embeddings + GPT‑4o chat) → citation selector → response schema `{answer, citations, method, last_updated, …}`
   - CORS enables `http://localhost:5173` and `http://127.0.0.1:5173`
3. **Frontend (`frontend/`)**
   - Vite + React + CSS modules
   - Centered card UI with example prompts, streaming-ready fetch, citation list, and disclaimer footer sourced from environment

## Getting Started
### Prerequisites
- Python 3.11+
- Node 20+
- MongoDB instance (local or Atlas)
- Pinecone account + index (`mf-assistant-index`, dim 1536)
- OpenAI API key with GPT‑4o + text-embedding-3-small access

### Environment variables
Create `.env` files at repo root for both backend and pipeline:

```
OPENAI_API_KEY=...
OPENAI_CHAT_MODEL=gpt-4o
OPENAI_EMBED_MODEL=text-embedding-3-small
PINECONE_API_KEY=...
PINECONE_INDEX=mf-assistant-index
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=mutual_fund_faq
MONGODB_COLLECTION_CHUNKS=chunks
ADVICE_REFUSAL_LINK=https://www.sebi.gov.in/sebiweb/investors/InvestorProtection.jsp
DISCLAIMER_TEXT="Facts-only. No investment advice."
```

Frontend `.env` (in `frontend/`):

```
VITE_BACKEND_URL=http://127.0.0.1:8001
```

### Run the data pipeline
```powershell
cd data-pipeline
python -m src.pipeline
```
This scrapes the URLs, stores raw docs, chunks + embeddings, and pushes vectors to Pinecone.

### Start the backend
```powershell
& venv\Scripts\Activate.ps1
python -m uvicorn backend.src.app:app --host 0.0.0.0 --port 8001
```

### Start the frontend
```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

### Smoke test
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8001/ask -Method POST \
  -Body (@{ query = "Exit load for HDFC Small Cap Fund?" } | ConvertTo-Json) \
  -ContentType "application/json"
```
The React UI automatically displays the same answer, final citation, and “Last updated …” line.

## Deliverables (checked into `docs/`)
- `docs/sources.csv` – canonical Groww URLs + timestamps
- `docs/sample_qna.md` – 5 sample questions/answers with links
- `docs/disclaimer.txt` – footer copy rendered in the UI
- Working prototype instructions (this README) for local execution

## Compliance Guardrails
- Public sources only – Groww scheme/help pages listed in `docs/sources.csv`
- Never store or request PII (PAN, Aadhaar, phone, email, OTP, etc.)
- No performance/return comparisons; the advice guard routes such queries to a refusal referencing SEBI
- Responses limited to ≤3 sentences, include one citation, and show “Last updated from sources: …”

## Known Limitations
- Pinecone + Mongo credentials expected via `.env`; no fallback if unset
- Streaming UI path is stubbed (fetch reads full response). Incremental streaming TBD
- Only the six Groww URLs listed are ingested today; new schemes require adding to `data-pipeline/src/constants.py` and rerunning the pipeline
- Prototype is local-only; deployment scripts (Railway/Vercel) not finalized
- Capital-gains statement article is static; Groww HTML structure changes may require scraper tweaks

## References
- Source list: `docs/sources.csv`
- Sample outputs: `docs/sample_qna.md`
- Disclaimer text: `docs/disclaimer.txt`

For any question not covered in the sources, the assistant responds with "I couldn’t find that fact …" and links back to Groww.
