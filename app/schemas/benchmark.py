from pydantic import BaseModel

from app.benchmarking.benchmark_result import BenchmarkResult


class BenchmarkListResponse(BaseModel):
    """
    Response returned by the benchmarks listing endpoint.
    """

    results: list[BenchmarkResult]
