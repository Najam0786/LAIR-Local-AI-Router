from fastapi import APIRouter

from app.knowledge.knowledge_base import default_knowledge_base
from app.schemas.benchmark import BenchmarkListResponse

router = APIRouter(tags=["Benchmarks"])


@router.get("/benchmarks", response_model=BenchmarkListResponse)
async def list_benchmarks() -> BenchmarkListResponse:
    """
    Return the latest known benchmark result for every measured model.
    """

    return BenchmarkListResponse(
        results=list(default_knowledge_base.all_latest().values())
    )
