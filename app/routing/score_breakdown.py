from pydantic import BaseModel, Field, computed_field

from app.routing.provenance import Provenance


class ScoreFactor(BaseModel):
    """
    A single named contribution to a model's routing score, tagged with
    where the underlying value came from.
    """

    name: str

    score: float

    provenance: Provenance

    reason: str


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

    complexity_score: float = Field(
        default=0.0,
        ge=0.0,
    )

    quant_efficiency_score: float = Field(
        default=0.0,
        ge=0.0,
    )

    language_score: float = Field(
        default=0.0,
        ge=0.0,
    )

    battery_score: float = Field(
        default=0.0,
        ge=0.0,
    )

    # ---------------------------------------------------------
    # Explainability
    # ---------------------------------------------------------

    matched_capabilities: list[str] = Field(
        default_factory=list,
    )

    factors: list[ScoreFactor] = Field(
        default_factory=list,
    )

    def add_factor(
        self,
        name: str,
        score: float,
        provenance: Provenance,
        reason: str,
    ) -> None:
        """
        Record a tagged, explainable contribution to this breakdown.
        """

        self.factors.append(
            ScoreFactor(
                name=name,
                score=score,
                provenance=provenance,
                reason=reason,
            )
        )

    @computed_field
    @property
    def reasons(self) -> list[str]:
        """
        Human-readable reasons, projected from the tagged factors.
        """

        return [factor.reason for factor in self.factors]
