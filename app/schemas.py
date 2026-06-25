from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    pages: int
    chunks: int


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    chunks: int


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, description="What you want to ask the documents")
    session_id: str | None = Field(
        None, description="Pass back a session_id to keep the conversation together"
    )
    document_id: str | None = Field(
        None, description="Limit the search to one document. Omit to search everything."
    )
    top_k: int | None = Field(None, ge=1, le=10, description="How many chunks to retrieve")


class Source(BaseModel):
    document_id: str
    filename: str
    page: int
    chunk_index: int
    snippet: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    session_id: str


class HistoryTurn(BaseModel):
    question: str
    answer: str
    created_at: str


class HistoryResponse(BaseModel):
    session_id: str
    turns: list[HistoryTurn]
