from app.capabilities.requirement import CapabilityRequirement
from app.knowledge.knowledge_base import KnowledgeBase
from app.models.ai_model import AIModel
from app.models.task import Task
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
    ) -> DecisionRecord:
        """
        Select the highest-ranked model.
        """

        if not models:
            raise NoCandidateModelsError("No candidate models available.")

        candidates = [
            ScoredCandidate(
                model=model,
                breakdown=model_scorer.score(
                    model,
                    requirements,
                    policy,
                    knowledge_base,
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
            candidates=candidates,
            policy=policy,
            selected_model=candidates[0].model,
        )


selector = ModelSelector()
