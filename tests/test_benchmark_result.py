from app.benchmarking.benchmark_result import BenchmarkResult


def test_tokens_per_second_normal_case():
    result = BenchmarkResult(
        run_id="test-run",
        model_id="a",
        provider="fake",
        prompt="hello",
        latency_seconds=2.0,
        completion_tokens=20,
    )

    assert result.tokens_per_second == 10.0


def test_tokens_per_second_zero_latency_does_not_raise():
    result = BenchmarkResult(
        run_id="test-run",
        model_id="a",
        provider="fake",
        prompt="hello",
        latency_seconds=0.0,
        completion_tokens=20,
    )

    assert result.tokens_per_second == 0.0
