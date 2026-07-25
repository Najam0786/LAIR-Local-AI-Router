from pydantic import BaseModel

from app.rag.store import DocumentInfo


class DocumentIngestResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]


class DocumentForgetResponse(BaseModel):
    forgotten: bool
