<div align="center">
  <br>
  <pre style="font-size: 1.2em; font-weight: bold; background: #0d1117; color: #58a6ff; padding: 1.2em 0; border-radius: 8px; letter-spacing: 0.15em">
██████╗ ██╗ ██████╗ ██████╗  █████╗  ██████╗
██╔══██╗██║██╔═══██╗██╔══██╗██╔══██╗██╔════╝
██████╔╝██║██║   ██║██████╔╝███████║██║  ███╗
██╔══██╗██║██║   ██║██╔══██╗██╔══██║██║   ██║
██████╔╝██║╚██████╔╝██║  ██║██║  ██║╚██████╔╝
╚═════╝ ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝
  </pre>

  <h3 align="center" style="margin-top: 0; color: #e6edf3;">
    Biomedical Agentic RAG — Autonomous Research Assistant
  </h3>

  <p align="center">
    <em>Final Year PG Project · Data Science & Bioinformatics</em>
  </p>

  <p align="center">
    <a href="https://www.python.org/downloads/">
      <img src="https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white&style=flat-square" alt="Python">
    </a>
    <a href="https://fastapi.tiangolo.com">
      <img src="https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white&style=flat-square" alt="FastAPI">
    </a>
    <a href="https://react.dev">
      <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white&style=flat-square" alt="React">
    </a>
    <a href="https://langchain-ai.github.io/langgraph/">
      <img src="https://img.shields.io/badge/LangGraph-0.1.19-1C3C3C?logo=langchain&logoColor=white&style=flat-square" alt="LangGraph">
    </a>
    <a href="https://www.trychroma.com/">
      <img src="https://img.shields.io/badge/ChromaDB-0.5.0-FC6E6E?logo=chroma&logoColor=white&style=flat-square" alt="ChromaDB">
    </a>
    <a href="https://opensource.org/licenses/MIT">
      <img src="https://img.shields.io/badge/License-MIT-A31F34?style=flat-square" alt="License">
    </a>
  </p>

  <br>
</div>

---

##  Overview

BioRAG is an **autonomous biomedical research agent** that retrieves drug–gene–disease relationships from local documents and live scientific APIs, self-corrects when evidence is weak, and synthesizes grounded answers using a **Gemini-powered LangGraph pipeline**. It also features a separate **Incognito mode** for unrestricted general-purpose chat via OpenRouter's free Gemma 4 model.

> **Built for researchers, by researchers.** Ask complex biomedical questions in natural language and get cited, evidence-backed answers.

---

##  Key Capabilities

| Area | Features |
|------|----------|
| ** Retrieval** | ChromaDB vector search (PubMedBERT) → FlashRank cross-encoder reranking → token optimization |
| ** Reasoning** | LangGraph agent with self-correction loop (up to 3 rephrasing attempts) |
| ** Live APIs** | PubMed (NCBI Entrez), UniProt REST, Open Targets GraphQL |
| ** Security** | Prompt injection / jailbreak / out-of-scope input guardrails + hallucination output guardrails |
| ** Resilience** | Graceful API failover — returns raw chunks + PubMed results on LLM failure |
| ** Document Management** | Dynamic CRUD — add, update, delete documents without full index rebuild |
| ** Evaluation** | Built-in RAGAS scoring (faithfulness, relevancy, recall, precision) |
| ** Incognito Chat** | Unrestricted general-purpose chat via OpenRouter (Gemma 4 free tier) — no guardrails, no RAG |
| ** Dashboard** | 6-tab React UI: Query, Incognito, Documents, Reasoning Trace, Evaluation, Settings |
| ** Export** | Multi-page PDF report generation |

---

##  Architecture

### Query Pipeline

