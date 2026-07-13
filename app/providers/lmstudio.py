import httpx

from app.capabilities.resolver import resolver
from app.core.settings import settings
from app.models.ai_model import AIModel
from app.providers.base import BaseProvider


class LMStudioProvider(BaseProvider):
    """
    Provider for LM Studio's OpenAI-compatible API.
    """

    name = "lmstudio"

    def __init__(self):
        self.base_url = settings.LM_STUDIO_URL
        self.timeout = settings.REQUEST_TIMEOUT

    async def list_models(self) -> list[AIModel]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/models")
            response.raise_for_status()

            data = response.json()

        models: list[AIModel] = []

        for model in data.get("data", []):
            models.append(
                AIModel(
                    id=model["id"],
                    provider=self.name,
                    loaded=True,
                    profile=resolver.resolve(
                        model_id=model["id"],
                        provider=self.name,
                    ),
                )
            )

        return models

    async def health_check(self) -> bool:
        try:
            await self.list_models()
            return True
        except Exception:
            return False


lmstudio = LMStudioProvider()