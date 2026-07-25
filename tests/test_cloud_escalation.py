import asyncio

from app.core.settings import settings
from app.costs.budget import CloudBudgetLedger
from app.execution.conversation import ChatMessage
from app.providers.base import BaseProvider
from app.providers.completion_result import CompletionResult
from app.routing.cloud_escalation import (
    CloudEscalator,
    estimate_cloud_cost,
    evaluate_escalation,
)
from app.routing.complexity import ComplexityAssessment


class _FakeCloudProvider(BaseProvider):
    is_cloud = True

    def __init__(self, result: CompletionResult | None = None, error: bool = False):
        self._result = result or CompletionResult(
            text="cloud answer", completion_tokens=5, latency_seconds=0.2
        )
        self._error = error

    async def list_models(self):
        return []

    async def health_check(self):
        return True

    async def complete(self, model_id, messages, max_tokens=64, ttl_seconds=None):
        if self._error:
            raise RuntimeError("simulated cloud failure")
        return self._result


def _enable_escalation(monkeypatch, budget=10.0, confidence_threshold=0.3):
    monkeypatch.setattr(settings, "ENABLE_CLOUD_ESCALATION", True)
    monkeypatch.setattr(settings, "CLOUD_PROVIDER_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "CLOUD_MONTHLY_BUDGET_USD", budget)
    monkeypatch.setattr(settings, "CLOUD_ESCALATION_COMPLEXITY_THRESHOLD", 5)
    monkeypatch.setattr(
        settings, "CLOUD_ESCALATION_LOCAL_CONFIDENCE_THRESHOLD", confidence_threshold
    )


def test_disabled_by_default_never_escalates(tmp_path):
    ledger = CloudBudgetLedger(monthly_budget_usd=10.0, path=tmp_path / "b.json")

    decision = evaluate_escalation(
        "hi", ComplexityAssessment(level=5, reasons=["x"]), 0.0, ledger
    )

    assert decision.should_escalate is False
    assert decision.reason == "disabled"


def test_enabled_but_no_api_key_never_escalates(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "ENABLE_CLOUD_ESCALATION", True)
    monkeypatch.setattr(settings, "CLOUD_PROVIDER_API_KEY", "")
    ledger = CloudBudgetLedger(monthly_budget_usd=10.0, path=tmp_path / "b.json")

    decision = evaluate_escalation(
        "hi", ComplexityAssessment(level=5, reasons=["x"]), 0.0, ledger
    )

    assert decision.should_escalate is False


def test_enabled_but_no_budget_never_escalates(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "ENABLE_CLOUD_ESCALATION", True)
    monkeypatch.setattr(settings, "CLOUD_PROVIDER_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "CLOUD_MONTHLY_BUDGET_USD", 0.0)
    ledger = CloudBudgetLedger(monthly_budget_usd=0.0, path=tmp_path / "b.json")

    decision = evaluate_escalation(
        "hi", ComplexityAssessment(level=5, reasons=["x"]), 0.0, ledger
    )

    assert decision.should_escalate is False


def test_low_complexity_never_escalates(monkeypatch, tmp_path):
    _enable_escalation(monkeypatch)
    ledger = CloudBudgetLedger(monthly_budget_usd=10.0, path=tmp_path / "b.json")

    decision = evaluate_escalation(
        "hi", ComplexityAssessment(level=2, reasons=["x"]), 0.0, ledger
    )

    assert decision.should_escalate is False
    assert "complexity" in decision.reason


def test_no_complexity_assessment_never_escalates(monkeypatch, tmp_path):
    _enable_escalation(monkeypatch)
    ledger = CloudBudgetLedger(monthly_budget_usd=10.0, path=tmp_path / "b.json")

    decision = evaluate_escalation("hi", None, 0.0, ledger)

    assert decision.should_escalate is False


def test_confident_local_candidate_never_escalates(monkeypatch, tmp_path):
    _enable_escalation(monkeypatch)
    ledger = CloudBudgetLedger(monthly_budget_usd=10.0, path=tmp_path / "b.json")

    decision = evaluate_escalation(
        "hi", ComplexityAssessment(level=5, reasons=["x"]), 0.9, ledger
    )

    assert decision.should_escalate is False
    assert "confident" in decision.reason


def test_all_conditions_met_escalates(monkeypatch, tmp_path):
    _enable_escalation(monkeypatch)
    ledger = CloudBudgetLedger(monthly_budget_usd=10.0, path=tmp_path / "b.json")

    decision = evaluate_escalation(
        "hi", ComplexityAssessment(level=5, reasons=["x"]), 0.1, ledger
    )

    assert decision.should_escalate is True
    assert decision.estimated_cost_usd is not None


def test_exhausted_budget_blocks_escalation_mid_month(monkeypatch, tmp_path):
    _enable_escalation(monkeypatch, budget=0.01)
    ledger = CloudBudgetLedger(monthly_budget_usd=0.01, path=tmp_path / "b.json")
    ledger.record(0.01)  # budget exhausted mid-month

    decision = evaluate_escalation(
        "hi", ComplexityAssessment(level=5, reasons=["x"]), 0.1, ledger
    )

    assert decision.should_escalate is False
    assert "budget" in decision.reason


def test_estimate_cloud_cost_scales_with_prompt_length():
    short = estimate_cloud_cost("hi")
    long = estimate_cloud_cost(" ".join(["word"] * 5000))

    assert long > short


def test_escalator_execute_returns_success_outcome():
    provider = _FakeCloudProvider()
    escalator = CloudEscalator(provider=provider)

    result, outcome = asyncio.run(
        escalator.execute([ChatMessage(role="user", content="hi")], max_tokens=64)
    )

    assert result is not None
    assert result.text == "cloud answer"
    assert outcome.success is True


def test_escalator_execute_never_raises_on_provider_failure():
    provider = _FakeCloudProvider(error=True)
    escalator = CloudEscalator(provider=provider)

    result, outcome = asyncio.run(
        escalator.execute([ChatMessage(role="user", content="hi")], max_tokens=64)
    )

    assert result is None
    assert outcome.success is False
    assert "simulated cloud failure" in outcome.error


def test_actual_cost_usd_uses_real_token_counts(monkeypatch):
    monkeypatch.setattr(settings, "CLOUD_PROVIDER_INPUT_PRICE_PER_1M_USD", 5.0)
    monkeypatch.setattr(settings, "CLOUD_PROVIDER_OUTPUT_PRICE_PER_1M_USD", 15.0)

    from app.execution.execution_outcome import ExecutionOutcome

    escalator = CloudEscalator(provider=_FakeCloudProvider())
    outcome = ExecutionOutcome(
        success=True, prompt_tokens=1_000_000, completion_tokens=1_000_000
    )

    assert escalator.actual_cost_usd(outcome) == 20.0
