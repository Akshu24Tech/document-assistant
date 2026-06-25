import logging

import chromadb

from app.config import get_settings

log = logging.getLogger("app.vectorstore")

_collection = None


def _get_collection():
    """One persistent Chroma collection holds chunks from every document.

    We bring our own Gemini embeddings, so Chroma is used purely as the vector
    index + metadata store (embedding_function stays unset).
    """
    global _collection
    if _collection is None:
        settings = get_settings()
        client = chromadb.PersistentClient(path=settings.chroma_dir)
        _collection = client.get_or_create_collection(
            name="documents", metadata={"hnsw:space": "cosine"}
        )
    return _collection


def add_chunks(
    document_id: str,
    filename: str,
    chunks: list[dict],
    embeddings: list[list[float]],
) -> None:
    collection = _get_collection()
    ids = [f"{document_id}:{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "document_id": document_id,
            "filename": filename,
            "page": chunk["page"],
            "chunk_index": i,
        }
        for i, chunk in enumerate(chunks)
    ]
    documents = [chunk["text"] for chunk in chunks]
    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    log.info("stored %d chunks for %s", len(chunks), document_id)


def search(query_embedding: list[float], top_k: int, document_id: str | None = None) -> list[dict]:
    collection = _get_collection()
    where = {"document_id": document_id} if document_id else None
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    # chroma nests everything one list deep (one entry per query); we sent one query
    hits = []
    for text, meta, distance in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        hits.append({"text": text, "meta": meta, "score": 1 - distance})
    return hits


def list_documents() -> list[dict]:
    """Roll the per-chunk rows up into one entry per document."""
    collection = _get_collection()
    rows = collection.get(include=["metadatas"])
    counts: dict[str, dict] = {}
    for meta in rows["metadatas"]:
        doc_id = meta["document_id"]
        if doc_id not in counts:
            counts[doc_id] = {"document_id": doc_id, "filename": meta["filename"], "chunks": 0}
        counts[doc_id]["chunks"] += 1
    return list(counts.values())
