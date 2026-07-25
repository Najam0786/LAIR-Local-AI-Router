from app.hardware.tier import HardwareTier
from app.knowledge.knowledge_base import KnowledgeBase
from app.models.task import Task
from app.registry.community_scores import CommunityScoreEntry, CommunityScoreTable
from app.registry.portfolio import Portfolio, PortfolioModel
import app.routing.routing_engine as routing_engine_module
from app.routing.routing_engine import RoutingEngine
from tests.conftest import FAKE_MODELS


class _FakePortfolioStore:
    def __init__(self, portfolio):
        self._portfolio = portfolio

    def load(self):
        return self._portfolio


def _portfolio(tier: HardwareTier) -> Portfolio:
    return Portfolio(
        tier=tier,
        description="test",
        default_context_length=4096,
        models=[PortfolioModel(name="m", lm_studio_search="m", role="general")],
    )


def test_active_portfolio_tier_used_for_community_score_lookup(monkeypatch, tmp_path):
    model = FAKE_MODELS[0]
    monkeypatch.setattr(
        routing_engine_module,
        "default_portfolio_store",
        _FakePortfolioStore(_portfolio(HardwareTier.STANDARD)),
    )

    community_scores = CommunityScoreTable(
        [
            CommunityScoreEntry(
                model_id=model.id,
                hardware_tier=HardwareTier.STANDARD,
                tokens_per_second=55.0,
            )
        ]
    )

    engine = RoutingEngine()
    plan = engine.route(
        task=Task(prompt="hello there, general question"),
        models=[model],
        knowledge_base=KnowledgeBase(path=tmp_path / "kb.json"),
        community_scores=community_scores,
    )

    winner = plan.decision.candidates[0]
    factor = next(f for f in winner.breakdown.factors if f.name == "benchmark")
    assert "Community benchmark" in factor.reason


def test_no_active_portfolio_means_no_community_fallback(monkeypatch, tmp_path):
    model = FAKE_MODELS[0]
    monkeypatch.setattr(
        routing_engine_module,
        "default_portfolio_store",
        _FakePortfolioStore(None),
    )

    community_scores = CommunityScoreTable(
        [
            CommunityScoreEntry(
                model_id=model.id,
                hardware_tier=HardwareTier.STANDARD,
                tokens_per_second=55.0,
            )
        ]
    )

    engine = RoutingEngine()
    plan = engine.route(
        task=Task(prompt="hello there, general question"),
        models=[model],
        knowledge_base=KnowledgeBase(path=tmp_path / "kb.json"),
        community_scores=community_scores,
    )

    winner = plan.decision.candidates[0]
    assert not any(f.name == "benchmark" for f in winner.breakdown.factors)
