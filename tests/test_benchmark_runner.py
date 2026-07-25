import asyncio

from app.benchmarking.runner import BenchmarkRunner
from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.knowledge.knowledge_base import KnowledgeBase
from app.models.ai_model import AIModel
from app.providers.completion_result import CompletionResult
from app.registry.provider_registry import ProviderRegistry
from tests.conftest import FakeProvider


def _model(model_id: str) -> AIModel:
    return AIModel(
        id=model_id,
        provider="fake",
        profile=CapabilityProfile(
            model_id=model_id,
            provider="fake",
            capabilities=[Capability(type=CapabilityType.TEXT_GENERATION)],
        ),
    )


def test_runner_records_successes_and_skips_failures(tmp_path):
    good = _model("good-model")
    bad = _model("bad-model")

    provider = FakeProvider(
        [good, bad],
        completions={
            "good-model": CompletionResult(
                text="hello world", completion_tokens=10, latency_seconds=1.0
            ),
        },
        failures={"bad-model"},
    )

    registry = ProviderRegistry()
    registry.register(provider)

    knowledge_base = KnowledgeBase(path=tmp_path / "kb.json")
    runner = BenchmarkRunner(provider_registry=registry, knowledge_base=knowledge_base)

    results = asyncio.run(runner.run([good, bad], prompt="hi"))

    assert [r.model_id for r in results] == ["good-model"]
    assert knowledge_base.latest("good-model") is not None
    assert knowledge_base.latest("bad-model") is None
