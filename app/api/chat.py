import uuid

from fastapi import APIRouter, HTTPException

from app.execution.conversation import Conversation
from app.execution.runtime import execute
from app.models.task import Task
from app.registry.provider_registry import provider_registry
from app.routing.decision_repository import default_decision_repository
from app.routing.routing_engine import routing_engine
from app.routing.selector import NoCandidateModelsError
from app.schemas.chat import (
    ChatCompletionChoice,
    ChatCompletionMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    OpenAIModelInfo,
    OpenAIModelListResponse,
    Usage,
)

router = APIRouter(tags=["OpenAI Compatibility"])


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest) -> ChatCompletionResponse:
    """
    OpenAI-compatible chat completion: routes the request to the best
    local model, executes it, and returns an OpenAI-shaped response.
    """

    if request.stream:
        raise HTTPException(
            status_code=400,
            detail="Streaming is not supported yet.",
        )

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
