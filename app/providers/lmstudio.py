import asyncio
import json
import logging
import subprocess
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
        self._recovery_lock = asyncio.Lock()

    async def list_models(self) -> list[AIModel]:
        try:
            return await self._list_models_native()
        except Exception as exc:
            if settings.ENABLE_LM_STUDIO_AUTOSTART:
                async with self._recovery_lock:
                    await self._ensure_server_started_if_down()
                try:
                    return await self._list_models_native()
                except Exception:
                    pass

            # Graceful degradation (ADR-0011): an older LM Studio version
            # or a different OpenAI-compatible server won't expose the
            # native API. Fall back to the minimal endpoint rather than
            # failing to list any models at all.
            logger.warning(
                "Native LM Studio API unavailable, falling back to "
                "/v1/models with no metadata: %s",
                exc,
            )
            try:
                return await self._list_models_fallback()
            except Exception:
                # LM Studio is unreachable via either API -- report no
                # models rather than letting the request 500.
                return []

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

    async def _probe_loaded_model_ids(self) -> set[str] | None:
        """
        Returns the set of currently-loaded model ids, or None if the
        native LM Studio API isn't reachable right now (server down, or
        an older/non-LM-Studio OpenAI-compatible backend). Bounded by a
        short timeout, independent of the full completion timeout, so a
        cold/unreachable server never stalls a request behind it.
        """
        try:
            async with httpx.AsyncClient(
                timeout=settings.LMS_PROBE_TIMEOUT_SECONDS
            ) as client:
                response = await client.get(f"{self._host_root}/api/v0/models")
                response.raise_for_status()

                data = response.json()
        except Exception:
            return None

        return {
            entry["id"]
            for entry in data.get("data", [])
            if entry.get("state") == "loaded"
        }

    async def _run_lms(self, *args: str) -> bool:
        """
        Runs the LM Studio CLI (`lms`) headlessly, off the event loop
        thread via subprocess.run rather than asyncio.create_subprocess_exec:
        uvicorn's --reload worker runs under WindowsSelectorEventLoop,
        which has no subprocess transport at all (bare NotImplementedError
        from base_events._make_subprocess_transport) -- subprocess.run
        doesn't depend on loop subprocess support, so it works regardless
        of which event loop policy is active. Never raises: a missing
        binary, timeout, or non-zero exit is logged and treated as
        remediation having failed, so the caller falls through to
        whatever the original request would have done anyway.
        """
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                [settings.LMS_CLI_PATH, *args],
                capture_output=True,
                timeout=settings.LMS_RECOVERY_TIMEOUT_SECONDS,
            )
        except Exception as exc:
            logger.warning("Failed to run 'lms %s': %r", " ".join(args), exc)
            return False

        if result.returncode != 0:
            logger.warning(
                "'lms %s' exited with code %s: %s",
                " ".join(args),
                result.returncode,
                result.stderr.decode(errors="replace").strip(),
            )
            return False

        return True

    async def _ensure_server_started_if_down(self) -> None:
        if await self._probe_loaded_model_ids() is None:
            await self._run_lms("server", "start")

    async def _ensure_ready(self, model_id: str) -> None:
        """
        Auto-management preflight (ADR pending): make sure LM Studio's
        server is running and the target model is loaded before a
        request depends on it, rather than reacting to a mid-request
        connection failure. Models can auto-unload on their own TTL, so
        this always re-checks -- only the remediation subprocess calls
        are conditional on something actually being wrong.
        """
        if not settings.ENABLE_LM_STUDIO_AUTOSTART:
            return

        async with self._recovery_lock:
            await self._ensure_server_started_if_down()
            loaded_ids = await self._probe_loaded_model_ids()

            if loaded_ids is not None and model_id not in loaded_ids:
                await self._run_lms("load", model_id, "-y")

    async def complete(
        self,
        model_id: str,
        messages: list[dict],
        max_tokens: int = 64,
    ) -> CompletionResult:
        await self._ensure_ready(model_id)

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
        await self._ensure_ready(model_id)

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
