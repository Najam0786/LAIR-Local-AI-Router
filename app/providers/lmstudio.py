import json
import logging
import time
from collections.abc import AsyncIterator

import httpx

from app.capabilities.resolver import resolver
from app.core.settings import settings
from app.models.ai_model import AIModel
from app.providers.base import BaseProvider
from app.providers.completion_result import CompletionResult
from app.providers.model_metadata import ModelMetadata
from app.providers.stream_chunk import ProviderStreamChunk

logger = logging.getLogger(__name__)


class LMStudioProvider(BaseProvider):
    """
    Provider for LM Studio's OpenAI-compatible and native APIs.
    """

    name = "lmstudio"

    def __init__(self):
        self.base_url = settings.LM_STUDIO_URL
        self.timeout = settings.REQUEST_TIMEOUT
        self._host_root = self.base_url.removesuffix("/v1")

    async def list_models(self) -> list[AIModel]:
        try:
            return await self._list_models_native()
        except Exception as exc:
            # Graceful degradation (ADR-0011): an older LM Studio version
            # or a different OpenAI-compatible server won't expose the
            # native API. Fall back to the minimal endpoint rather than
            # failing to list any models at all.
            logger.warning(
                "Native LM Studio API unavailable, falling back to "
                "/v1/models with no metadata: %s",
                exc,
            )
            return await self._list_models_fallback()

    async def _list_models_native(self) -> list[AIModel]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self._host_root}/api/v0/models")
            response.raise_for_status()

            data = response.json()

        models: list[AIModel] = []

        for entry in data.get("data", []):
            metadata = ModelMetadata(
                is_vision=entry.get("type") == "vlm",
                is_embedding=entry.get("type") == "embeddings",
                supports_tool_use="tool_use" in entry.get("capabilities", []),
                context_window=entry.get("max_context_length"),
                quantization=entry.get("quantization"),
                loaded=entry.get("state") == "loaded",
            )

            models.append(
                AIModel(
                    id=entry["id"],
                    provider=self.name,
                    loaded=metadata.loaded,
                    profile=resolver.resolve(
                        model_id=entry["id"],
                        provider=self.name,
                        metadata=metadata,
                    ),
                    metadata=metadata,
                )
            )

        return models

    async def _list_models_fallback(self) -> list[AIModel]:
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

    async def complete(
        self,
        model_id: str,
        messages: list[dict],
        max_tokens: int = 64,
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
            )
            response.raise_for_status()

            data = response.json()

        latency_seconds = time.perf_counter() - start

        text = data["choices"][0]["message"]["content"]

        completion_tokens = data.get("usage", {}).get("completion_tokens")

        if completion_tokens is None:
            completion_tokens = len(text.split())

        return CompletionResult(
            text=text,
            completion_tokens=completion_tokens,
            latency_seconds=latency_seconds,
            prompt_tokens=data.get("usage", {}).get("prompt_tokens"),
            finish_reason=data["choices"][0].get("finish_reason"),
        )

    async def stream_complete(
        self,
        model_id: str,
        messages: list[dict],
        max_tokens: int = 64,
    ) -> AsyncIterator[ProviderStreamChunk]:
        payload = {
            "model": model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    data_str = line[len("data: ") :]

                    if data_str == "[DONE]":
                        break

                    event = json.loads(data_str)
                    usage = event.get("usage")
                    choices = event.get("choices") or []
                    choice = choices[0] if choices else {}

                    yield ProviderStreamChunk(
                        delta=choice.get("delta", {}).get("content", ""),
                        finish_reason=choice.get("finish_reason"),
                        completion_tokens=(
                            usage.get("completion_tokens") if usage else None
                        ),
                        prompt_tokens=usage.get("prompt_tokens") if usage else None,
                    )


lmstudio = LMStudioProvider()
