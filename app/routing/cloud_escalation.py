from pydantic import BaseModel

from app.core.settings import settings
from app.costs.budget import CloudBudgetLedger, default_cloud_budget_ledger
from app.execution.context_compression import estimate_tokens
from app.execution.conversation import ChatMessage
from app.execution.execution_outcome import ExecutionOutcome
from app.providers.base import BaseProvider
from app.providers.cloud import default_cloud_provider
from app.providers.completion_result import CompletionResult
from app.routing.complexity import ComplexityAssessment


class CloudEscalationDecision(BaseModel):
    """
    Whether a request should escalate to the cloud (I-06, RFC-0001),
    and why -- always populated, even when `should_escalate` is False,
    so the caller (and, on the response, the user) can see the reason.
    """

    should_escalate: bool
    reason: str
    estimated_cost_usd: float | None = None


def estimate_cloud_cost(prompt: str, expected_completion_tokens: int = 500) -> float:
    """
    Conservative (upper-bound) cost estimate for a single escalation,
    using the configured cloud model's real published per-token price
    -- checked against the budget *before* the call goes out, per
    RFC-0001's stated risk mitigation.
    """

    prompt_tokens = estimate_tokens(prompt)

    return (
        prompt_tokens / 1_000_000 * settings.CLOUD_PROVIDER_INPUT_PRICE_PER_1M_USD
        + expected_completion_tokens
        / 1_000_000
        * settings.CLOUD_PROVIDER_OUTPUT_PRICE_PER_1M_USD
    )


def evaluate_escalation(
    prompt: str,
    complexity: ComplexityAssessment | None,
    local_confidence: float,
    budget_ledger: CloudBudgetLedger | None = None,
) -> CloudEscalationDecision:
    """
    Decides whether this request should escalate to the cloud.

    A gate, not a scored preference (RFC-0001): every condition below
    must hold, or the request stays local. Two independent signals --
    high complexity *and* low local confidence -- are both required,
    not complexity alone, so a single triage false positive can't
    trigger a real-money escalation by itself.
    """

    if not settings.ENABLE_CLOUD_ESCALATION:
        return CloudEscalationDecision(should_escalate=False, reason="disabled")

    if not settings.CLOUD_PROVIDER_API_KEY:
        return CloudEscalationDecision(
            should_escalate=False, reason="no cloud API key configured"
        )

    if settings.CLOUD_MONTHLY_BUDGET_USD <= 0:
        return CloudEscalationDecision(
            should_escalate=False, reason="no cloud budget configured"
        )

    if complexity is None or complexity.level < settings.CLOUD_ESCALATION_COMPLEXITY_THRESHOLD:
        return CloudEscalationDecision(
            should_escalate=False, reason="complexity below escalation threshold"
        )

    if local_confidence >= settings.CLOUD_ESCALATION_LOCAL_CONFIDENCE_THRESHOLD:
        return CloudEscalationDecision(
            should_escalate=False,
            reason="local candidate confident enough",
        )

    budget_ledger = budget_ledger or default_cloud_budget_ledger
    estimated_cost = estimate_cloud_cost(prompt)
    remaining = budget_ledger.remaining_this_month()

    if estimated_cost > remaining:
        return CloudEscalationDecision(
            should_escalate=False,
            reason=(
                f"estimated cost ${estimated_cost:.4f} would exceed "
                f"remaining budget ${remaining:.4f}"
            ),
            estimated_cost_usd=estimated_cost,
        )

    return CloudEscalationDecision(
        should_escalate=True,
        reason=(
            f"complexity {complexity.level}/5 with local confidence "
            f"{local_confidence:.2f} below threshold; escalating to "
            f"{settings.CLOUD_PROVIDER_MODEL_ID}"
        ),
        estimated_cost_usd=estimated_cost,
    )


class CloudEscalator:
    """
    Executes an escalated request against the configured cloud
    provider, mirroring `app.execution.runtime.execute()`'s
    never-raises contract exactly -- a failed cloud call becomes a
    failed ExecutionOutcome, never an exception, so the caller can fall
    back to the local decision cleanly.
    """

    def __init__(self, provider: BaseProvider | None = None):
        self._provider = provider or default_cloud_provider

    async def execute(
        self,
        messages: list[ChatMessage],
        max_tokens: int,
    ) -> tuple[CompletionResult | None, ExecutionOutcome]:
        try:
            result = await self._provider.complete(
                settings.CLOUD_PROVIDER_MODEL_ID,
                [message.model_dump() for message in messages],
                max_tokens,
            )
        except Exception as exc:
            return None, ExecutionOutcome(success=False, error=str(exc))

        outcome = ExecutionOutcome(
            success=True,
            latency_ms=result.latency_seconds * 1000,
            completion_tokens=result.completion_tokens,
            prompt_tokens=result.prompt_tokens,
            finish_reason=result.finish_reason,
        )

        return result, outcome

    def actual_cost_usd(self, outcome: ExecutionOutcome) -> float:
        return (
            (outcome.prompt_tokens or 0)
            / 1_000_000
            * settings.CLOUD_PROVIDER_INPUT_PRICE_PER_1M_USD
            + (outcome.completion_tokens or 0)
            / 1_000_000
            * settings.CLOUD_PROVIDER_OUTPUT_PRICE_PER_1M_USD
        )


default_cloud_escalator = CloudEscalator()
