import asyncio

from app.benchmarking.runner import BenchmarkRunner
from app.registry.provider_registry import provider_registry

PROMPT = "Explain what a neural network is in two sentences."
MAX_TOKENS = 64


async def main() -> None:
    models = await provider_registry.list_models()

    print("=" * 60)
    print("LAIR Benchmark Run")
    print("=" * 60)
    print(f"Models discovered: {len(models)}\n")

    results = await BenchmarkRunner().run(models, PROMPT, max_tokens=MAX_TOKENS)

    for result in results:
        print(
            f"  {result.model_id:40s} "
            f"{result.latency_seconds:6.2f}s  "
            f"{result.completion_tokens:4d} tok  "
            f"{result.tokens_per_second:6.2f} tok/s"
        )

    skipped = {model.id for model in models} - {r.model_id for r in results}

    if skipped:
        print(f"\nSkipped ({len(skipped)}): {', '.join(sorted(skipped))}")

    print(f"\nRecorded {len(results)} result(s) to benchmarks/knowledge_base.json")


asyncio.run(main())
