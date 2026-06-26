import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.routers import chat, documents

settings = get_settings()
setup_logging(settings.log_level)
log = logging.getLogger("app")

app = FastAPI(
    title=settings.app_name,
    description=(
        "Upload PDFs and ask questions about them. Retrieval-augmented generation "
        "over Gemini embeddings + ChromaDB, with source references and chat history."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

register_exception_handlers(app)

app.include_router(documents.router, tags=["documents"])
app.include_router(chat.router, tags=["chat"])


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}


# serve the single-page frontend. mounted last so it owns "/" without shadowing
# the /api routes above. html=True makes "/" return index.html.
static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

log.info("%s ready", settings.app_name)
