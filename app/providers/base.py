from abc import ABC, abstractmethod

from app.models.ai_model import AIModel


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