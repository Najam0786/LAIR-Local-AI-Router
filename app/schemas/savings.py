from pydantic import BaseModel, Field


class SavingsTotals(BaseModel):
    """
    Running cloud-equivalent cost avoided by routing locally.
    """

    day_usd: float
    month_usd: float
    lifetime_usd: float


class SavingsResponse(SavingsTotals):
    """
    GET /v1/lair/savings response body.
    """


class LairMeta(BaseModel):
    """
    LAIR-specific metadata attached to OpenAI-compatible chat responses.
    """

    model_used: str

    estimated_savings_usd: float | None = Field(default=None)

    cache_hit: bool = Field(default=False)

    routed_to_cloud: bool = Field(
        default=False,
        description="True when this response was answered by a cloud "
        "provider (I-06, RFC-0001) -- the prompt left the machine. "
        "Never true unless explicitly enabled with a budget.",
    )

    cloud_escalation_reason: str | None = Field(default=None)

    memory_injected_count: int = Field(
        default=0,
        description="Number of persisted project memories (I-18, "
        "provenance MEMORY) injected as context for this request. "
        "Always 0 when ENABLE_PROJECT_MEMORY is off or no "
        "lair_project_scope was supplied.",
    )
