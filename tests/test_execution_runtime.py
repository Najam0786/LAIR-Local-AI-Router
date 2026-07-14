import asyncio

from app.execution.conversation import ChatMessage
from app.execution.runtime import execute
from app.providers.completion_result import CompletionResult
from tests.conftest import FAKE_MODELS, FakeProvider


def test_execute_success_returns_populated_result_and_outcome(clean_registry):
    model = FAKE_MODELS[1]  # qwen2.5-coder-32b
    provider = FakeProvider(
        [model],
        completions={
            model.id: CompletionResult(
                text="hello",
                completion_tokens=3,
                latency_seconds=0.25,
                prompt_tokens=10,
                finish_reason="stop",
            )
        },
    )
    clean_registry.register(provider)

    result, outcome = asyncio.run(
        execute(model, [ChatMessage(role="user", content="hi")], max_tokens=64)
    )

    assert result is not None
    assert result.text == "hello"
    assert outcome.success is True
    assert outcome.completion_tokens == 3
    assert outcome.prompt_tokens == 10
    assert outcome.finish_reason == "stop"
    assert outcome.latency_ms == 250.0


def test_execute_failure_returns_none_result_and_failed_outcome(clean_registry):
    model = FAKE_MODELS[1]
    provider = FakeProvider([model], failures={model.id})
    clean_registry.register(provider)

    result, outcome = asyncio.run(
        execute(model, [ChatMessage(role="user", content="hi")], max_tokens=64)
    )

    assert result is None
    assert outcome.success is False
    assert "simulated failure" in outcome.error
