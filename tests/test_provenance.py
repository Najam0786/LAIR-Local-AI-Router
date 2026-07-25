import pytest
from pydantic import ValidationError

from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.capabilities.requirement import CapabilityRequirement
from app.knowledge.knowledge_base import KnowledgeBase
from app.benchmarking.benchmark_result import BenchmarkResult
from app.models.ai_model import AIModel
from app.routing.model_scorer import model_scorer
from app.routing.policy import RoutingPolicy
from app.routing.provenance import Provenance
from app.routing.score_breakdown import ScoreBreakdown, ScoreFactor


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


def test_score_factor_requires_provenance():
    with pytest.raises(ValidationError):
        ScoreFactor(name="x", score=1.0, reason="no provenance given")


def test_add_factor_appears_in_reasons():
    breakdown = ScoreBreakdown()
    breakdown.add_factor(
        name="custom",
        score=5.0,
        provenance=Provenance.HEURISTIC,
        reason="Custom heuristic bonus",
    )

    assert breakdown.reasons == ["Custom heuristic bonus"]
    assert breakdown.factors[0].provenance == Provenance.HEURISTIC


def test_every_scored_factor_is_tagged_with_a_valid_provenance(tmp_path):
    policy = RoutingPolicy()
    model = _model(
        [Capability(type=CapabilityType.CODING)],
        supports_streaming=True,
        context_window=1000,
        loaded=True,
    )
    requirements = [CapabilityRequirement(capability=CapabilityType.CODING)]

    knowledge_base = KnowledgeBase(path=tmp_path / "kb.json")
    knowledge_base.record(
        BenchmarkResult(
            run_id="test-run",
            model_id="m",
            provider="test",
            prompt="hello",
            latency_seconds=1.0,
            completion_tokens=10,
        )
    )

    breakdown = model_scorer.score(model, requirements, policy, knowledge_base)

    # Every factor produced by a real scoring pass must carry a provenance
    # tag drawn from the closed Provenance enum -- nothing untagged.
    assert len(breakdown.factors) >= 4
    for factor in breakdown.factors:
        assert isinstance(factor.provenance, Provenance)

    provenances = {factor.name: factor.provenance for factor in breakdown.factors}
    assert provenances["streaming"] == Provenance.DECLARED
    assert provenances["context_window"] == Provenance.DECLARED
    assert provenances["capability:coding"] == Provenance.DECLARED
    assert provenances["benchmark"] == Provenance.MEASURED
    assert provenances["loaded_bonus"] == Provenance.HEURISTIC
