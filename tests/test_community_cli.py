import json

import app.registry.community_scores as community_scores_module
from app.benchmarking.benchmark_result import BenchmarkResult
from app.hardware.tier import HardwareTier
from app.knowledge.knowledge_base import KnowledgeBase
from lair.commands import community as community_command


def test_export_produces_anonymized_json(monkeypatch, tmp_path):
    kb = KnowledgeBase(path=tmp_path / "kb.json")
    kb.record(
        BenchmarkResult(
            run_id="run-1",
            model_id="qwen3-8b",
            provider="fake",
            prompt="hello",
            latency_seconds=1.0,
            completion_tokens=15,
        )
    )
    monkeypatch.setattr(community_scores_module, "default_knowledge_base", kb)

    output = community_command.export(HardwareTier.STANDARD)
    parsed = json.loads(output)

    assert parsed == [
        {
            "model_id": "qwen3-8b",
            "hardware_tier": "standard",
            "tokens_per_second": 15.0,
            "sample_count": 1,
        }
    ]
