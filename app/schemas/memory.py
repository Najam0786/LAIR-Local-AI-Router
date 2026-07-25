from pydantic import BaseModel

from app.memory.store import MemoryRecordInfo


class MemoryListResponse(BaseModel):
    memories: list[MemoryRecordInfo]


class MemoryForgetResponse(BaseModel):
    forgotten: bool


class MemoryForgetAllResponse(BaseModel):
    removed_count: int
