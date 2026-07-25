import asyncio

from app.core.settings import settings
from app.providers.completion_result import CompletionResult
from app.registry.provider_registry import ProviderRegistry
from app.routing.complexity_classifier import (
    ClassificationCache,
    ModelAssistedComplexityClassifier,
)
from tests.conftest import FAKE_MODELS, FakeProvider


def _classifier(monkeypatch, tmp_path, completions=None, failures=None):
    monkeypatch.setattr(settings, "ENABLE_MODEL_ASSISTED_COMPLEXITY", True)
    monkeypatch.setattr(settings, "COMPLEXITY_CLASSIFIER_MODEL_ID", "qwen3-8b")

    model = FAKE_MODELS[0]  # "qwen3-8b"
    provider = FakeProvider([model], completions=completions, failures=failures)
    registry = ProviderRegistry()
    registry.register(provider)

    cache = ClassificationCache(path=tmp_path / "classifications.json")
    return ModelAssistedComplexityClassifier(provider_registry=registry, cache=cache)


def test_disabled_by_default_returns_none(tmp_path):
    registry = ProviderRegistry()
    cache = ClassificationCache(path=tmp_path / "c.json")
    classifier = ModelAssistedComplexityClassifier(
        provider_registry=registry, cache=cache
    )

    result = asyncio.run(classifier.classify("hello"))

    assert result is None


def test_enabled_but_unconfigured_model_returns_none(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "ENABLE_MODEL_ASSISTED_COMPLEXITY", True)
    monkeypatch.setattr(settings, "COMPLEXITY_CLASSIFIER_MODEL_ID", "")

    registry = ProviderRegistry()
    cache = ClassificationCache(path=tmp_path / "c.json")
    classifier = ModelAssistedComplexityClassifier(
        provider_registry=registry, cache=cache
    )

    result = asyncio.run(classifier.classify("hello"))

    assert result is None


def test_valid_json_response_is_parsed(monkeypatch, tmp_path):
    classifier = _classifier(
        monkeypatch,
        tmp_path,
        completions={
            "qwen3-8b": CompletionResult(
                text='{"complexity": 4, "task_type": "refactor"}',
                completion_tokens=10,
                latency_seconds=0.1,
            )
        },
    )

    result = asyncio.run(classifier.classify("please refactor this"))

    assert result is not None
    assert result.level == 4
    assert any("refactor" in reason for reason in result.reasons)


def test_response_with_surrounding_text_is_still_parsed(monkeypatch, tmp_path):
    classifier = _classifier(
        monkeypatch,
        tmp_path,
        completions={
            "qwen3-8b": CompletionResult(
                text='Sure, here you go: {"complexity": 2, "task_type": "chat"} thanks!',
                completion_tokens=10,
                latency_seconds=0.1,
            )
        },
    )

    result = asyncio.run(classifier.classify("hi"))

    assert result is not None
    assert result.level == 2


def test_out_of_range_complexity_is_clamped(monkeypatch, tmp_path):
    classifier = _classifier(
        monkeypatch,
        tmp_path,
        completions={
            "qwen3-8b": CompletionResult(
                text='{"complexity": 99, "task_type": "chat"}',
                completion_tokens=10,
                latency_seconds=0.1,
            )
        },
    )

    result = asyncio.run(classifier.classify("hi"))

    assert result.level == 5


def test_malformed_response_falls_back_to_none(monkeypatch, tmp_path):
    classifier = _classifier(
        monkeypatch,
        tmp_path,
        completions={
            "qwen3-8b": CompletionResult(
                text="not json at all",
                completion_tokens=10,
                latency_seconds=0.1,
            )
        },
    )

    result = asyncio.run(classifier.classify("hi"))

    assert result is None


def test_provider_failure_falls_back_to_none(monkeypatch, tmp_path):
    classifier = _classifier(monkeypatch, tmp_path, failures={"qwen3-8b"})

    result = asyncio.run(classifier.classify("hi"))

    assert result is None


def test_unknown_classifier_model_falls_back_to_none(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "ENABLE_MODEL_ASSISTED_COMPLEXITY", True)
    monkeypatch.setattr(settings, "COMPLEXITY_CLASSIFIER_MODEL_ID", "no-such-model")

    registry = ProviderRegistry()
    registry.register(FakeProvider([FAKE_MODELS[0]]))
    cache = ClassificationCache(path=tmp_path / "c.json")
    classifier = ModelAssistedComplexityClassifier(
        provider_registry=registry, cache=cache
    )

    result = asyncio.run(classifier.classify("hi"))

    assert result is None


def test_second_call_is_served_from_cache_without_hitting_the_provider(
    monkeypatch, tmp_path
):
    call_count = {"n": 0}

    class _CountingProvider(FakeProvider):
        async def complete(self, *args, **kwargs):
            call_count["n"] += 1
            return await super().complete(*args, **kwargs)

    monkeypatch.setattr(settings, "ENABLE_MODEL_ASSISTED_COMPLEXITY", True)
    monkeypatch.setattr(settings, "COMPLEXITY_CLASSIFIER_MODEL_ID", "qwen3-8b")

    provider = _CountingProvider(
        [FAKE_MODELS[0]],
        completions={
            "qwen3-8b": CompletionResult(
                text='{"complexity": 3, "task_type": "chat"}',
                completion_tokens=10,
                latency_seconds=0.1,
            )
        },
    )
    registry = ProviderRegistry()
    registry.register(provider)
    cache = ClassificationCache(path=tmp_path / "c.json")
    classifier = ModelAssistedComplexityClassifier(
        provider_registry=registry, cache=cache
    )

    first = asyncio.run(classifier.classify("please refactor this"))
    second = asyncio.run(classifier.classify("please refactor this"))

    assert call_count["n"] == 1
    assert first.level == second.level == 3
    assert any("cached" in reason for reason in second.reasons)
