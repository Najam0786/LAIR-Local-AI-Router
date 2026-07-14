from app.benchmarking.benchmark_result import BenchmarkResult
from app.knowledge.knowledge_base import KnowledgeBase


def _result(model_id: str, tokens_per_second_inputs: tuple[float, int]) -> BenchmarkResult:
    latency_seconds, completion_tokens = tokens_per_second_inputs
    return BenchmarkResult(
        run_id="test-run",
        model_id=model_id,
        provider="fake",
        prompt="hello",
        latency_seconds=latency_seconds,
        completion_tokens=completion_tokens,
    )


def test_record_and_latest(tmp_path):
    kb = KnowledgeBase(path=tmp_path / "kb.json")
    result = _result("a", (2.0, 20))

    kb.record(result)

    latest = kb.latest("a")

    assert latest is not None
    assert latest.model_id == "a"
    assert latest.tokens_per_second == 10.0


def test_latest_returns_none_for_unknown_model(tmp_path):
    kb = KnowledgeBase(path=tmp_path / "kb.json")

    assert kb.latest("does-not-exist") is None


def test_latest_returns_none_when_file_does_not_exist(tmp_path):
    kb = KnowledgeBase(path=tmp_path / "missing" / "kb.json")

    assert kb.latest("a") is None


def test_all_latest_picks_most_recent_per_model(tmp_path):
    kb = KnowledgeBase(path=tmp_path / "kb.json")

    kb.record(_result("a", (2.0, 10)))
    kb.record(_result("a", (2.0, 40)))
    kb.record(_result("b", (1.0, 5)))

    latest = kb.all_latest()

    assert set(latest.keys()) == {"a", "b"}
    assert latest["a"].tokens_per_second == 20.0
