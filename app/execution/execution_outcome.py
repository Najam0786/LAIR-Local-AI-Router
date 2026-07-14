from pydantic import BaseModel


class ExecutionOutcome(BaseModel):
    """
    Result of actually invoking a provider for a routed decision.

    Deliberately omits model/provider -- both already live on
    DecisionRecord.selected_model, and duplicating them here risks
    the two drifting out of sync.
    """

    success: bool

    latency_ms: float | None = None

    completion_tokens: int | None = None

    prompt_tokens: int | None = None

    finish_reason: str | None = None

    error: str | None = None
