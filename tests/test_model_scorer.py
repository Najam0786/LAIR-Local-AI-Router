from app.benchmarking.benchmark_result import BenchmarkResult
from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.capabilities.requirement import CapabilityRequirement
from app.hardware.hardware_profile import HardwareProfile
from app.hardware.power import PowerState
from app.hardware.resource_profile import ResourceProfile
from app.hardware.tier import HardwareTier
from app.knowledge.knowledge_base import KnowledgeBase
from app.models.ai_model import AIModel
from app.providers.model_metadata import ModelMetadata
from app.registry.community_scores import CommunityScoreEntry, CommunityScoreTable
from app.routing.complexity import ComplexityAssessment
from app.routing.model_scorer import model_scorer
from app.routing.policy import RoutingPolicy
from app.routing.provenance import Provenance


def _model_with_metadata(metadata: ModelMetadata) -> AIModel:
    return AIModel(
        id="m",
        provider="test",
        loaded=False,
        profile=CapabilityProfile(
            model_id="m",
            provider="test",
            capabilities=[],
        ),
        metadata=metadata,
    )


def _model(
    capabilities: list[Capability],
    supports_streaming: bool,
    context_window: int | None,
    loaded: bool = False,
) -> AIModel:
    return AIModel(
        id="m",
        provider="test",
        loaded=loaded,
        profile=CapabilityProfile(
            model_id="m",
            provider="test",
            capabilities=capabilities,
            supports_streaming=supports_streaming,
            context_window=context_window,
        ),
    )


def test_scores_streaming_support():
    policy = RoutingPolicy()
    model = _model([], supports_streaming=True, context_window=None)

    breakdown = model_scorer.score(model, [], policy)

    assert breakdown.streaming_score == policy.streaming_weight
    assert breakdown.total_score == policy.streaming_weight


def test_loaded_model_gets_bonus_score():
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=None, loaded=True)

    breakdown = model_scorer.score(model, [], policy)

    assert breakdown.loaded_bonus_score == policy.loaded_bonus_weight
    assert breakdown.total_score == policy.loaded_bonus_weight
    assert "Already loaded" in breakdown.reasons


def test_unloaded_model_gets_no_bonus_score():
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=None, loaded=False)

    breakdown = model_scorer.score(model, [], policy)

    assert breakdown.loaded_bonus_score == 0.0
    assert "Already loaded" not in breakdown.reasons


def test_scores_context_window():
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=1000)

    breakdown = model_scorer.score(model, [], policy)

    assert breakdown.context_window_score == 1000 * policy.context_window_weight


def test_uses_policy_capability_weights():
    policy = RoutingPolicy(capability_weights={CapabilityType.CODING: 20.0})
    model = _model(
        [Capability(type=CapabilityType.CODING)],
        supports_streaming=False,
        context_window=None,
    )
    requirements = [CapabilityRequirement(capability=CapabilityType.CODING, weight=2.0)]

    breakdown = model_scorer.score(model, requirements, policy)

    assert breakdown.capability_score == 40.0
    assert "coding" in breakdown.matched_capabilities


def test_unmatched_requirement_contributes_nothing():
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=None)
    requirements = [CapabilityRequirement(capability=CapabilityType.VISION)]

    breakdown = model_scorer.score(model, requirements, policy)

    assert breakdown.capability_score == 0.0
    assert breakdown.matched_capabilities == []


def test_no_knowledge_base_contributes_no_benchmark_score():
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=None)

    breakdown = model_scorer.score(model, [], policy, knowledge_base=None)

    assert breakdown.benchmark_score == 0.0


def test_high_complexity_boosts_reasoning_capable_model():
    policy = RoutingPolicy()
    model = _model(
        [Capability(type=CapabilityType.REASONING)],
        supports_streaming=False,
        context_window=None,
    )
    hard = ComplexityAssessment(level=5, reasons=["test"])

    breakdown = model_scorer.score(model, [], policy, complexity=hard)

    assert breakdown.complexity_score == 5 * policy.complexity_weight
    assert breakdown.total_score == breakdown.complexity_score
    assert any("Complexity 5/5" in reason for reason in breakdown.reasons)


