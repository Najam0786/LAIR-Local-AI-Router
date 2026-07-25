from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.models.ai_model import AIModel
from app.providers.completion_result import CompletionResult
from app.providers.stream_chunk import ProviderStreamChunk


class BaseProvider(ABC):
    """
    Abstract base class for all AI providers.

    Every provider must implement the same interface so that
    LAIR can interact with them without knowing provider-specific
    implementation details.
    """

    # True for a provider whose completions leave this machine (I-06,
    # RFC-0001). Local providers never override this -- it exists so
    # cloud-escalation logic can identify a cloud provider generically,
    # without hardcoding provider names.
    is_cloud: bool = False

    @abstractmethod
    async def list_models(self) -> list[AIModel]:
        """
        Return all AI models available from this provider.
        """
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Return True if the provider is healthy and reachable.
        """
        raise NotImplementedError

    @abstractmethod
    async def complete(
        self,
        model_id: str,
        messages: list[dict],
        max_tokens: int = 64,
        ttl_seconds: int | None = None,
    ) -> CompletionResult:
        """
        Run a single completion against a model and measure it.

        `ttl_seconds`, when given, is a hint for how long the provider
        should keep the model loaded after this request goes idle
        (LM Studio's `ttl` payload field, I-05) -- providers without an
        equivalent knob are free to ignore it.
        """
        raise NotImplementedError

    async def stream_complete(
        self,
        model_id: str,
        messages: list[dict],
        max_tokens: int = 64,
        ttl_seconds: int | None = None,
    ) -> AsyncIterator[ProviderStreamChunk]:
        """
        Stream a completion incrementally.

        Default fallback: run complete() once and yield its full text as
        a single chunk. Not abstract -- there is exactly one real
        streaming implementation (LMStudioProvider) today; overriding
        this is optional per provider.
        """
        result = await self.complete(model_id, messages, max_tokens, ttl_seconds)
        yield ProviderStreamChunk(
            delta=result.text,
            finish_reason=result.finish_reason,
            completion_tokens=result.completion_tokens,
            prompt_tokens=result.prompt_tokens,
        )
