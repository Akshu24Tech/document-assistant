import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

log = logging.getLogger("app.errors")


class LLMError(Exception):
    """Raised when a Gemini call (embedding or generation) fails."""


class DocumentError(Exception):
    """Raised when an uploaded file can't be read as a usable PDF."""


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DocumentError)
    async def handle_document_error(request: Request, exc: DocumentError):
        log.warning("bad document on %s: %s", request.url.path, exc)
        return JSONResponse(status_code=400, content={"error": str(exc)})

    @app.exception_handler(LLMError)
    async def handle_llm_error(request: Request, exc: LLMError):
        log.error("Gemini call failed on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=502,
            content={"error": "The language model is unavailable right now. Please try again."},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        log.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": "Something went wrong on our side."},
        )
