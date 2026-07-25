from app.registry.provider_registry import provider_registry
from app.schemas.model import ModelInfo


class ModelRegistry:
    """
    Registry of available AI models.
    """

    async def list_models(self) -> list[ModelInfo]:
        """
        Return all models from all registered providers.
        """

        models = await provider_registry.list_models()

        return [
            ModelInfo(
                id=model.id,
                provider=model.provider,
                loaded=model.loaded,
            )
            for model in models
        ]


registry = ModelRegistry()