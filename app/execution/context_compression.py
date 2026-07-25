import logging

from app.execution.conversation import ChatMessage
from app.registry.provider_registry import ProviderRegistry
from app.registry.provider_registry import provider_registry as _default_registry

logger = logging.getLogger(__name__)

# Rough, widely-used rule of thumb (~4 characters per token for
# English text) -- no real tokenizer is wired in anywhere in LAIR
# today, and pulling one in just to estimate context fill would be a
# heavy new dependency for a single heuristic. Good enough to decide
# "are we approaching the limit," not meant as an exact count.
_CHARS_PER_TOKEN_ESTIMATE = 4

_SUMMARIZATION_PROMPT_TEMPLATE = (
    "Summarize the following earlier conversation turns concisely, "
    "preserving any facts, decisions, or constraints that later turns "
    "might depend on. Respond with ONLY the summary text.\n\n{transcript}"
)

_SUMMARIZER_MAX_TOKENS = 200


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN_ESTIMATE)


def _conversation_token_estimate(messages: list[ChatMessage]) -> int:
    return sum(estimate_tokens(message.content) for message in messages)


def needs_compression(
    messages: list[ChatMessage],
    context_window: int,
    threshold: float,
) -> bool:
    """
    True once the conversation's estimated token count reaches
    `threshold` (default 0.8) of the model's context window (I-09).
    """

    if context_window <= 0:
        return False

    return _conversation_token_estimate(messages) / context_window >= threshold


class ContextCompressor:
    """
    Summarizes (or, failing that, truncates) older conversation turns
    once a request approaches the selected model's context limit.

    The most recent `keep_recent_turns` messages are always preserved
    verbatim. When a summarizer model is configured and reachable, the
    older turns are condensed into one marked summary message; when
    not, they're dropped with an explicit marker instead -- never
    silently, and never by fabricating a "summary" LAIR didn't
    actually produce.
    """

    def __init__(self, provider_registry: ProviderRegistry = _default_registry):
        self._provider_registry = provider_registry

    async def compress(
        self,
        messages: list[ChatMessage],
        keep_recent_turns: int,
        summarizer_model_id: str,
    ) -> list[ChatMessage]:
        system_messages = [m for m in messages if m.role == "system"]
        rest = [m for m in messages if m.role != "system"]

        if len(rest) <= keep_recent_turns:
            return messages

        older = rest[:-keep_recent_turns] if keep_recent_turns > 0 else rest
        recent = rest[-keep_recent_turns:] if keep_recent_turns > 0 else []

        summary_text = await self._summarize(older, summarizer_model_id)

        marker = ChatMessage(
            role="system",
            content=(
                f"[Earlier conversation summary]: {summary_text}"
                if summary_text is not None
                else f"[{len(older)} earlier message(s) omitted to fit "
                "the model's context window]"
            ),
        )

        return [*system_messages, marker, *recent]

    async def _summarize(
        self, older: list[ChatMessage], summarizer_model_id: str
    ) -> str | None:
        if not summarizer_model_id or not older:
            return None

        models = await self._provider_registry.list_models()
        model = next((m for m in models if m.id == summarizer_model_id), None)

        if model is None:
            logger.warning(
                "Context compression summarizer model '%s' not found; "
                "falling back to truncation with a marker.",
                summarizer_model_id,
            )
            return None

        transcript = "\n".join(f"{m.role}: {m.content}" for m in older)

        try:
            provider = self._provider_registry.get(model.provider)
            result = await provider.complete(
                model.id,
                [
                    {
                        "role": "user",
                        "content": _SUMMARIZATION_PROMPT_TEMPLATE.format(
                            transcript=transcript
                        ),
                    }
                ],
                max_tokens=_SUMMARIZER_MAX_TOKENS,
            )
            return result.text.strip() or None
        except Exception as exc:
            logger.warning(
                "Context compression summarization failed, falling back "
                "to truncation with a marker: %s",
                exc,
            )
            return None


default_context_compressor = ContextCompressor()
