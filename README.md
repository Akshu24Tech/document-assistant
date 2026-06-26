# Document Assistant

Upload PDFs and ask questions about them. The app extracts and chunks the text,
embeds it with Gemini, stores it in ChromaDB, and answers your questions from the
most relevant chunks — with the source page it pulled each answer from.

This is retrieval-augmented generation (RAG): the model only answers from what it
retrieved, so it stays grounded in your documents instead of guessing.

It ships as one service — a FastAPI backend that also serves a small web UI, so
there's a single thing to run and a single thing to deploy.

## What it does

- **Upload** a PDF — text is extracted, chunked, embedded and indexed
- **Ask** questions — answers come back with source references (filename + page)
- **Multi-document** — search across everything, or scope to one document
- **Chat history** — every question/answer turn is saved under a session id
- **Streaming** — watch the answer arrive token-by-token
- **Auth** — flip on a shared API key with one env var
- **Web UI** — upload + chat from the browser, served by the API itself

## How it works

```
PDF ──▶ extract text ──▶ chunk ──▶ Gemini embeddings ──▶ ChromaDB
                                                            │
question ──▶ Gemini embedding ──▶ similarity search ◀───────┘
                                       │
                              top-k chunks + question ──▶ Gemini ──▶ answer + sources
```

More detail (with the request/response flow) is in [docs/architecture.md](docs/architecture.md).

## Project layout

```
app/
  main.py              # app setup, router wiring, serves the frontend
  config.py            # settings loaded from .env
  schemas.py           # request/response models (validation lives here)
  routers/
    documents.py       # /api/documents — upload + list
    chat.py            # /api/chat — ask, streaming ask, history
  services/
    pdf.py             # text extraction + chunking
    embeddings.py      # Gemini embeddings (document vs query)
    vectorstore.py     # ChromaDB wrapper
    llm.py             # Gemini generation + the RAG prompt
    history.py         # chat history (SQLite)
  core/                # logging, exception handling, auth
  static/              # the web UI (plain HTML/CSS/JS, no build step)
tests/                 # pytest (Gemini + Chroma are mocked, no key needed)
docs/                  # API reference + architecture
```

## Setup

You need Python 3.10+ and a Gemini API key (free from
https://aistudio.google.com/app/apikey).

```bash
python -m venv .venv
.venv\Scripts\activate          # on Windows
# source .venv/bin/activate     # on macOS/Linux

pip install -r requirements.txt

copy .env.example .env          # then open .env and paste your key
```

## Run

```bash
uvicorn app.main:app --reload
```

- Web UI: http://127.0.0.1:8000/
- Swagger docs: http://127.0.0.1:8000/api/docs

## Run with Docker

```bash
docker build -t document-assistant .
docker run -p 8000:8000 --env-file .env -v "$(pwd)/data:/code/data" document-assistant
```

The `-v` mount keeps the vector store and chat history between restarts.

## Config

Set in `.env` (see `.env.example`):

| Variable          | Default                      | What it does                              |
|-------------------|------------------------------|-------------------------------------------|
| `GEMINI_API_KEY`  | —                            | your Gemini key (required)                |
| `GEMINI_MODEL`    | `gemini-2.5-flash`           | model used to write answers               |
| `EMBEDDING_MODEL` | `models/text-embedding-004`  | model used to embed text                  |
| `API_KEY`         | empty                        | if set, every API endpoint needs `X-API-Key` |
| `LOG_LEVEL`       | `INFO`                       | log verbosity                             |

Chunk size, overlap and top-k have sensible defaults in `config.py`.

## Tests

```bash
pytest
```

Tests mock the Gemini and Chroma calls, so they run without a real key.

## Notes

- Logs go to the console and to `logs/app.log` (rotated).
- The vector store and chat history live under `data/` (gitignored).
- Scanned image PDFs with no text layer are rejected — there's no OCR step.
- Full endpoint reference with examples is in [docs/API.md](docs/API.md).
