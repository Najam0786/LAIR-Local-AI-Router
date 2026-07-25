from app.capabilities.capability import CapabilityType
from app.capabilities.requirement import CapabilityRequirement
from app.hardware.hardware_profile import HardwareProfile
from app.hardware.power import BATTERY_SMALL_MODEL_RAM_THRESHOLD_GB, PowerState
from app.hardware.resource_profile import ResourceProfile
from app.hardware.tier import HardwareTier
from app.knowledge.knowledge_base import KnowledgeBase
from app.models.ai_model import AIModel
from app.registry.community_scores import CommunityScoreTable
from app.registry.language_strengths import (
    LanguageStrengthTable,
    default_language_strength_table,
)
from app.routing.complexity import ComplexityAssessment
from app.routing.policy import RoutingPolicy
from app.routing.provenance import Provenance
from app.routing.score_breakdown import ScoreBreakdown

# Quantization families judged "memory-efficient" -- the Q4_K_M-and-
# smaller sweet spot research shows as near-indistinguishable quality
# at a fraction of the memory of Q8/F16 (docs/INNOVATION_PLAN_2026.md
# section 1.1). Used only to break ties between candidates that
# already fit available memory (I-03) -- filter_by_hardware(), not
# this bonus, is what enforces the hard fit constraint.
_MEMORY_EFFICIENT_QUANT_PREFIXES = ("Q2", "Q3", "Q4")


