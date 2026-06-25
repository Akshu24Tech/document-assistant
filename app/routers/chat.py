import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.core.auth import require_api_key
from app.schemas import AskRequest, AskResponse, HistoryResponse, HistoryTurn, Source
from app.services import embeddings, history, llm, vectorstore

router = APIRouter(prefix="/api/chat", dependencies=[Depends(require_api_key)])
log = logging.getLogger("app.chat")


def _retrieve(req: AskRequest) -> list[dict]:
    """Embed the question and pull the closest chunks from the store."""
    top_k = req.top_k or get_settings().top_k
    query_vector = embeddings.embed_query(req.question)
    hits = vectorstore.search(query_vector, top_k, req.document_id)
    if not hits:
        raise HTTPException(
            status_code=404,
            detail="No documents to search yet. Upload a PDF first.",
        )
    return hits


def _to_sources(hits: list[dict]) -> list[Source]:
    return [
        Source(
            document_id=h["meta"]["document_id"],
            filename=h["meta"]["filename"],
            page=h["meta"]["page"],
            chunk_index=h["meta"]["chunk_index"],
            snippet=h["text"][:300],
        )
        for h in hits
    ]


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    hits = _retrieve(req)
    passages = [h["text"] for h in hits]
    answer = llm.answer(req.question, passages)

    session_id = req.session_id or history.new_session()
    sources = _to_sources(hits)
    history.save_turn(session_id, req.question, answer, [s.model_dump() for s in sources])

    log.info("answered in session %s using %d chunks", session_id, len(hits))
    return AskResponse(answer=answer, sources=sources, session_id=session_id)


@router.post("/ask/stream")
def ask_stream(req: AskRequest):
    """Same retrieval as /ask, but the answer streams back as plain text.

    The full turn is saved to history once the stream finishes.
    """
    hits = _retrieve(req)
    passages = [h["text"] for h in hits]
    session_id = req.session_id or history.new_session()
    sources = _to_sources(hits)

    def generate():
        collected: list[str] = []
        for token in llm.answer_stream(req.question, passages):
            collected.append(token)
            yield token
        history.save_turn(
            session_id, req.question, "".join(collected), [s.model_dump() for s in sources]
        )

    headers = {"X-Session-Id": session_id}
    return StreamingResponse(generate(), media_type="text/plain", headers=headers)


@router.get("/history/{session_id}", response_model=HistoryResponse)
def get_history(session_id: str):
    turns = history.get_turns(session_id)
    return HistoryResponse(
        session_id=session_id,
        turns=[HistoryTurn(**t) for t in turns],
    )
