import io
import logging

from pypdf import PdfReader

from app.config import get_settings
from app.core.exceptions import DocumentError

log = logging.getLogger("app.pdf")


def extract_pages(file_bytes: bytes) -> list[str]:
    """Pull the text out of a PDF, one string per page.

    Page order matters here — we keep the page number around so answers can
    cite where they came from.
    """
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception as exc:
        raise DocumentError("Couldn't open that file as a PDF.") from exc

    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    if not any(pages):
        # scanned PDFs with no text layer land here — we don't OCR
        raise DocumentError("No extractable text found. Is this a scanned image PDF?")

    log.info("extracted %d pages", len(pages))
    return pages


def chunk_pages(pages: list[str]) -> list[dict]:
    """Split each page into overlapping windows.

    Returns dicts carrying the text plus the page it came from, so the chunk
    index lines up with a real location in the document.
    """
    settings = get_settings()
    size, overlap = settings.chunk_size, settings.chunk_overlap
    step = size - overlap

    chunks: list[dict] = []
    for page_no, text in enumerate(pages, start=1):
        if not text:
            continue
        for start in range(0, len(text), step):
            window = text[start : start + size].strip()
            if window:
                chunks.append({"text": window, "page": page_no})

    log.info("built %d chunks", len(chunks))
    return chunks
