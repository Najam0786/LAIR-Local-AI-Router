from datetime import datetime, timezone

from pydantic import BaseModel, Field, computed_field


class BenchmarkResult(BaseModel):
    """
    A single measured latency/throughput result for a model.
    """

    run_id: str

    model_id: str

    provider: str

    prompt: str

    latency_seconds: float = Field(ge=0.0)

    completion_tokens: int = Field(ge=0)

    measured_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @computed_field
    @property
    def tokens_per_second(self) -> float:
        if self.latency_seconds <= 0:
            return 0.0

        return self.completion_tokens / self.latency_seconds