```
                        ┌──────────────────────────┐
                        │     USER QUERY           │
                        └──────────┬───────────────┘
                                   │
                                   ▼
                        ┌──────────────────────────┐
                        │   INPUT GUARDRAIL        │
                        │  (injection / jailbreak  │
                        │   / out-of-scope check)  │
                        └──────┬──────────┬───────┘
                               │ blocked  │ passed
                               ▼          ▼
                        Blocked    ┌──────────────────────────┐
                        response   │   RETRIEVE (ChromaDB)    │
                                   │   k=15, PubMedBERT      │
                                   └──────────┬───────────────┘
                                              ▼
                                   ┌──────────────────────────┐
                                   │   RERANK (FlashRank)     │
                                   │   cross-encoder → top 5  │
                                   └──────────┬───────────────┘
                                              ▼
                                   ┌──────────────────────────┐
                                   │   TOKEN OPTIMIZE         │
                                   │   clean · truncate 300   │
                                   │   cosine dedup           │
                                   └──────────┬───────────────┘
                                              ▼
                                   ┌──────────────────────────┐
                                   │   EVALUATE (Gemini)      │
                                   │   evidence sufficiency   │
                                   └──┬───────┬───────┬──────┘
                                      │       │       │
                          sufficient  │  needs │  in-  │
                                      │  tools │ suff. │
                                      ▼        ▼       ▼
                                   ┌────┐ ┌────────┐ ┌──────────┐
                                   │SYN-│ │TOOL    │ │SELF-     │
                                   │THE-│ │CALL    │ │CORRECT   │
                                   │SIZE│ │PubMed  │ │(rephrase │
                                   │    │ │UniProt │ │×3 max)   │
                                   │    │ │OpenTar.│ │          │
                                   └──┬─┘ └──┬─────┘ └──────────┘
                                      │      │
                                      └──┬───┘
                                         ▼
                              ┌──────────────────────┐
                              │  OUTPUT GUARDRAIL    │
                              │  hallucination check │
                              └──────┬───────────────┘
                                     │
                          ┌──────────┴──────────┐
                          │                     │
                      grounded             unverified
                          │                     │
                       Return               Return +
                       answer               warning flag

    On any LLM API failure at any step:
    └── [FAILOVER] → raw chunks + PubMed results + warning
```

### Incognito Mode (Parallel Path)

```
    ┌──────────────────────────────────────┐
    │           INCognito MODE            │
    │  User Message → OpenRouter → Gemma 4 │
    │  No guardrails · No RAG · Any topic  │
    └──────────────────────────────────────┘
```

---

##  Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **LLM (Query)** | `gemini-2.0-flash-lite` | Core RAG reasoning & synthesis |
| **LLM (Incognito)** | `google/gemma-4-26b-a4b-it` via OpenRouter | Free unrestricted chat |
| **Agent Framework** | `LangGraph 0.1.19` | State machine orchestration |
| **Vector Store** | `ChromaDB 0.5.0` | Document embeddings & retrieval |
| **Embeddings** | `pritamdeka/S-PubMedBert-MS-MARCO` | Biomedical semantic search |
| **Reranker** | `FlashRank` | Cross-encoder precision reranking |
| **Literature API** | `BioPython Entrez` | PubMed literature search |
| **Protein API** | `UniProt REST` | Protein function & disease associations |
| **Drug–Disease API** | `Open Targets GraphQL` | Drug–gene–disease relationships |
| **Backend API** | `FastAPI 0.111` (port 8742) | REST endpoints |
| **Frontend** | `React 19` + `Vite` (port 5173) | 6-tab dashboard |
| **NLP** | `spaCy` + `scispaCy` | Biomedical text processing |
| **PDF Export** | `ReportLab` | Multi-page report generation |
| **Evaluation** | `RAGAS` | Automated metric scoring |

---

##  Quick Start

<details open>
<summary><strong>1. Prerequisites</strong></summary>

- Python **3.10** or **3.11**
- Node.js **18+** (for frontend only)
- Git

</details>

<details>
<summary><strong>2. Clone & set up virtual environment</strong></summary>

```bash
git clone <your-repo-url>
cd agentic_rag
python -m venv venv

# Windows
venv\Scripts\activate
# Mac / Linux
# source venv/bin/activate

pip install -r requirements.txt
```

</details>

<details>
<summary><strong>3. Download biomedical NLP model</strong></summary>

```bash
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_sm-0.5.4.tar.gz
```

</details>

<details>
<summary><strong>4. Configure environment</strong></summary>

```bash
cp .env.example .env
```

