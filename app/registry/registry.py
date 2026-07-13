from app.providers.lmstudio import lmstudio
from app.schemas.model import ModelInfo


class ModelRegistry:
    """
    Registry of available AI models.
    """

    async def list_models(self) -> list[ModelInfo]:
        models = await lmstudio.list_models()

        return [
            ModelInfo(
                id=model["id"],
                provider="lmstudio",
                loaded=True,
            )
            for model in models
        ]


registry = ModelRegistry()