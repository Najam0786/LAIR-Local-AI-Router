import io

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.settings import settings
from app.rag.chunking import chunk_text
from app.rag.embeddings import default_embedding_model
from app.rag.pdf_extractor import extract_pdf_text
from app.rag.store import DocumentChunk, default_document_store
from app.schemas.documents import (
    DocumentForgetResponse,
    DocumentIngestResponse,
    DocumentListResponse,
)

router = APIRouter(tags=["Documents"])


@router.post("/v1/lair/documents", response_model=DocumentIngestResponse)
async def ingest_document(file: UploadFile = File(...)) -> DocumentIngestResponse:
    """
    Ingests a document for RAG-lite retrieval (I-08): extracts text
    (PDF via `pypdf`, otherwise treated as plain text), chunks it,
    embeds each chunk locally, and stores it for later retrieval by
    `document_id`. All processing local -- no network call happens
    here beyond the embedding model's one-time acquisition, which
    already happened (or happens now, once) on first use.
    """

    raw = await file.read()
    filename = file.filename or "document"

    if filename.lower().endswith(".pdf"):
        text = extract_pdf_text(io.BytesIO(raw))
    else:
        text = raw.decode("utf-8", errors="replace")

    chunks_text = chunk_text(
        text,
        settings.RAG_CHUNK_SIZE_TOKENS,
        settings.RAG_CHUNK_OVERLAP_TOKENS,
    )

    if not chunks_text:
        raise HTTPException(
            status_code=400,
            detail="Document produced no extractable text.",
        )

    embeddings = default_embedding_model.embed(chunks_text)
    chunks = [
        DocumentChunk(text=text_chunk, embedding=embedding)
        for text_chunk, embedding in zip(chunks_text, embeddings)
    ]

    document_id = default_document_store.ingest(filename, chunks)

    return DocumentIngestResponse(
        document_id=document_id,
        filename=filename,
        chunk_count=len(chunks),
    )


@router.get("/v1/lair/documents", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    return DocumentListResponse(documents=default_document_store.list_documents())


@router.delete("/v1/lair/documents/{document_id}", response_model=DocumentForgetResponse)
async def forget_document(document_id: str) -> DocumentForgetResponse:
    removed = default_document_store.forget(document_id)

    if not removed:
        raise HTTPException(status_code=404, detail="Document not found.")

    return DocumentForgetResponse(forgotten=True)
