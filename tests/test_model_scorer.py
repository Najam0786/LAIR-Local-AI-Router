from app.benchmarking.benchmark_result import BenchmarkResult
from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.capabilities.requirement import CapabilityRequirement
from app.knowledge.knowledge_base import KnowledgeBase
from app.models.ai_model import AIModel
from app.routing.model_scorer import model_scorer
from app.routing.policy import RoutingPolicy


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
