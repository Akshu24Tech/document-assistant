from fastapi.testclient import TestClient

from app import main
from app.services import embeddings, llm, vectorstore

client = TestClient(main.app)


def _fake_hits():
    return [
        {
            "text": "The refund window is 30 days.",
            "meta": {
                "document_id": "doc1",
                "filename": "policy.pdf",
                "page": 2,
                "chunk_index": 5,
            },
            "score": 0.91,
        }
    ]


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_frontend_is_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "Document Assistant" in r.text


def test_ask_returns_answer_and_sources(monkeypatch):
    monkeypatch.setattr(embeddings, "embed_query", lambda q: [0.1, 0.2, 0.3])
    monkeypatch.setattr(vectorstore, "search", lambda v, k, d=None: _fake_hits())
    monkeypatch.setattr(llm, "answer", lambda q, passages: "You have 30 days [1].")

    r = client.post("/api/chat/ask", json={"question": "What is the refund window?"})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == "You have 30 days [1]."
    assert body["sources"][0]["filename"] == "policy.pdf"
    assert body["sources"][0]["page"] == 2
    assert body["session_id"]  # a session id is always returned


def test_ask_rejects_short_question():
    r = client.post("/api/chat/ask", json={"question": "x"})
    assert r.status_code == 422


def test_ask_404_when_nothing_indexed(monkeypatch):
    monkeypatch.setattr(embeddings, "embed_query", lambda q: [0.1])
    monkeypatch.setattr(vectorstore, "search", lambda v, k, d=None: [])

    r = client.post("/api/chat/ask", json={"question": "anything in here?"})
    assert r.status_code == 404


def test_history_round_trips(monkeypatch):
    monkeypatch.setattr(embeddings, "embed_query", lambda q: [0.1])
    monkeypatch.setattr(vectorstore, "search", lambda v, k, d=None: _fake_hits())
    monkeypatch.setattr(llm, "answer", lambda q, passages: "An answer.")

    first = client.post("/api/chat/ask", json={"question": "first question?"}).json()
    session_id = first["session_id"]
    client.post("/api/chat/ask", json={"question": "second question?", "session_id": session_id})

    hist = client.get(f"/api/chat/history/{session_id}").json()
    assert hist["session_id"] == session_id
    assert [t["question"] for t in hist["turns"]] == ["first question?", "second question?"]
