from typing import Any

import httpx

from app.core.settings import settings
from app.providers.base import BaseProvider


class LMStudioProvider(BaseProvider):
    """
    Provider for LM Studio's OpenAI-compatible API.
    """

    def __init__(self):
        self.base_url = settings.LM_STUDIO_URL
        self.timeout = settings.REQUEST_TIMEOUT

    async def list_models(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/models")
            response.raise_for_status()

            data = response.json()

            return data.get("data", [])

    async def health_check(self) -> bool:
        try:
            await self.list_models()
            return True
        except Exception:
            return False


lmstudio = LMStudioProvider()