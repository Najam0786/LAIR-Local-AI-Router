import pytest

from app.hardware.tier import HardwareTier
from app.registry.portfolio import Portfolio, PortfolioLoader, PortfolioStore


@pytest.mark.parametrize("tier", list(HardwareTier))
def test_every_tier_has_a_loadable_portfolio_file(tier):
    portfolio = PortfolioLoader().load(tier)

    assert portfolio is not None
    assert portfolio.tier == tier
    assert portfolio.default_context_length > 0
    assert len(portfolio.models) > 0


def test_cpu_only_portfolio_uses_small_models_and_conservative_context():
    portfolio = PortfolioLoader().load(HardwareTier.CPU_ONLY)

    # "Working configuration" per I-02's acceptance criteria: small
    # models (parseable size <= 8B) and a conservative context length.
    assert portfolio.default_context_length <= 4096

    for model in portfolio.models:
        assert any(
            size in model.name for size in ("3B", "3.8B", "4B")
        ) or "mini" in model.name.lower()


@pytest.mark.parametrize(
    "tier,expected",
    [
        (HardwareTier.ENTRY, "int8"),
        (HardwareTier.CPU_ONLY, "int8"),
        (HardwareTier.STANDARD, "fp16"),
        (HardwareTier.ENTHUSIAST, "fp16"),
    ],
)
def test_portfolios_recommend_kv_cache_precision_per_tier(tier, expected):
    # I-17: constrained tiers recommend int8 KV to stretch usable
    # context; well-resourced tiers keep full fp16 precision.
    portfolio = PortfolioLoader().load(tier)

    assert portfolio.kv_cache_recommendation == expected


def test_loader_returns_none_for_missing_tier_file(tmp_path):
    loader = PortfolioLoader(directory=tmp_path)

    assert loader.load(HardwareTier.ENTRY) is None


def test_store_round_trip(tmp_path):
    store = PortfolioStore(path=tmp_path / "active_portfolio.yaml")
    original = PortfolioLoader().load(HardwareTier.STANDARD)

    assert store.load() is None

    store.save(original)
    loaded = store.load()

    assert loaded == original


def test_streaming_viability_round_trips_through_the_store(tmp_path):
    store = PortfolioStore(path=tmp_path / "active_portfolio.yaml")
    original = PortfolioLoader().load(HardwareTier.STANDARD)

    store.save(original.model_copy(update={"streaming_viability": 0.75}))
    loaded = store.load()

    assert loaded.streaming_viability == 0.75


def test_streaming_viability_defaults_to_none():
    portfolio = PortfolioLoader().load(HardwareTier.STANDARD)

    assert portfolio.streaming_viability is None