def test_high_complexity_gives_no_bonus_to_non_reasoning_model():
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=None)
    hard = ComplexityAssessment(level=5, reasons=["test"])

    breakdown = model_scorer.score(model, [], policy, complexity=hard)

    assert breakdown.complexity_score == 0.0


def test_low_complexity_gives_no_bonus_even_to_reasoning_model():
    policy = RoutingPolicy()
    model = _model(
        [Capability(type=CapabilityType.REASONING)],
        supports_streaming=False,
        context_window=None,
    )
    easy = ComplexityAssessment(level=1, reasons=["test"])

    breakdown = model_scorer.score(model, [], policy, complexity=easy)

    assert breakdown.complexity_score == 0.0


def test_no_complexity_assessment_contributes_nothing():
    policy = RoutingPolicy()
    model = _model(
        [Capability(type=CapabilityType.REASONING)],
        supports_streaming=False,
        context_window=None,
    )

    breakdown = model_scorer.score(model, [], policy, complexity=None)

    assert breakdown.complexity_score == 0.0


def test_efficient_quant_gets_a_scoring_bonus():
    policy = RoutingPolicy()
    model = _model_with_metadata(ModelMetadata(quantization="Q4_K_M"))

    breakdown = model_scorer.score(model, [], policy)

    assert breakdown.quant_efficiency_score == policy.quant_efficiency_weight
    assert any("Q4_K_M selected" in reason for reason in breakdown.reasons)


def test_inefficient_quant_gets_no_bonus_but_is_still_explained():
    policy = RoutingPolicy()
    model = _model_with_metadata(ModelMetadata(quantization="F16"))

    breakdown = model_scorer.score(model, [], policy)

    assert breakdown.quant_efficiency_score == 0.0
    assert any("F16 selected" in reason for reason in breakdown.reasons)


def test_no_quantization_metadata_contributes_no_quant_factor():
    policy = RoutingPolicy()
    model = _model_with_metadata(ModelMetadata(quantization=None))

    breakdown = model_scorer.score(model, [], policy)

    assert breakdown.quant_efficiency_score == 0.0
    assert not any("selected" in reason for reason in breakdown.reasons)


def test_quant_explanation_names_estimated_and_free_ram():
    policy = RoutingPolicy()
    model = _model_with_metadata(ModelMetadata(quantization="Q4_K_M"))
    resource_profile = ResourceProfile(estimated_ram_gb=19.6)
    hardware = HardwareProfile(total_ram_gb=32.0, available_ram_gb=24.0)

    breakdown = model_scorer.score(
        model, [], policy, resource_profile=resource_profile, hardware=hardware
    )

    reason = next(r for r in breakdown.reasons if "selected" in r)
    assert "19.6GB estimated" in reason
    assert "24.0GB free" in reason


def test_moe_model_explanation_notes_active_params():
    policy = RoutingPolicy()
    model = _model_with_metadata(
        ModelMetadata(quantization="Q4_K_M", is_moe=True, active_params_b=3.0)
    )

    breakdown = model_scorer.score(model, [], policy)

    reason = next(r for r in breakdown.reasons if "selected" in r)
    assert "MoE" in reason
    assert "3B active" in reason


def test_language_match_adds_score_and_explanation():
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=None)

    class _FakeTable:
        def supports(self, model_id, language_code):
            return language_code == "es"

    breakdown = model_scorer.score(
        model,
        [],
        policy,
        language_code="es",
        language_strength_table=_FakeTable(),
    )

    assert breakdown.language_score == policy.language_match_weight
    assert any("'es'" in reason for reason in breakdown.reasons)


def test_language_mismatch_adds_no_score():
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=None)

    class _FakeTable:
        def supports(self, model_id, language_code):
            return False

    breakdown = model_scorer.score(
        model,
        [],
        policy,
        language_code="es",
        language_strength_table=_FakeTable(),
    )

    assert breakdown.language_score == 0.0


