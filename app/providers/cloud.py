import time
from collections.abc import AsyncIterator

import httpx

from app.capabilities.capability import Capability, CapabilityType
from app.capabilities.profile import CapabilityProfile
from app.core.settings import settings
from app.models.ai_model import AIModel
from app.providers.base import BaseProvider
from app.providers.completion_result import CompletionResult
from app.providers.stream_chunk import ProviderStreamChunk


class OpenAICompatibleCloudProvider(BaseProvider):
    """
    A single configured OpenAI-compatible cloud endpoint (I-06,
    RFC-0001) -- real OpenAI, or any other OpenAI-compatible cloud API
    (DeepSeek, etc.) via `Settings.CLOUD_PROVIDER_BASE_URL`.

    Deliberately minimal compared to `LMStudioProvider`: no JIT-load
    management, no native-API metadata grounding, no `ttl`/speculative
    decoding -- none of those concepts apply to a cloud API. Inert
    (every method is a safe no-op or returns nothing) whenever no API
    key is configured, so constructing this unconditionally is safe.
    """

    name = "cloud"
    is_cloud = True

    def __init__(self):
        self.base_url = settings.CLOUD_PROVIDER_BASE_URL
        self.api_key = settings.CLOUD_PROVIDER_API_KEY
        self.model_id = settings.CLOUD_PROVIDER_MODEL_ID
        self.timeout = settings.REQUEST_TIMEOUT

    async def list_models(self) -> list[AIModel]:
        if not self.api_key or not self.model_id:
            return []

        return [
            AIModel(
                id=self.model_id,
                provider=self.name,
                loaded=True,
                profile=CapabilityProfile(
                    model_id=self.model_id,
                    provider=self.name,
                    capabilities=[
                        Capability(type=CapabilityType.TEXT_GENERATION),
                        Capability(type=CapabilityType.REASONING),
                        Capability(type=CapabilityType.CODING),
                    ],
                    supports_streaming=True,
                ),
            )
        ]

    async def health_check(self) -> bool:
        # A real health check would itself cost money against a paid
        # API -- "is this configured at all" is the cheap, honest
        # signal available without spending anything to find out.
        return bool(self.api_key)

    async def complete(
        self,
        model_id: str,
        messages: list[dict],
        max_tokens: int = 64,
        ttl_seconds: int | None = None,
    ) -> CompletionResult:
        payload = {
            "model": model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": False,
        }

        start = time.perf_counter()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()

            data = response.json()

        latency_seconds = time.perf_counter() - start

        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        completion_tokens = usage.get("completion_tokens")

        if completion_tokens is None:
            completion_tokens = len(text.split())

        return CompletionResult(
            text=text,
            completion_tokens=completion_tokens,
            latency_seconds=latency_seconds,
            prompt_tokens=usage.get("prompt_tokens"),
            finish_reason=data["choices"][0].get("finish_reason"),
        )

    async def stream_complete(
        self,
        model_id: str,
        messages: list[dict],
        max_tokens: int = 64,
        ttl_seconds: int | None = None,
    ) -> AsyncIterator[ProviderStreamChunk]:
        # Cloud escalation is non-streaming only for this pass (RFC-0001
        # scopes it that way, mirroring I-07/I-09's same simplification)
        # -- falls back to BaseProvider's single-chunk default.
        async for chunk in super().stream_complete(
            model_id, messages, max_tokens, ttl_seconds
        ):
            yield chunk


default_cloud_provider = OpenAICompatibleCloudProvider()
