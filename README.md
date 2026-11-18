# DocuMind AI

[![CI](https://github.com/keerthanan2211/documind-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/keerthanan2211/documind-ai/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Upload a PDF and ask questions about it in plain language. Answers come only from the document and cite the exact passages and page numbers they're based on, so you can check every claim.

Built with retrieval-augmented generation (RAG): **FastAPI · PostgreSQL + pgvector · Google Gemini · Next.js · TypeScript · Docker**

---

## Contents

- [Features](#features)
- [How it works](#how-it-works)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Environment variables](#environment-variables)
- [API reference](#api-reference)
- [Engineering decisions](#engineering-decisions)
- [Testing](#testing)
- [Deployment](#deployment)
- [Limitations and roadmap](#limitations-and-roadmap)

---

## Features

- **Upload PDFs** by drag and drop (up to 20 MB and 300 pages by default)
- **Background processing:** text extraction, chunking and embedding run after upload, while the UI shows live status
- **Ask in plain language,** with follow-up questions that use recent conversation context
- **Cited answers:** every claim links to a highlighted source excerpt with its page number
- **Honest "not found":** if nothing relevant is in the document, it says so instead of guessing, and doesn't call the model at all
- **Conversation history** saved per document
- **Clear failures:** scanned PDFs, password-protected files and damaged files each get a specific explanation
- **Storage options:** local disk for development, or AWS S3 (server-side encrypted) for production
- **Rate limiting** on uploads and questions, to protect your AI quota
- **Accessible UI:** keyboard friendly, labelled controls, live status updates for screen readers, and a highly legible typeface

---

## How it works

```mermaid
flowchart TB
    subgraph Ingest[Upload: runs once per document]
        U[PDF upload] --> S[(Local disk / S3)]
        S --> X[Extract text per page<br/>pypdf]
        X --> C[Split into overlapping passages<br/>keeps page numbers]
        C --> E[Embed passages<br/>Gemini embeddings]
        E --> V[(PostgreSQL + pgvector<br/>HNSW index)]
    end

    subgraph Ask[Question: runs per question]
        Q[Question] --> QE[Embed question]
        QE --> R[Find nearest passages<br/>cosine distance]
        V --> R
        R -->|relevant passages| P[Prompt: numbered sources<br/>+ recent chat + question]
        R -->|nothing relevant| NF[“I couldn’t find that”]
        P --> G[Gemini generates an answer<br/>citing sources as 1, 2…]
        G --> A[Answer + cited excerpts with page numbers]
    end
```

1. **Chunking.** Page text is split into passages of about 1,200 characters, breaking on paragraphs and sentences where possible, with a 200-character overlap so ideas spanning a boundary aren't lost. Each passage keeps its page number.
2. **Embedding.** Each passage becomes a 768-dimension vector that captures its meaning, stored in PostgreSQL with pgvector and indexed with HNSW for fast nearest-neighbour search.
3. **Retrieval.** The question is embedded the same way, and the 6 closest passages (by cosine distance) are retrieved. Passages beyond a distance cutoff are ignored as unrelated.
4. **Generation.** Gemini receives the numbered passages and a strict instruction to answer only from them and cite each claim like `[2]`.
5. **Citations.** The server returns only the sources the answer actually cited, each with its page and an excerpt. The UI turns `[2]` into a link to the highlighted excerpt.

---

## Tech stack

| Layer | Technology | Why |
| --- | --- | --- |
| API | FastAPI (Python 3.12) | Typed request validation, async uploads, automatic OpenAPI docs |
| Database | PostgreSQL 16 + pgvector | Vectors live next to relational data; one database to run |
| ORM | SQLAlchemy 2.0 | Typed models, and pgvector's `cosine_distance` in queries |
| AI | Google Gemini (`google-genai` SDK) | Embeddings and generation, with a free tier |
| PDF | pypdf | Pure-Python text extraction |
| Storage | Local disk or AWS S3 (boto3) | Same interface, swapped by config |
| Rate limiting | slowapi | Per-IP limits on the costly endpoints |
| Frontend | Next.js 14, TypeScript, Tailwind CSS | Fast, typed UI |
| Data fetching | TanStack React Query | Caching, and polling while documents process |
| Testing | pytest (real PostgreSQL + pgvector), Vitest | Integration tests with a fake AI provider |
| Quality | Ruff (lint + format), ESLint | Consistent, clean code |
| DevOps | Docker Compose, GitHub Actions | One-command stack, CI with a pgvector service |

---

## Project structure

```
documind/
├── backend/
│   ├── app/
│   │   ├── main.py              App factory, CORS, rate limiting, error handling
│   │   ├── config.py            Settings from environment variables
│   │   ├── db.py                Engine, sessions, pgvector setup
│   │   ├── models.py            Document, Chunk (vector + HNSW index), Message
│   │   ├── schemas.py           Request and response models
│   │   ├── routers/
│   │   │   ├── documents.py     Upload, list, get, delete, history
│   │   │   └── chat.py          Ask a question
│   │   └── services/
│   │       ├── pdf.py           Text extraction with clear error messages
│   │       ├── chunking.py      Page-aware, sentence-aware chunking with overlap
│   │       ├── ai.py            AIProvider interface + Gemini implementation
│   │       ├── ingest.py        Upload pipeline: extract → chunk → embed → store
│   │       ├── rag.py           Retrieval, prompt building, citation extraction
│   │       └── storage.py       Local and S3 storage
│   ├── tests/                   Unit + integration tests (pgvector, fake AI)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── app/                 Library page, document chat page
│       ├── components/          Upload zone, document list, chat, cited answer
│       └── lib/                 API client, citation parsing, types
├── .github/workflows/ci.yml
└── docker-compose.yml
```

---

## Getting started

You need a free **Gemini API key** from [Google AI Studio](https://aistudio.google.com/apikey).

### Option 1: Docker

```bash
git clone https://github.com/keerthanan2211/documind-ai.git
cd documind-ai
GEMINI_API_KEY=your-key docker compose up --build
```

Open **http://localhost:3000**. API docs are at http://localhost:8000/docs.

### Option 2: Run locally

**Prerequisites:** Python 3.12, Node.js 20, and PostgreSQL 16 with pgvector. The easiest way to get the database is:
`docker run -d -p 5432:5432 -e POSTGRES_USER=documind -e POSTGRES_PASSWORD=documind -e POSTGRES_DB=documind pgvector/pgvector:pg16`

**Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                 # then add your GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

Tables and the vector index are created automatically on startup.

**Frontend** (new terminal)

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev                          # http://localhost:3000
```

---

## Environment variables

### Backend (`backend/.env`)

| Variable | Default | Description |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://documind:documind@localhost:5432/documind` | PostgreSQL with pgvector |
| `GEMINI_API_KEY` | (none) | **Required.** Free at Google AI Studio |
| `GEMINI_CHAT_MODEL` | `gemini-2.5-flash` | Model used to write answers |
| `GEMINI_EMBED_MODEL` | `gemini-embedding-001` | Model used for embeddings |
| `EMBED_DIM` | `768` | Vector size. Changing it requires recreating the database. |
| `STORAGE_BACKEND` | `local` | `local` or `s3` |
| `LOCAL_STORAGE_DIR` | `./uploads` | Folder for local storage |
| `S3_BUCKET`, `AWS_REGION` | (none), `ap-south-1` | For S3 storage (credentials via standard AWS env vars or IAM role) |
| `MAX_UPLOAD_MB` / `MAX_PAGES` | `20` / `300` | Upload limits |
| `MAX_DISTANCE` | `0.75` | Relevance cutoff (cosine distance). Lower is stricter. |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed frontend origins, comma-separated |

### Frontend (`frontend/.env.local`)

| Variable | Description |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | Backend URL, e.g. `http://localhost:8000` |

---

## API reference

Interactive docs: **`/docs`** (Swagger UI).

| Method | Route | Description |
| --- | --- | --- |
| `POST` | `/api/documents` | Upload a PDF (`multipart/form-data`, field `file`). Returns `202` with `status: "processing"`. |
| `GET` | `/api/documents` | List documents, newest first |
| `GET` | `/api/documents/{id}` | One document. Poll this until `status` is `ready` or `failed`. |
| `GET` | `/api/documents/{id}/messages` | Conversation history |
| `POST` | `/api/documents/{id}/ask` | Ask a question: `{ "question": "…" }` |
| `DELETE` | `/api/documents/{id}` | Delete the file, its passages and its conversation |
| `GET` | `/api/health` | API and database health |

**Example**

```bash
curl -F "file=@manual.pdf" http://localhost:8000/api/documents
curl -X POST http://localhost:8000/api/documents/<id>/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How long is the warranty?"}'
```

```json
{
  "answer": {
    "role": "assistant",
    "content": "The warranty lasts 24 months from the date of purchase [1].",
    "sources": [{ "number": 1, "page": 2, "excerpt": "Warranty The warranty lasts 24 months from the date of purchase…" }]
  }
}
```

---

## Engineering decisions

**pgvector instead of a separate vector database.** Documents, passages, vectors and chat history live in one PostgreSQL database, so deletes cascade cleanly and there's one service to run and back up. An HNSW index keeps similarity search fast as data grows.

**A provider interface for the AI.** The app depends on a two-method `AIProvider` interface (`embed`, `generate`). Gemini is one implementation; tests use a deterministic fake, and switching vendors means changing one file.

**Grounded answers with verifiable citations.** The prompt numbers each passage and requires citations. The server returns only the sources the answer actually cites, each with a page number, so users can verify answers instead of trusting them.

**Don't call the model when there's nothing to say.** If no passage passes the relevance cutoff, the API answers "I couldn't find that in this document" without a model call. This saves cost and avoids invented answers.

**Page-aware, sentence-aware chunking.** Passages never cross pages, so every citation has an exact page. They break on paragraphs or sentences where possible, so excerpts read naturally, and overlap preserves context at boundaries.

**Background ingestion with visible status.** Uploads return immediately with `202 Accepted`; processing happens in a background task with its own database session. The UI polls only while something is processing.

**Specific failure messages.** Scanned PDFs (no text), password-protected files and damaged files each get a message that tells the user what to do next.

---

## Testing

```bash
cd backend && pytest -q        # needs a PostgreSQL + pgvector test database (see below)
cd frontend && npm test
```

The backend tests run against a **real PostgreSQL + pgvector** database, with a fake AI provider that builds word-overlap vectors, so retrieval behaves realistically without API calls. Set `TEST_DATABASE_URL`, for example:

```bash
docker run -d -p 5433:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=documind_test pgvector/pgvector:pg16
export TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/documind_test
```

- **Chunking:** page tracking, size limits, overlap, hyphen re-joining, very long words
- **RAG:** prompt structure, history window, citation parsing, excerpt trimming
- **API integration:** upload → processing → ready, cited answers pointing at the right page, unrelated questions skipping the model, non-PDF rejection, scanned-PDF failure messages, deletes cascading, and validation errors

CI runs Ruff, pytest (with a pgvector service container), and the frontend lint, typecheck, tests and build on every push.

---

## Deployment

| Part | Service | Notes |
| --- | --- | --- |
| Database | [Neon](https://neon.tech) or [Supabase](https://supabase.com) (both support pgvector) | Use the `postgresql+psycopg://` form of the connection string |
| Backend | [Render](https://render.com) or [Railway](https://railway.app) | Deploy `backend/` with its Dockerfile. Set the env vars. Use S3 for uploads, since container disks are temporary. |
| Frontend | [Vercel](https://vercel.com) | Root directory `frontend`, set `NEXT_PUBLIC_API_URL` |

Set `CORS_ORIGINS` on the backend to your Vercel URL.

---

## Limitations and roadmap

- **Single workspace:** there are no user accounts yet, so everyone using one deployment shares the document library. Next step: authentication and per-user documents.
- **Scanned PDFs** need OCR (for example, Tesseract or Gemini's document understanding) before they can be searched.
- Streaming answers token by token
- Alembic migrations for schema changes
- Multi-document questions across a whole library
- Background job queue (Celery or RQ) for very large files

---

## License

MIT. Built by **Nichenametla Keerthana** · [LinkedIn](https://www.linkedin.com/in/nichenametla-keerthana/)
