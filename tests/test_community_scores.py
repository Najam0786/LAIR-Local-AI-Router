import json

from app.hardware.tier import HardwareTier
from app.knowledge.knowledge_base import KnowledgeBase
from app.benchmarking.benchmark_result import BenchmarkResult
from app.registry.community_scores import (
    CommunityScoreEntry,
    CommunityScoreLoader,
    CommunityScoreTable,
    export_contribution,
)


def test_loader_returns_empty_table_when_snapshot_missing(tmp_path):
    loader = CommunityScoreLoader(path=tmp_path / "no-such-snapshot.json")

    table = loader.load()

    assert table.for_model_and_tier("any-model", HardwareTier.STANDARD) is None


def test_loader_parses_a_real_snapshot_file(tmp_path):
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            [
                {
                    "model_id": "qwen3-8b",
                    "hardware_tier": "standard",
                    "tokens_per_second": 42.5,
                    "sample_count": 3,
                }
            ]
        ),
        encoding="utf-8",
    )
    loader = CommunityScoreLoader(path=snapshot_path)

    table = loader.load()
    entry = table.for_model_and_tier("qwen3-8b", HardwareTier.STANDARD)

    assert entry is not None
    assert entry.tokens_per_second == 42.5
    assert entry.sample_count == 3


def test_table_never_matches_a_different_tier():
    table = CommunityScoreTable(
        [
            CommunityScoreEntry(
                model_id="qwen3-8b",
                hardware_tier=HardwareTier.ENTHUSIAST,
                tokens_per_second=90.0,
            )
        ]
    )

    assert table.for_model_and_tier("qwen3-8b", HardwareTier.ENTRY) is None


def test_export_contribution_includes_only_model_tier_and_score(tmp_path):
    kb = KnowledgeBase(path=tmp_path / "kb.json")
    kb.record(
        BenchmarkResult(
            run_id="run-1",
            model_id="qwen3-8b",
            provider="fake",
            prompt="a secret prompt that should never be exported",
            latency_seconds=2.0,
            completion_tokens=20,
        )
    )

    exported = json.loads(export_contribution(HardwareTier.STANDARD, knowledge_base=kb))

    assert len(exported) == 1
    entry = exported[0]
    assert entry["model_id"] == "qwen3-8b"
    assert entry["hardware_tier"] == "standard"
    assert entry["tokens_per_second"] == 10.0
    assert "prompt" not in entry
    assert "secret" not in json.dumps(entry)
