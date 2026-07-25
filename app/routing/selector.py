from app.capabilities.requirement import CapabilityRequirement
from app.hardware.hardware_profile import HardwareProfile
from app.hardware.power import PowerState
from app.hardware.resource_profile import ResourceProfile
from app.hardware.tier import HardwareTier
from app.knowledge.knowledge_base import KnowledgeBase
from app.models.ai_model import AIModel
from app.models.task import Task
from app.registry.community_scores import CommunityScoreTable
from app.routing.complexity import ComplexityAssessment
from app.routing.decision import DecisionRecord, ScoredCandidate
from app.routing.model_scorer import model_scorer
from app.routing.policy import RoutingPolicy


class NoCandidateModelsError(ValueError):
    """
    Raised when no model satisfies the request's requirements.
    """


class ModelSelector:
    """
    Selects the highest-ranked AI model.

    The selector delegates score calculation to the
    ModelScorer and ranks models using the resulting
    ScoreBreakdown.
    """

    def select(
        self,
        task: Task,
        models: list[AIModel],
        requirements: list[CapabilityRequirement],
        policy: RoutingPolicy,
        knowledge_base: KnowledgeBase | None = None,
        complexity: ComplexityAssessment | None = None,
        resource_profiles: dict[str, ResourceProfile] | None = None,
        hardware: HardwareProfile | None = None,
        language_code: str | None = None,
        community_scores: CommunityScoreTable | None = None,
        hardware_tier: HardwareTier | None = None,
        power_state: PowerState | None = None,
    ) -> DecisionRecord:
        """
        Select the highest-ranked model.
        """

        if not models:
            raise NoCandidateModelsError("No candidate models available.")

        resource_profiles = resource_profiles or {}

        candidates = [
            ScoredCandidate(
                model=model,
                breakdown=model_scorer.score(
                    model,
                    requirements,
                    policy,
                    knowledge_base,
                    complexity,
                    resource_profiles.get(model.id),
                    hardware,
                    language_code,
                    community_scores=community_scores,
                    hardware_tier=hardware_tier,
                    power_state=power_state,
                ),
            )
            for model in models
        ]

        candidates.sort(
            key=lambda candidate: candidate.breakdown.total_score,
            reverse=True,
        )

        return DecisionRecord(
            task=task,
            requirements=requirements,
            complexity=complexity,
            language_code=language_code,
            candidates=candidates,
            policy=policy,
            selected_model=candidates[0].model,
        )


selector = ModelSelector()
