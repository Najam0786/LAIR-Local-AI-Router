import logging
import uuid

from app.benchmarking.benchmark_result import BenchmarkResult
from app.knowledge.knowledge_base import KnowledgeBase, default_knowledge_base
from app.models.ai_model import AIModel
from app.registry.provider_registry import ProviderRegistry
from app.registry.provider_registry import provider_registry as _default_registry

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """
    Measures real latency/throughput for a set of models.
    """

    def __init__(
        self,
        provider_registry: ProviderRegistry = _default_registry,
        knowledge_base: KnowledgeBase = default_knowledge_base,
    ):
        self._provider_registry = provider_registry
        self._knowledge_base = knowledge_base

    async def run(
        self,
        models: list[AIModel],
        prompt: str,
        max_tokens: int = 64,
    ) -> list[BenchmarkResult]:
        run_id = uuid.uuid4().hex
        results: list[BenchmarkResult] = []

        # Sequential, not concurrent -- calling models in parallel against
        # one local inference server would make each model's measured
        # latency include queueing/contention from the others.
        for model in models:
            try:
                provider = self._provider_registry.get(model.provider)
                completion = await provider.complete(
                    model.id,
                    [{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                )
            except Exception as exc:
                logger.warning(
                    "Skipping benchmark for %s (%s): %s",
                    model.id,
                    model.provider,
                    exc,
                )
                continue

            result = BenchmarkResult(
                run_id=run_id,
                model_id=model.id,
                provider=model.provider,
                prompt=prompt,
                latency_seconds=completion.latency_seconds,
                completion_tokens=completion.completion_tokens,
            )

            self._knowledge_base.record(result)
            results.append(result)

        return results
