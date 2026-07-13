from app.models.ai_model import AIModel
from app.providers.base import BaseProvider
from app.providers.lmstudio import lmstudio


class ProviderRegistry:
    """
    Registry of AI providers available to LAIR.
    """

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider) -> None:
        """
        Register a provider.
        """
        self._providers[provider.name] = provider

    def list_providers(self) -> list[BaseProvider]:
        """
        Return all registered providers.
        """
        return list(self._providers.values())

    async def list_models(self) -> list[AIModel]:
        """
        Collect models from every registered provider.
        """
        models: list[AIModel] = []

        for provider in self._providers.values():
            models.extend(await provider.list_models())

        return models


provider_registry = ProviderRegistry()
provider_registry.register(lmstudio)