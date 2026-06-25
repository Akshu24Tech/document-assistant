import logging

import google.generativeai as genai

from app.config import get_settings
from app.core.exceptions import LLMError

log = logging.getLogger("app.embeddings")

_configured = False


def _configure() -> None:
    global _configured
    if not _configured:
        genai.configure(api_key=get_settings().gemini_api_key)
        _configured = True


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed chunks for storage. task_type tells Gemini these are documents."""
    _configure()
    model = get_settings().embedding_model
    try:
        result = genai.embed_content(model=model, content=texts, task_type="retrieval_document")
        return result["embedding"]
    except Exception as exc:
        raise LLMError(f"embedding failed: {exc}") from exc


def embed_query(text: str) -> list[float]:
    """Embed a single question. A different task_type than the documents above."""
    _configure()
    model = get_settings().embedding_model
    try:
        result = genai.embed_content(model=model, content=text, task_type="retrieval_query")
        return result["embedding"]
    except Exception as exc:
        raise LLMError(f"embedding failed: {exc}") from exc
