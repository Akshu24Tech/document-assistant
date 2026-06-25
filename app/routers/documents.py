import logging
import uuid

from fastapi import APIRouter, Depends, UploadFile

from app.core.auth import require_api_key
from app.core.exceptions import DocumentError
from app.schemas import DocumentInfo, UploadResponse
from app.services import embeddings, pdf, vectorstore

router = APIRouter(prefix="/api/documents", dependencies=[Depends(require_api_key)])
log = logging.getLogger("app.documents")


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise DocumentError("Only PDF files are supported.")

    raw = await file.read()
    pages = pdf.extract_pages(raw)
    chunks = pdf.chunk_pages(pages)

    document_id = uuid.uuid4().hex
    vectors = embeddings.embed_documents([c["text"] for c in chunks])
    vectorstore.add_chunks(document_id, file.filename, chunks, vectors)

    log.info("uploaded %s as %s (%d chunks)", file.filename, document_id, len(chunks))
    return UploadResponse(
        document_id=document_id,
        filename=file.filename,
        pages=len(pages),
        chunks=len(chunks),
    )


@router.get("", response_model=list[DocumentInfo])
def list_documents():
    return [DocumentInfo(**d) for d in vectorstore.list_documents()]
