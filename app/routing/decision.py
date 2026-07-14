from datetime import datetime, timezone

from pydantic import BaseModel, Field, computed_field

from app.capabilities.requirement import CapabilityRequirement
from app.models.ai_model import AIModel
from app.models.task import Task
from app.routing.policy import RoutingPolicy
from app.routing.score_breakdown import ScoreBreakdown


class ScoredCandidate(BaseModel):
    """
    A single candidate model considered during a routing decision.
    """

    model: AIModel

    breakdown: ScoreBreakdown


class DecisionRecord(BaseModel):
    """
    Immutable, auditable trace of a routing decision.
    """

    task: Task

    requirements: list[CapabilityRequirement]

    candidates: list[ScoredCandidate]

    policy: RoutingPolicy

    selected_model: AIModel

    decided_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def _winner(self) -> ScoredCandidate:
        for candidate in self.candidates:
            if candidate.model.id == self.selected_model.id:
                return candidate

        raise ValueError("selected_model not present among candidates.")

    @computed_field
    @property
    def confidence(self) -> float:
        """
        Confidence derived from the gap between the winning and
        runner-up scores, normalized by the winning score.
        """

        if len(self.candidates) == 1:
            return 1.0

        top = self.candidates[0].breakdown.total_score
        second = self.candidates[1].breakdown.total_score

        if top <= 0:
            return 0.0

        return max(0.0, min(1.0, (top - second) / top))

    @computed_field
    @property
    def reasons(self) -> list[str]:
        """
        Human-readable explanation, projected from the winning candidate.
        """

        return self._winner().breakdown.reasons