Then edit `.env` with your API keys. At minimum you need:
- `GOOGLE_API_KEY` — from [Google AI Studio](https://aistudio.google.com/apikey)
- `OPENROUTER_API_KEY` — from [OpenRouter](https://openrouter.ai/keys) *(for Incognito mode)*

See the [Configuration](#-configuration) section for all options.

</details>

<details>
<summary><strong>5. Ingest documents (optional)</strong></summary>

Place biomedical PDFs or TXT files into `data/documents/`, then:

```bash
python -c "from app.rag.retriever import ingest_documents; ingest_documents('./data/documents')"
```

The agent also works without local documents — it falls through to live PubMed/UniProt automatically.

</details>

<details>
<summary><strong>6. Launch the backend</strong></summary>

```bash
python main.py
```

| Resource | URL |
|----------|-----|
| API Server | [http://localhost:8742](http://localhost:8742) |
| Interactive Docs | [http://localhost:8742/docs](http://localhost:8742/docs) |

</details>

<details>
<summary><strong>7. Launch the frontend (optional)</strong></summary>

```bash
cd frontend
npm install
npm run dev
```

Dashboard at [http://localhost:5173](http://localhost:5173) — auto-proxies API calls to port 8742.

</details>

---

##  Configuration

All settings are read from a `.env` file in the project root.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | **Yes** | — | Gemini API key ([get one](https://aistudio.google.com/apikey)) |
| `GOOGLE_MODEL` | No | `gemini-2.0-flash-lite` | Gemini model for the Query pipeline |
| `OPENROUTER_API_KEY` | No | — | OpenRouter key for Incognito mode ([get one](https://openrouter.ai/keys)) |
| `TAVILY_API_KEY` | No | — | Tavily web search API key |
| `ENTREZ_EMAIL` | No | `researcher@university.edu` | Email for NCBI/PubMed API |
| `ENTREZ_API_KEY` | No | — | NCBI API key (increases rate limits) |
| `CHROMA_DB_PATH` | No | `./data/chroma_db` | Vector store directory |
| `CHROMA_COLLECTION_NAME` | No | `biomedical_docs` | ChromaDB collection name |
| `EMBEDDING_MODEL` | No | `pritamdeka/S-PubMedBert-MS-MARCO` | Sentence-transformer model |
| `MAX_DOCUMENTS_PER_QUERY` | No | `5` | Top-k documents for synthesis |
| `RELEVANCE_THRESHOLD` | No | `0.75` | Minimum relevance score |
| `SELF_CORRECTION_ATTEMPTS` | No | `3` | Max query rephrasing attempts |
| `API_HOST` | No | `0.0.0.0` | FastAPI bind address |
| `API_PORT` | No | `8742` | FastAPI port |

---

##  API Reference

All endpoints serve from `http://localhost:8742`.

###  Query — Main RAG Pipeline
```bash
curl -X POST http://localhost:8742/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What genes are implicated in both Alzheimer disease and Type 2 Diabetes?",
    "include_reasoning": true,
    "offline": false
  }'
```

###  Incognito — Unrestricted Chat
```bash
curl -X POST http://localhost:8742/incognito \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Explain quantum computing in simple terms"}
    ]
  }'
```

###  Document Upload
```bash
curl -X POST http://localhost:8742/documents/upload \
  -F "file=@paper.pdf" \
  -F "doc_id=my_paper"
```

###  Document Delete
```bash
curl -X DELETE http://localhost:8742/documents/my_paper
```

###  Document Update
```bash
curl -X PUT http://localhost:8742/documents/my_paper \
  -F "file=@paper_v2.pdf"
```

###  List Documents
```bash
curl http://localhost:8742/documents
```

###  Bulk Ingest
```bash
curl -X POST http://localhost:8742/ingest \
  -H "Content-Type: application/json" \
  -d '{"source_dir": "./data/documents"}'
```

###  Run Evaluation
```bash
curl -X POST http://localhost:8742/evaluate
```

###  Export PDF Report
```bash
curl -X POST http://localhost:8742/export/pdf \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Alzheimer genes",
    "answer": "APOE, BIN1, CLU, PICALM, CR1..."
  }'
```

###  Health Check
```bash
curl http://localhost:8742/health
```

---

##  Incognito Mode

The **Incognito** tab is a completely separate chat environment — no biomedical RAG, no guardrails, no domain restrictions.

| Capability | Details |
|-----------|---------|
| **Model** | `google/gemma-4-26b-a4b-it:free` via OpenRouter |
| **Context** | 262K tokens |
| **Features** | Markdown rendering, file upload (.txt, .csv, .json, .py, images), voice input |
| **Limits** | OpenRouter free tier: 50 req/day total |
| **Latency** | ~5–7s on free tier (queue) |

> **Speed tip:** Add a $10 one-time top-up to your OpenRouter account to get priority queue access (~1,000 req/day).

---

##  Dynamic CRUD

Documents can be managed **without rebuilding** the entire ChromaDB index.

| Operation | Description |
|-----------|-------------|
| **Add** | Upload PDF/TXT → chunk → embed → store in ChromaDB |
| **Update** | Delete old chunks → ingest new version |
| **Delete** | Remove all chunks for a given `doc_id` |
| **List** | View all documents with chunk counts |

---

##  Security — Guardrails

### Input Guardrail
Blocks before any LLM call is made:
-  **Prompt injection** — "Ignore previous instructions..."
-  **Jailbreak attempts** — "You are now DAN..."
-  **Out-of-scope** — non-biomedical queries
-  **Length violations** — empty or excessively long queries

```bash
# Try it — this will be blocked
curl -X POST http://localhost:8742/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the best recipe for chocolate cake?"}'
# → {"blocked": true, ...}
```

### Output Guardrail
Gemini re-verifies each claim in the synthesized answer against the retrieved chunks. If hallucination is detected, the response carries a `guardrail_warning` field.

---

##  Resilience — API Failover

If any Gemini API call fails at any stage (rate limit, auth error, network timeout):

1. Exception is caught and logged
2. Pipeline returns **raw retrieved chunks** + **PubMed fallback results**
3. Response includes `"fallback": true` + a human-readable warning
4. **Zero crashes** — the system never dies from an API error

---

##  Evaluation

Built-in [RAGAS](https://docs.ragas.io/) evaluation using Gemini-based scoring on a standard set of 5 biomedical questions.

### Current Results

```json
{
  "faithfulness":      0.644,
  "answer_relevancy":  0.532,
  "context_recall":    0.608,
  "context_precision": 0.608,
  "num_questions":     5
}
```

| Metric | Measures | Score |
|--------|----------|-------|
| **Faithfulness** | Is the answer grounded in retrieved evidence? | 0.644 |
| **Answer Relevancy** | Does the answer address the question? | 0.532 |
| **Context Recall** | Did retrieval find the relevant information? | 0.608 |
| **Context Precision** | Is retrieved context focused (low noise)? | 0.608 |

### Run It Yourself
```bash
python -m app.eval.ragas_eval
```
Results saved to `eval_results.json`.

---

##  Sample Queries

Copy-paste these into the Query tab:

```
What genes are associated with Alzheimer's disease?
What is the mechanism of BRCA1 in DNA damage repair?
Which drugs target the EGFR pathway in lung cancer?
What is the relationship between insulin resistance and Type 2 Diabetes?
What proteins are involved in the p53 tumor suppressor pathway?
How does PTEN loss contribute to cancer progression?
```

---

##  Project Structure

```
agentic_rag/
├── app/                           # Python backend
│   ├── agent/
│   │   └── graph.py               # LangGraph state machine
│   ├── rag/
│   │   ├── retriever.py           # ChromaDB ingestion & search
│   │   ├── reranker.py            # FlashRank + token optimization
│   │   └── crud.py                # Dynamic document CRUD
│   ├── tools/
│   │   └── biomedical_tools.py    # PubMed, UniProt, Open Targets
│   ├── api/
│   │   └── routes.py              # FastAPI endpoints
│   ├── eval/
│   │   └── ragas_eval.py          # RAGAS evaluation
│   ├── incognito.py               # Unrestricted OpenRouter chat
│   ├── guardrails.py              # Input / output security
│   ├── failover.py                # Graceful API failover
│   ├── pdf_report.py              # PDF report generation
│   └── config.py                  # Pydantic Settings
├── frontend/                      # React + Vite dashboard
│   └── src/
│       ├── App.jsx                # Root (6-tab navigation)
│       ├── api/index.js           # API client
│       └── components/
│           ├── Query/             # Query panel
│           ├── Incognito/         # Incognito chat
│           ├── Documents/         # Document management
│           ├── Trace/             # Reasoning trace
│           ├── Eval/              # Evaluation panel
│           └── Settings/          # Settings panel
├── data/
│   ├── documents/                 # Your PDFs / TXTs go here
│   └── chroma_db/                 # Vector store (auto-created)
├── scripts/
│   ├── demo.py                    # Quick demo
│   └── ingest_cord19.py           # CORD-19 bulk ingestion
├── tests/
│   └── test_pipeline.py           # Unit tests
├── main.py                        # FastAPI entry point
├── requirements.txt
├── .env.example
└── .gitignore
```

---

##  Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| `ModuleNotFoundError` | Missing dependencies | Run `pip install -r requirements.txt` in your activated venv |
| `401` on Gemini API | Invalid API key | Check `GOOGLE_API_KEY` in `.env`. Get a new key at [aistudio.google.com](https://aistudio.google.com/apikey) |
| `401` on OpenRouter | Invalid API key | Check `OPENROUTER_API_KEY` in `.env`. Get a key at [openrouter.ai/keys](https://openrouter.ai/keys) |
| `429 Too Many Requests` | Rate limit exceeded | Use a paid API tier or wait. For OpenRouter, add a $10 top-up. |
| Empty retrieval results | No documents ingested | Run `python -c "from app.rag.retriever import ingest_documents; ingest_documents()"` |
| Slow first query | Downloading embedding model | First run downloads ~400MB PubMedBERT. Cached afterwards. |
| Incognito ~5–7s latency | Free tier queue | Add $10 top-up to OpenRouter for priority access |
| PubMed rate limit | No API key | Add `ENTREZ_API_KEY` to `.env` for higher limits |
| Frontend can't reach backend | Server not started | Ensure `python main.py` is running on port 8742 |

---

##  License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

---

<div align="center">
  <sub>
    Built with Python, React, LangGraph, ChromaDB &middot;
    Powered by Google Gemini &amp; OpenRouter
  </sub>
</div>
