import time
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.execution.conversation import Conversation
from app.execution.execution_outcome import ExecutionOutcome
from app.execution.runtime import execute, stream_execute
from app.models.task import Task
from app.registry.provider_registry import provider_registry
from app.routing.decision import DecisionRecord
from app.routing.decision_repository import default_decision_repository
from app.routing.routing_engine import routing_engine
from app.routing.selector import NoCandidateModelsError
from app.schemas.chat import (
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChunkDelta,
    ChatCompletionMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    OpenAIModelInfo,
    OpenAIModelListResponse,
    Usage,
)

router = APIRouter(tags=["OpenAI Compatibility"])


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
) -> ChatCompletionResponse | StreamingResponse:
    """
    OpenAI-compatible chat completion: routes the request to the best
    local model, executes it, and returns an OpenAI-shaped response.
    """

    models = await provider_registry.list_models()

    if not models:
        raise HTTPException(
            status_code=503,
            detail="No AI models are currently available.",
        )

    conversation = Conversation(messages=request.messages)
    task = Task(prompt=conversation.latest_user_message())

    try:
        plan = routing_engine.route(task=task, models=models)
    except NoCandidateModelsError:
        raise HTTPException(
            status_code=404,
            detail="No suitable model found for this request.",
        )

    if request.stream:
        return StreamingResponse(
            _stream_chat_completion(
                plan.decision, conversation, request.max_tokens
            ),
            media_type="text/event-stream",
        )

    result, outcome = await execute(
        plan.decision.selected_model,
        conversation.messages,
        request.max_tokens,
    )

    default_decision_repository.record(
        plan.decision.model_copy(update={"execution_outcome": outcome})
    )

    if not outcome.success:
        raise HTTPException(status_code=502, detail=outcome.error)

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        model=plan.decision.selected_model.id,
        choices=[
            ChatCompletionChoice(
                message=ChatCompletionMessage(content=result.text),
                finish_reason=outcome.finish_reason or "stop",
            )
        ],
        usage=Usage(
            prompt_tokens=outcome.prompt_tokens or 0,
            completion_tokens=outcome.completion_tokens or 0,
            total_tokens=(outcome.prompt_tokens or 0) + (outcome.completion_tokens or 0),
        ),
    )


async def _stream_chat_completion(
    decision: DecisionRecord,
    conversation: Conversation,
    max_tokens: int,
) -> AsyncIterator[str]:
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"
    model_id = decision.selected_model.id

    def sse(chunk: ChatCompletionChunk) -> str:
        return f"data: {chunk.model_dump_json()}\n\n"

    yield sse(
        ChatCompletionChunk(
            id=completion_id,
            model=model_id,
            choices=[
                ChatCompletionChunkChoice(
                    delta=ChatCompletionChunkDelta(role="assistant", content="")
                )
            ],
        )
    )

    full_text = ""
    finish_reason = "stop"
    completion_tokens: int | None = None
    prompt_tokens: int | None = None
    error: str | None = None
    start = time.perf_counter()

    async for event in stream_execute(
        decision.selected_model, conversation.messages, max_tokens
    ):
        if event.error is not None:
            error = event.error
            yield sse(
                ChatCompletionChunk(
                    id=completion_id,
                    model=model_id,
                    choices=[
                        ChatCompletionChunkChoice(
                            delta=ChatCompletionChunkDelta(
                                content=f"\n\n[LAIR error: {error}]"
                            )
                        )
                    ],
                )
            )
            break

        if event.delta:
            full_text += event.delta
            yield sse(
                ChatCompletionChunk(
                    id=completion_id,
                    model=model_id,
                    choices=[
                        ChatCompletionChunkChoice(
                            delta=ChatCompletionChunkDelta(content=event.delta)
                        )
                    ],
                )
            )

        if event.finish_reason:
            finish_reason = event.finish_reason
        if event.completion_tokens is not None:
            completion_tokens = event.completion_tokens
        if event.prompt_tokens is not None:
            prompt_tokens = event.prompt_tokens

    if completion_tokens is None and error is None:
        completion_tokens = len(full_text.split())

    outcome = ExecutionOutcome(
        success=error is None,
        latency_ms=(time.perf_counter() - start) * 1000,
        completion_tokens=completion_tokens,
        prompt_tokens=prompt_tokens,
        finish_reason=finish_reason if error is None else None,
        error=error,
    )

    default_decision_repository.record(
        decision.model_copy(update={"execution_outcome": outcome})
    )

    yield sse(
        ChatCompletionChunk(
            id=completion_id,
            model=model_id,
            choices=[
                ChatCompletionChunkChoice(
                    delta=ChatCompletionChunkDelta(), finish_reason="stop"
                )
            ],
        )
    )
    yield "data: [DONE]\n\n"


@router.get("/v1/models", response_model=OpenAIModelListResponse)
async def list_openai_models() -> OpenAIModelListResponse:
    """
    OpenAI-compatible model listing, for client discovery/autocomplete.
    """

    models = await provider_registry.list_models()

    return OpenAIModelListResponse(
        data=[
            OpenAIModelInfo(id=model.id, owned_by=model.provider)
            for model in models
        ]
    )