def _is_memory_efficient_quant(quantization: str) -> bool:
    return quantization.upper().startswith(_MEMORY_EFFICIENT_QUANT_PREFIXES)


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
        complexity: ComplexityAssessment | None = None,
        resource_profile: ResourceProfile | None = None,
        hardware: HardwareProfile | None = None,
        language_code: str | None = None,
        language_strength_table: LanguageStrengthTable | None = None,
        community_scores: CommunityScoreTable | None = None,
        hardware_tier: HardwareTier | None = None,
        power_state: PowerState | None = None,
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

            breakdown.add_factor(
                name="streaming",
                score=breakdown.streaming_score,
                provenance=Provenance.DECLARED,
                reason="Supports streaming",
            )

        # ---------------------------------------------------------
        # Context Window
        # ---------------------------------------------------------

        if profile.context_window:

            breakdown.context_window_score = (
                profile.context_window
                * policy.context_window_weight
            )

            breakdown.add_factor(
                name="context_window",
                score=breakdown.context_window_score,
                provenance=Provenance.DECLARED,
                reason=f"Context window: {profile.context_window}",
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

            breakdown.add_factor(
                name=f"capability:{requirement.capability.value}",
                score=weight,
                provenance=Provenance.DECLARED,
                reason=f"Matched capability: {requirement.capability.value}",
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

                breakdown.add_factor(
                    name="benchmark",
                    score=breakdown.benchmark_score,
                    provenance=Provenance.MEASURED,
                    reason=f"Benchmark: {result.tokens_per_second:.1f} tok/s",
                )
            elif community_scores is not None and hardware_tier is not None:
                # I-12: no local measurement exists for this model on
                # this machine -- fall back to an anonymized community
                # data point for the same hardware tier, tagged
                # COMMUNITY so it's never confused with a real local
                # measurement. A local MEASURED result always wins
                # (this branch is unreachable when one exists, above).
                community_entry = community_scores.for_model_and_tier(
                    model.id, hardware_tier
                )

                if community_entry is not None:
                    breakdown.benchmark_score = (
                        community_entry.tokens_per_second
                        * policy.benchmark_weight
                    )

                    breakdown.add_factor(
                        name="benchmark",
                        score=breakdown.benchmark_score,
                        provenance=Provenance.COMMUNITY,
                        reason=(
                            f"Community benchmark: "
                            f"{community_entry.tokens_per_second:.1f} tok/s "
                            f"({hardware_tier.value} tier, "
                            f"{community_entry.sample_count} contributor(s))"
                        ),
                    )

        # ---------------------------------------------------------
        # Complexity Triage (I-04)
        # ---------------------------------------------------------
        #
        # Difficulty-aware routing (RouteLLM/HybridLLM, see
        # docs/INNOVATION_PLAN_2026.md §1.4): a hard request should
        # prefer a reasoning-capable specialist. Deliberately one-sided
        # -- an easy request gets no penalty against any model here,
        # since other factors (benchmark speed, loaded bonus) already
        # do the job of preferring the cheaper/faster candidate.

        if (
            complexity is not None
            and complexity.level >= policy.complexity_reasoning_threshold
            and CapabilityType.REASONING in model_capabilities
        ):
            breakdown.complexity_score = (
                complexity.level * policy.complexity_weight
            )

            breakdown.add_factor(
                name="complexity",
                score=breakdown.complexity_score,
                provenance=Provenance.HEURISTIC,
                reason=(
                    f"Complexity {complexity.level}/5: reasoning-capable "
                    "model preferred for this hard task"
                ),
            )

        # ---------------------------------------------------------
        # Quantization Fit (I-03)
        # ---------------------------------------------------------
        #
        # Purely a tie-breaking preference among candidates that already
        # passed filter_by_hardware()'s hard fit check -- prefer a
        # memory-efficient quant (e.g. a bigger model at Q4 over a
        # smaller one at Q8, within budget) without ever claiming a
        # quant "fits" here; that determination stays the filter's job.

        quantization = model.metadata.quantization if model.metadata else None

        if quantization is not None:
            if _is_memory_efficient_quant(quantization):
                breakdown.quant_efficiency_score = policy.quant_efficiency_weight

            fit_note = ""
            if resource_profile is not None and resource_profile.estimated_ram_gb is not None:
                fit_note = f", ~{resource_profile.estimated_ram_gb:.1f}GB estimated"
                if hardware is not None:
                    fit_note += f", {hardware.available_ram_gb:.1f}GB free"

            # KV cache at the model's configured context length (I-17).
            # A recommendation only -- LAIR doesn't set this on the
            # backend, since no verified LM Studio request-level API
            # exposes KV-cache precision the way `ttl`/`draft_model` do.
            kv_note = ""
            if resource_profile is not None and resource_profile.estimated_kv_cache_gb is not None:
                kv_note = (
                    f", ~{resource_profile.estimated_kv_cache_gb:.1f}GB fp16 "
                    "KV cache at full context"
                )
                recommended = resource_profile.kv_cache_quant_recommended
                if recommended is None:
                    kv_note += " (may not fit even with reduced KV precision)"
                elif recommended != "fp16":
                    kv_note += (
                        f" -- recommend {recommended} KV cache in LM Studio "
                        "to comfortably fit full context"
                    )

            moe_note = ""
            if model.metadata and model.metadata.is_moe:
                active = model.metadata.active_params_b
                moe_note = (
                    f" (MoE, ~{active:.0f}B active params -- may fit "
                    "better with expert-offload enabled in LM Studio)"
                    if active is not None
                    else " (MoE)"
                )

            breakdown.add_factor(
                name="quant_fit",
                score=breakdown.quant_efficiency_score,
                provenance=Provenance.DECLARED,
                reason=f"{quantization} selected{fit_note}{kv_note}{moe_note}",
            )

        # ---------------------------------------------------------
        # Language Fit (I-10)
        # ---------------------------------------------------------
        #
        # Detected once per request in RoutingEngine.route() (never
        # guessed per-model here) and matched against each model's
        # declared language support -- a user writing in Hindi or
        # Arabic silently gets the model documented as strongest in
        # that language, per docs/INNOVATION_PLAN_2026.md I-10.

        if language_code is not None:
            language_strength_table = (
                language_strength_table or default_language_strength_table
            )

            if language_strength_table.supports(model.id, language_code):
                breakdown.language_score = policy.language_match_weight

                breakdown.add_factor(
                    name="language_fit",
                    score=breakdown.language_score,
                    provenance=Provenance.DECLARED,
                    reason=f"Declared strong in detected language '{language_code}'",
                )

        # ---------------------------------------------------------
        # Streaming Pick Labeling (I-16, ADR-0021)
        # ---------------------------------------------------------
        #
        # Purely explanatory -- filter_by_hardware() already decided
        # whether to admit this candidate at all via the SSD-streaming
        # allowance; this only makes that choice visible, with a
        # latency estimate, rather than silently blending it in among
        # normal candidates. No score bonus: being admitted at all
        # (only when nothing else fits) is discouragement enough.

        if (
            model.metadata is not None
            and model.metadata.streamable
            and resource_profile is not None
            and resource_profile.effective_ram_gb is not None
            and hardware is not None
            and resource_profile.effective_ram_gb > hardware.available_ram_gb
        ):
            estimated_latency_multiplier = resource_profile.effective_ram_gb / max(
                hardware.available_ram_gb, 0.01
            )

            breakdown.add_factor(
                name="streaming_pick",
                score=0.0,
                provenance=Provenance.HEURISTIC,
                reason=(
                    "Exceeds available RAM -- offered via SSD streaming, "
                    f"est. {estimated_latency_multiplier:.1f}x slower"
                ),
            )

        # ---------------------------------------------------------
        # Battery Awareness (I-15)
        # ---------------------------------------------------------
        #
        # On battery power, bias toward smaller/faster models -- a
        # laptop running on its battery is the primary audience this
        # is for. A no-op (power_state is None, or on_battery=False on
        # a desktop) leaves total_score identical to pre-I-15 LAIR.

        if (
            power_state is not None
            and power_state.on_battery
            and resource_profile is not None
            and resource_profile.estimated_ram_gb is not None
            and resource_profile.estimated_ram_gb <= BATTERY_SMALL_MODEL_RAM_THRESHOLD_GB
        ):
            breakdown.battery_score = policy.battery_efficiency_weight

            breakdown.add_factor(
                name="battery_awareness",
                score=breakdown.battery_score,
                provenance=Provenance.HEURISTIC,
                reason=(
                    "On battery power: smaller/faster model preferred "
                    f"(~{resource_profile.estimated_ram_gb:.1f}GB estimated)"
                ),
            )

        # ---------------------------------------------------------
        # Already Loaded
        # ---------------------------------------------------------

        if model.loaded:
            breakdown.loaded_bonus_score = policy.loaded_bonus_weight

            breakdown.add_factor(
                name="loaded_bonus",
                score=breakdown.loaded_bonus_score,
                provenance=Provenance.HEURISTIC,
                reason="Already loaded",
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
            + breakdown.complexity_score
            + breakdown.quant_efficiency_score
            + breakdown.language_score
            + breakdown.battery_score
        )

        return breakdown


model_scorer = ModelScorer()
