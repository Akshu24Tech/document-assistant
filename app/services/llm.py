import logging
from typing import Iterator

import google.generativeai as genai

from app.config import get_settings
from app.core.exceptions import LLMError

log = logging.getLogger("app.llm")

_configured = False

SYSTEM_RULES = (
    "You are a document assistant. Answer the question using only the context "
    "passages provided. If the answer isn't in the context, say you couldn't find "
    "it in the documents — don't make something up. Cite passages as [1], [2] to "
    "match the numbering you're given."
)


def _get_model():
    global _configured
    settings = get_settings()
    if not _configured:
        genai.configure(api_key=settings.gemini_api_key)
        _configured = True
        log.info("Gemini configured with model %s", settings.gemini_model)
    return genai.GenerativeModel(settings.gemini_model, system_instruction=SYSTEM_RULES)


def build_prompt(question: str, passages: list[str]) -> str:
    context = "\n\n".join(f"[{i + 1}] {p}" for i, p in enumerate(passages))
    return f"Context passages:\n\n{context}\n\nQuestion: {question}"


def answer(question: str, passages: list[str]) -> str:
    prompt = build_prompt(question, passages)
    try:
        response = _get_model().generate_content(prompt)
        return response.text.strip()
    except Exception as exc:
        raise LLMError(str(exc)) from exc


def answer_stream(question: str, passages: list[str]) -> Iterator[str]:
    """Yield the answer token-by-token for the streaming endpoint."""
    prompt = build_prompt(question, passages)
    try:
        for chunk in _get_model().generate_content(prompt, stream=True):
            if chunk.text:
                yield chunk.text
    except Exception as exc:
        raise LLMError(str(exc)) from exc
