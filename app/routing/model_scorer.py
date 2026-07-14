from app.capabilities.requirement import CapabilityRequirement
from app.knowledge.knowledge_base import KnowledgeBase
from app.models.ai_model import AIModel
from app.routing.policy import RoutingPolicy
from app.routing.score_breakdown import ScoreBreakdown


class ModelScorer:
    """
    Calculates routing scores for AI models.

    Returns a ScoreBreakdown containing a detailed explanation
    of how the routing score was calculated.
    """

    def score(
        self,
        model: AIModel,
        requirements: list[CapabilityRequirement],
        policy: RoutingPolicy,
        knowledge_base: KnowledgeBase | None = None,
    ) -> ScoreBreakdown:
        """
        Calculate a routing score for a model.
        """

        profile = model.profile

        breakdown = ScoreBreakdown()

        # ---------------------------------------------------------
        # Streaming
        # ---------------------------------------------------------

        if profile.supports_streaming:
            breakdown.streaming_score = policy.streaming_weight

            breakdown.reasons.append(
                "Supports streaming"
            )

        # ---------------------------------------------------------
        # Context Window
        # ---------------------------------------------------------

        if profile.context_window:

            breakdown.context_window_score = (
                profile.context_window
                * policy.context_window_weight
            )

            breakdown.reasons.append(
                f"Context window: {profile.context_window}"
            )

        # ---------------------------------------------------------
        # Available Model Capabilities
        # ---------------------------------------------------------

        model_capabilities = {
            capability.type
            for capability in profile.capabilities
        }

        # ---------------------------------------------------------
        # Match Requested Capabilities
        # ---------------------------------------------------------

        for requirement in requirements:

            if requirement.capability not in model_capabilities:
                continue

            weight = (
                policy.capability_weights.get(
                    requirement.capability,
                    0.0,
                )
                * requirement.weight
            )

            breakdown.capability_score += weight

            breakdown.matched_capabilities.append(
                requirement.capability.value
            )

            breakdown.reasons.append(
                f"Matched capability: {requirement.capability.value}"
            )

        # ---------------------------------------------------------
        # Benchmarked Throughput
        # ---------------------------------------------------------

        if knowledge_base is not None:
            result = knowledge_base.latest(model.id)

            if result is not None:
                breakdown.benchmark_score = (
                    result.tokens_per_second
                    * policy.benchmark_weight
                )

                breakdown.reasons.append(
                    f"Benchmark: {result.tokens_per_second:.1f} tok/s"
                )

        # ---------------------------------------------------------
        # Already Loaded
        # ---------------------------------------------------------

        if model.loaded:
            breakdown.loaded_bonus_score = policy.loaded_bonus_weight

            breakdown.reasons.append(
                "Already loaded"
            )

        # ---------------------------------------------------------
        # Final Score
        # ---------------------------------------------------------

        breakdown.total_score = (
            breakdown.capability_score
            + breakdown.streaming_score
            + breakdown.context_window_score
            + breakdown.benchmark_score
            + breakdown.loaded_bonus_score
        )

        return breakdown


model_scorer = ModelScorer()
