from app.execution.conversation import ChatMessage
from app.execution.execution_outcome import ExecutionOutcome
from app.models.ai_model import AIModel
from app.providers.completion_result import CompletionResult
from app.registry.provider_registry import provider_registry


async def execute(
    model: AIModel,
    messages: list[ChatMessage],
    max_tokens: int,
) -> tuple[CompletionResult | None, ExecutionOutcome]:
    """
    Invoke the provider for a routed model and translate the result.

    Never raises and never touches HTTP or persistence -- a failed
    call becomes a failed ExecutionOutcome, not an exception. Turning
    that into an HTTP response is the API handler's job, the same way
    NoCandidateModelsError is caught at the API layer rather than here.
    """

    provider = provider_registry.get(model.provider)

    try:
        result = await provider.complete(
            model.id,
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
