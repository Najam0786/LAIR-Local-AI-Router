import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from pydantic import BaseModel, Field

from app.core.settings import settings

_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_PATH = _ROOT / "logs" / "project_memory.json"


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


class MemoryRecord(BaseModel):
    memory_id: str
    project_scope: str
    text: str
    embedding: list[float]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryRecordInfo(BaseModel):
    """Metadata-only view of a memory (no embedding) -- `lair memory list`."""

    memory_id: str
    project_scope: str
    text: str
    created_at: datetime
    updated_at: datetime


class MemoryStore:
    """
    Local, per-project-scope store of extracted memories (I-18,
    RFC-0002, ADR-0020). JSON-backed like every other store in this
    codebase; a new memory is deduped against existing memories in the
    *same scope only* by embedding cosine similarity before being
    appended -- a near-duplicate updates the existing record instead of
    accumulating noise.
    """

    def __init__(self, path: Path | str = _DEFAULT_PATH):
        self._path = Path(path)
        self._lock = Lock()

    def remember(
        self, project_scope: str, text: str, embedding: list[float]
    ) -> MemoryRecord:
        with self._lock:
            records = self._read_all()

            best_match: MemoryRecord | None = None
            best_similarity = 0.0

            for record in records:
                if record.project_scope != project_scope:
                    continue

                similarity = _cosine_similarity(embedding, record.embedding)

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = record

            if best_match is not None and best_similarity >= settings.MEMORY_DEDUP_SIMILARITY_THRESHOLD:
                best_match.text = text
                best_match.embedding = embedding
                best_match.updated_at = datetime.now(timezone.utc)
                self._write_all(records)
                return best_match

            new_record = MemoryRecord(
                memory_id=uuid.uuid4().hex,
                project_scope=project_scope,
                text=text,
                embedding=embedding,
            )
            records.append(new_record)
            self._write_all(records)
            return new_record

    def get(self, memory_id: str) -> MemoryRecord | None:
        for record in self._read_all():
            if record.memory_id == memory_id:
                return record

        return None

    def list_for_scope(self, project_scope: str) -> list[MemoryRecordInfo]:
        return [
            MemoryRecordInfo(
                memory_id=record.memory_id,
                project_scope=record.project_scope,
                text=record.text,
                created_at=record.created_at,
                updated_at=record.updated_at,
            )
            for record in self._read_all()
            if record.project_scope == project_scope
        ]

    def all_for_scope(self, project_scope: str) -> list[MemoryRecord]:
        return [r for r in self._read_all() if r.project_scope == project_scope]

    def forget(self, memory_id: str) -> bool:
        with self._lock:
            records = self._read_all()
            remaining = [r for r in records if r.memory_id != memory_id]

            if len(remaining) == len(records):
                return False

            self._write_all(remaining)
            return True

    def forget_all(self, project_scope: str) -> int:
        with self._lock:
            records = self._read_all()
            remaining = [r for r in records if r.project_scope != project_scope]
            removed = len(records) - len(remaining)

            if removed:
                self._write_all(remaining)

            return removed

    def export_scope(self, project_scope: str) -> list[dict]:
        return [
            json.loads(record.model_dump_json())
            for record in self._read_all()
            if record.project_scope == project_scope
        ]

    def _read_all(self) -> list[MemoryRecord]:
        if not self._path.exists():
            return []

        text = self._path.read_text(encoding="utf-8").strip()

        if not text:
            return []

        return [MemoryRecord(**record) for record in json.loads(text)]

    def _write_all(self, records: list[MemoryRecord]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(
                [json.loads(r.model_dump_json()) for r in records],
                indent=2,
            ),
            encoding="utf-8",
        )


default_memory_store = MemoryStore()
