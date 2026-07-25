import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from pydantic import BaseModel, Field

_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_PATH = _ROOT / "logs" / "rag_documents.json"


class DocumentChunk(BaseModel):
    text: str
    embedding: list[float]


class IngestedDocument(BaseModel):
    document_id: str
    filename: str
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    chunks: list[DocumentChunk]


class DocumentInfo(BaseModel):
    """Metadata-only view of an ingested document (no embeddings)."""

    document_id: str
    filename: str
    ingested_at: datetime
    chunk_count: int


class DocumentStore:
    """
    Local store of ingested documents' chunks + embeddings (I-08).

    "Lite" per the plan's own design notes: no external vector DB.
    JSON-backed like every other store in this codebase; retrieval
    (app/rag/retrieval.py) loads a document's chunks into memory and
    does the similarity search there -- fine at the scale a single
    local user's document set actually reaches.
    """

    def __init__(self, path: Path | str = _DEFAULT_PATH):
        self._path = Path(path)
        self._lock = Lock()

    def ingest(self, filename: str, chunks: list[DocumentChunk]) -> str:
        document_id = uuid.uuid4().hex

        with self._lock:
            documents = self._read_all()
            documents.append(
                IngestedDocument(
                    document_id=document_id,
                    filename=filename,
                    chunks=chunks,
                )
            )
            self._write_all(documents)

        return document_id

    def get(self, document_id: str) -> IngestedDocument | None:
        for document in self._read_all():
            if document.document_id == document_id:
                return document

        return None

    def list_documents(self) -> list[DocumentInfo]:
        return [
            DocumentInfo(
                document_id=document.document_id,
                filename=document.filename,
                ingested_at=document.ingested_at,
                chunk_count=len(document.chunks),
            )
            for document in self._read_all()
        ]

    def forget(self, document_id: str) -> bool:
        with self._lock:
            documents = self._read_all()
            remaining = [d for d in documents if d.document_id != document_id]

            if len(remaining) == len(documents):
                return False

            self._write_all(remaining)
            return True

    def _read_all(self) -> list[IngestedDocument]:
        if not self._path.exists():
            return []

        text = self._path.read_text(encoding="utf-8").strip()

        if not text:
            return []

        return [IngestedDocument(**record) for record in json.loads(text)]

    def _write_all(self, documents: list[IngestedDocument]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(
                [json.loads(d.model_dump_json()) for d in documents],
                indent=2,
            ),
            encoding="utf-8",
        )


default_document_store = DocumentStore()
