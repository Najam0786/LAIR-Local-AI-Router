from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """
    Abstract base class for all AI providers.
    """

    @abstractmethod
    async def list_models(self) -> list[dict[str, Any]]:
        """
        Return all available models.
        """
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check whether the provider is reachable.
        """
        raise NotImplementedError