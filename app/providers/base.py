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
    ) -> CompletionResult:
        """
        Run a single completion against a model and measure it.
        """
        raise NotImplementedError

    async def stream_complete(
        self,
        model_id: str,
        messages: list[dict],
        max_tokens: int = 64,
    ) -> AsyncIterator[ProviderStreamChunk]:
        """
        Stream a completion incrementally.

        Default fallback: run complete() once and yield its full text as
        a single chunk. Not abstract -- there is exactly one real
        streaming implementation (LMStudioProvider) today; overriding
        this is optional per provider.
        """
        result = await self.complete(model_id, messages, max_tokens)
        yield ProviderStreamChunk(
            delta=result.text,
            finish_reason=result.finish_reason,
            completion_tokens=result.completion_tokens,
            prompt_tokens=result.prompt_tokens,
        )
