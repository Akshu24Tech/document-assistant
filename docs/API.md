# API Reference

Base URL: `http://127.0.0.1:8000`

All API routes live under `/api`. Request and response bodies are JSON (except
file upload, which is multipart, and the streaming endpoint, which returns plain
text). Validation errors return `422`. A bad PDF returns `400`. If a Gemini call
fails the API returns `502`.

If `API_KEY` is set in the environment, every endpoint below needs an
`X-API-Key` header with that value. Leave it blank and auth is off.

Interactive docs are auto-generated at `/api/docs` (Swagger) and `/api/redoc`.

---

## POST /api/documents/upload

Upload a PDF. It's extracted, chunked, embedded and indexed.

**Request** — `multipart/form-data` with a single `file` field (must be a `.pdf`).

```bash
curl -X POST http://127.0.0.1:8000/api/documents/upload \
  -F "file=@handbook.pdf"
```

**Response**

```json
{
  "document_id": "9f2c1a7b4e8d4f6a...",
  "filename": "handbook.pdf",
  "pages": 12,
  "chunks": 34
}
```

Keep the `document_id` if you want to scope later questions to this document.

---

## GET /api/documents

List every indexed document and its chunk count.

```bash
curl http://127.0.0.1:8000/api/documents
```

**Response**

```json
[
  { "document_id": "9f2c1a7b...", "filename": "handbook.pdf", "chunks": 34 }
]
```

---

## POST /api/chat/ask

Ask a question. Retrieves the most relevant chunks and answers from them, with
source references.

**Request**

| Field         | Type   | Required | Notes                                            |
|---------------|--------|----------|--------------------------------------------------|
| `question`    | string | yes      | at least 3 characters                            |
| `session_id`  | string | no       | pass it back to keep a conversation together     |
| `document_id` | string | no       | limit the search to one document                 |
| `top_k`       | int    | no       | 1–10, how many chunks to retrieve (default 4)    |

```bash
curl -X POST http://127.0.0.1:8000/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How many vacation days do new hires get?"}'
```

**Response**

```json
{
  "answer": "New hires get 15 days in their first year [1].",
  "sources": [
    {
      "document_id": "9f2c1a7b...",
      "filename": "handbook.pdf",
      "page": 4,
      "chunk_index": 11,
      "snippet": "Employees accrue 15 days of paid time off during..."
    }
  ],
  "session_id": "3b9e0d2f5a6c..."
}
```

The `[1]` in the answer maps to the first item in `sources`.

Returns `404` if nothing has been uploaded yet.

---

## POST /api/chat/ask/stream

Same as `/api/chat/ask`, but the answer streams back as `text/plain`
token-by-token. The session id comes back in the `X-Session-Id` response header.
The full turn is saved to history once the stream completes.

```bash
curl -N -X POST http://127.0.0.1:8000/api/chat/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "Summarize the leave policy."}'
```

---

## GET /api/chat/history/{session_id}

Return every question/answer turn saved under a session.

```bash
curl http://127.0.0.1:8000/api/chat/history/3b9e0d2f5a6c...
```

**Response**

```json
{
  "session_id": "3b9e0d2f5a6c...",
  "turns": [
    {
      "question": "How many vacation days do new hires get?",
      "answer": "New hires get 15 days in their first year [1].",
      "created_at": "2026-06-26T09:14:22.105000+00:00"
    }
  ]
}
```

---

## GET /api/health

Simple health check.

```json
{ "status": "ok" }
```
