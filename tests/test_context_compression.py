import asyncio

from app.execution.context_compression import (
    ContextCompressor,
    estimate_tokens,
    needs_compression,
)
from app.execution.conversation import ChatMessage
from app.providers.completion_result import CompletionResult
from app.registry.provider_registry import ProviderRegistry
from tests.conftest import FAKE_MODELS, FakeProvider


def _messages(n: int, words_per_message: int = 20) -> list[ChatMessage]:
    return [
        ChatMessage(
            role="user" if i % 2 == 0 else "assistant",
            content=" ".join(["word"] * words_per_message) + f" turn {i}",
        )
        for i in range(n)
    ]


def test_estimate_tokens_is_roughly_length_over_four():
    assert estimate_tokens("a" * 400) == 100


def test_estimate_tokens_never_returns_zero_for_nonempty_text():
    assert estimate_tokens("hi") >= 1


def test_needs_compression_false_when_well_under_threshold():
    messages = _messages(2, words_per_message=5)

    assert needs_compression(messages, context_window=100_000, threshold=0.8) is False


def test_needs_compression_true_when_over_threshold():
    messages = _messages(50, words_per_message=100)

    assert needs_compression(messages, context_window=4096, threshold=0.8) is True


def test_needs_compression_false_for_unknown_context_window():
    messages = _messages(50, words_per_message=50)

    assert needs_compression(messages, context_window=0, threshold=0.8) is False


def test_compress_is_a_noop_when_under_the_keep_threshold():
    messages = _messages(4)
    registry = ProviderRegistry()
    compressor = ContextCompressor(provider_registry=registry)

    result = asyncio.run(compressor.compress(messages, keep_recent_turns=6, summarizer_model_id=""))

    assert result == messages


def test_compress_without_summarizer_truncates_with_a_marker():
    messages = _messages(20)
    registry = ProviderRegistry()
    compressor = ContextCompressor(provider_registry=registry)

    result = asyncio.run(
        compressor.compress(messages, keep_recent_turns=6, summarizer_model_id="")
    )

    assert len(result) == 7  # 1 marker + 6 kept
    assert "omitted" in result[0].content
    assert result[1:] == messages[-6:]


def test_compress_preserves_system_messages_verbatim():
    messages = [
        ChatMessage(role="system", content="You are a helpful assistant."),
        *_messages(20),
    ]
    registry = ProviderRegistry()
    compressor = ContextCompressor(provider_registry=registry)

    result = asyncio.run(
        compressor.compress(messages, keep_recent_turns=6, summarizer_model_id="")
    )

    assert result[0].role == "system"
    assert result[0].content == "You are a helpful assistant."


def test_compress_with_configured_summarizer_uses_real_summary():
    model = FAKE_MODELS[0]
    provider = FakeProvider(
        [model],
        completions={
            model.id: CompletionResult(
                text="They discussed the project's architecture.",
                completion_tokens=8,
                latency_seconds=0.1,
            )
        },
    )
    registry = ProviderRegistry()
    registry.register(provider)
    compressor = ContextCompressor(provider_registry=registry)

    result = asyncio.run(
        compressor.compress(
            _messages(20), keep_recent_turns=6, summarizer_model_id=model.id
        )
    )

    assert "architecture" in result[0].content
    assert "[Earlier conversation summary]" in result[0].content


def test_compress_falls_back_to_truncation_when_summarizer_model_missing():
    registry = ProviderRegistry()
    registry.register(FakeProvider([FAKE_MODELS[0]]))
    compressor = ContextCompressor(provider_registry=registry)

    result = asyncio.run(
        compressor.compress(
            _messages(20), keep_recent_turns=6, summarizer_model_id="no-such-model"
        )
    )

    assert "omitted" in result[0].content


def test_compress_falls_back_to_truncation_when_summarizer_call_fails():
    model = FAKE_MODELS[0]
    registry = ProviderRegistry()
    registry.register(FakeProvider([model], failures={model.id}))
    compressor = ContextCompressor(provider_registry=registry)

    result = asyncio.run(
        compressor.compress(
            _messages(20), keep_recent_turns=6, summarizer_model_id=model.id
        )
    )

    assert "omitted" in result[0].content