def test_no_language_code_contributes_nothing():
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=None)

    breakdown = model_scorer.score(model, [], policy, language_code=None)

    assert breakdown.language_score == 0.0


def test_quant_explanation_recommends_reduced_kv_precision_when_needed():
    policy = RoutingPolicy()
    model = _model_with_metadata(ModelMetadata(quantization="Q4_K_M"))
    resource_profile = ResourceProfile(
        estimated_ram_gb=17.6,
        estimated_kv_cache_gb=18.3,
        estimated_total_ram_gb=35.9,
        kv_cache_quant_recommended="int8",
    )

    breakdown = model_scorer.score(
        model, [], policy, resource_profile=resource_profile
    )

    reason = next(r for r in breakdown.reasons if "selected" in r)
    assert "KV cache" in reason
    assert "recommend int8" in reason


def test_quant_explanation_notes_when_no_kv_precision_would_fit():
    policy = RoutingPolicy()
    model = _model_with_metadata(ModelMetadata(quantization="Q4_K_M"))
    resource_profile = ResourceProfile(
        estimated_ram_gb=17.6,
        estimated_kv_cache_gb=146.3,
        estimated_total_ram_gb=163.9,
        kv_cache_quant_recommended=None,
    )

    breakdown = model_scorer.score(
        model, [], policy, resource_profile=resource_profile
    )

    reason = next(r for r in breakdown.reasons if "selected" in r)
    assert "may not fit even with reduced KV precision" in reason


def test_knowledge_base_contributes_benchmark_score(tmp_path):
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=None)

    knowledge_base = KnowledgeBase(path=tmp_path / "kb.json")
    knowledge_base.record(
        BenchmarkResult(
            run_id="test-run",
            model_id="m",
            provider="test",
            prompt="hello",
            latency_seconds=2.0,
            completion_tokens=20,
        )
    )

    breakdown = model_scorer.score(model, [], policy, knowledge_base)

    assert breakdown.benchmark_score == 10.0 * policy.benchmark_weight
    assert any("Benchmark:" in reason for reason in breakdown.reasons)


def test_community_score_fills_in_when_no_local_measurement_exists(tmp_path):
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=None)
    knowledge_base = KnowledgeBase(path=tmp_path / "kb.json")
    community_scores = CommunityScoreTable(
        [
            CommunityScoreEntry(
                model_id="m",
                hardware_tier=HardwareTier.STANDARD,
                tokens_per_second=30.0,
                sample_count=5,
            )
        ]
    )

    breakdown = model_scorer.score(
        model,
        [],
        policy,
        knowledge_base,
        community_scores=community_scores,
        hardware_tier=HardwareTier.STANDARD,
    )

    assert breakdown.benchmark_score == 30.0 * policy.benchmark_weight
    factor = next(f for f in breakdown.factors if f.name == "benchmark")
    assert factor.provenance == Provenance.COMMUNITY
    assert "Community benchmark" in factor.reason


def test_local_measurement_always_overrides_community_score(tmp_path):
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=None)
    knowledge_base = KnowledgeBase(path=tmp_path / "kb.json")
    knowledge_base.record(
        BenchmarkResult(
            run_id="local-run",
            model_id="m",
            provider="test",
            prompt="hello",
            latency_seconds=1.0,
            completion_tokens=10,
        )
    )
    community_scores = CommunityScoreTable(
        [
            CommunityScoreEntry(
                model_id="m",
                hardware_tier=HardwareTier.STANDARD,
                tokens_per_second=999.0,
            )
        ]
    )

    breakdown = model_scorer.score(
        model,
        [],
        policy,
        knowledge_base,
        community_scores=community_scores,
        hardware_tier=HardwareTier.STANDARD,
    )

    factor = next(f for f in breakdown.factors if f.name == "benchmark")
    assert factor.provenance == Provenance.MEASURED
    assert breakdown.benchmark_score == 10.0 * policy.benchmark_weight


