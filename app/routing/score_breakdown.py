from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    """
    Represents a detailed explanation of how a routing
    score was calculated.
    """

    # ---------------------------------------------------------
    # Overall Score
    # ---------------------------------------------------------

    total_score: float = Field(
        default=0.0,
        ge=0.0,
    )

    # ---------------------------------------------------------
    # Individual Scores
    # ---------------------------------------------------------

    capability_score: float = Field(
        default=0.0,
        ge=0.0,
    )

    streaming_score: float = Field(
        default=0.0,
        ge=0.0,
    )

    context_window_score: float = Field(
        default=0.0,
        ge=0.0,
    )

    benchmark_score: float = Field(
        default=0.0,
        ge=0.0,
    )

    loaded_bonus_score: float = Field(
        default=0.0,
        ge=0.0,
    )

    # ---------------------------------------------------------
    # Explainability
    # ---------------------------------------------------------

    matched_capabilities: list[str] = Field(
        default_factory=list,
    )

    reasons: list[str] = Field(
        default_factory=list,
    )