def test_no_community_score_for_a_different_tier_contributes_nothing(tmp_path):
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=None)
    knowledge_base = KnowledgeBase(path=tmp_path / "kb.json")
    community_scores = CommunityScoreTable(
        [
            CommunityScoreEntry(
                model_id="m",
                hardware_tier=HardwareTier.ENTHUSIAST,
                tokens_per_second=999.0,
            )
        ]
    )

    breakdown = model_scorer.score(
        model,
        [],
        policy,
        knowledge_base,
        community_scores=community_scores,
        hardware_tier=HardwareTier.STANDARD,
    )

    assert breakdown.benchmark_score == 0.0


def test_on_battery_biases_toward_small_models():
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=None)
    small_profile = ResourceProfile(estimated_ram_gb=4.0)

    breakdown = model_scorer.score(
        model,
        [],
        policy,
        resource_profile=small_profile,
        power_state=PowerState(on_battery=True, battery_percent=50.0),
    )

    assert breakdown.battery_score == policy.battery_efficiency_weight
    factor = next(f for f in breakdown.factors if f.name == "battery_awareness")
    assert factor.provenance == Provenance.HEURISTIC
    assert "battery" in factor.reason.lower()


def test_on_battery_gives_no_bonus_to_large_models():
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=None)
    large_profile = ResourceProfile(estimated_ram_gb=20.0)

    breakdown = model_scorer.score(
        model,
        [],
        policy,
        resource_profile=large_profile,
        power_state=PowerState(on_battery=True, battery_percent=50.0),
    )

    assert breakdown.battery_score == 0.0


def test_plugged_in_gives_no_battery_bonus_even_for_small_models():
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=None)
    small_profile = ResourceProfile(estimated_ram_gb=4.0)

    breakdown = model_scorer.score(
        model,
        [],
        policy,
        resource_profile=small_profile,
        power_state=PowerState(on_battery=False, battery_percent=100.0),
    )

    assert breakdown.battery_score == 0.0


def test_no_power_state_never_adds_battery_bonus():
    policy = RoutingPolicy()
    model = _model([], supports_streaming=False, context_window=None)
    small_profile = ResourceProfile(estimated_ram_gb=4.0)

    breakdown = model_scorer.score(
        model, [], policy, resource_profile=small_profile
    )

    assert breakdown.battery_score == 0.0


def test_streaming_pick_is_labeled_with_a_latency_estimate():
    policy = RoutingPolicy()
    model = _model_with_metadata(ModelMetadata(streamable=True))
    hardware = HardwareProfile(total_ram_gb=16.0, available_ram_gb=4.0)
    profile = ResourceProfile(estimated_ram_gb=16.0)

    breakdown = model_scorer.score(
        model, [], policy, resource_profile=profile, hardware=hardware
    )

    factor = next(f for f in breakdown.factors if f.name == "streaming_pick")
    assert factor.score == 0.0
    assert "4.0x slower" in factor.reason


def test_non_streamable_model_never_gets_streaming_pick_factor():
    policy = RoutingPolicy()
    model = _model_with_metadata(ModelMetadata(streamable=False))
    hardware = HardwareProfile(total_ram_gb=16.0, available_ram_gb=4.0)
    profile = ResourceProfile(estimated_ram_gb=16.0)

    breakdown = model_scorer.score(
        model, [], policy, resource_profile=profile, hardware=hardware
    )

    assert not any(f.name == "streaming_pick" for f in breakdown.factors)


def test_streamable_model_that_fits_normally_gets_no_streaming_pick_factor():
    policy = RoutingPolicy()
    model = _model_with_metadata(ModelMetadata(streamable=True))
    hardware = HardwareProfile(total_ram_gb=16.0, available_ram_gb=8.0)
    profile = ResourceProfile(estimated_ram_gb=4.0)

    breakdown = model_scorer.score(
        model, [], policy, resource_profile=profile, hardware=hardware
    )

    assert not any(f.name == "streaming_pick" for f in breakdown.factors)
