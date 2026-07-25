import time
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.cache.response_cache import CachedResponse, cache_key_for, default_response_cache
from app.core.settings import settings
from app.costs.budget import default_cloud_budget_ledger
from app.costs.calculator import default_cost_calculator
from app.costs.ledger import default_savings_ledger
from app.execution.context_compression import (
    default_context_compressor,
    needs_compression,
)
from app.execution.conversation import ChatMessage, Conversation
from app.execution.execution_outcome import ExecutionOutcome
from app.execution.runtime import execute, stream_execute
from app.memory.extraction import extract_candidate_memory
from app.memory.retrieval import retrieve_relevant_memories
from app.memory.store import default_memory_store
from app.models.task import Task
from app.rag.embeddings import default_embedding_model
from app.rag.retrieval import retrieve_relevant_chunks
from app.registry.provider_registry import provider_registry
from app.routing.cloud_escalation import default_cloud_escalator, evaluate_escalation
from app.routing.complexity_classifier import default_complexity_classifier
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
from app.schemas.savings import LairMeta


def _estimate_and_record_savings(
    model_id: str,
    prompt_tokens: int | None,
    completion_tokens: int | None,
) -> LairMeta:
    savings_usd = default_cost_calculator.estimate_savings_usd(
        model_id,
        prompt_tokens or 0,
        completion_tokens or 0,
    )

    if savings_usd is not None:
        default_savings_ledger.record(model_id, savings_usd)

    return LairMeta(model_used=model_id, estimated_savings_usd=savings_usd)


def _remember_if_candidate(project_scope: str | None, prompt: str) -> None:
    """
    Extracts and stores a durable memory from `prompt` under
    `project_scope` (I-18) -- a no-op when memory is disabled, no
    scope was given, or the prompt didn't match a durable-statement
    pattern. Never raises: a failed extraction/embedding should never
    fail the chat request it's a side effect of.
    """

    if not settings.ENABLE_PROJECT_MEMORY or not project_scope:
        return

    candidate = extract_candidate_memory(prompt)

    if candidate is None:
        return

    embedding = default_embedding_model.embed_one(candidate)
    default_memory_store.remember(project_scope, candidate, embedding)


def _response_from_cache(cached: CachedResponse) -> ChatCompletionResponse:
    """
    Serves a cache hit (I-07) without touching routing, execution, or
    the savings ledger -- no real inference happened, so there is no
    real token count to honestly base a savings estimate on.
    """

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        model=cached.model_id,
        choices=[
            ChatCompletionChoice(
                message=ChatCompletionMessage(content=cached.text),
                finish_reason=cached.finish_reason or "stop",
            )
        ],
        usage=Usage(
            prompt_tokens=cached.prompt_tokens or 0,
            completion_tokens=cached.completion_tokens or 0,
            total_tokens=(cached.prompt_tokens or 0) + (cached.completion_tokens or 0),
        ),
        lair_meta=LairMeta(model_used=cached.model_id, cache_hit=True),
    )


def _response_from_cloud(
    text: str,
    outcome: ExecutionOutcome,
    reason: str,
) -> ChatCompletionResponse:
    """
    Builds a response from a successful cloud escalation (I-06,
    RFC-0001) -- separate from `_estimate_and_record_savings`: this
    path *spends* real money rather than avoiding it, so no savings
    estimate is attached.
    """

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        model=settings.CLOUD_PROVIDER_MODEL_ID,
        choices=[
            ChatCompletionChoice(
                message=ChatCompletionMessage(content=text),
                finish_reason=outcome.finish_reason or "stop",
            )
        ],
        usage=Usage(
            prompt_tokens=outcome.prompt_tokens or 0,
            completion_tokens=outcome.completion_tokens or 0,
            total_tokens=(outcome.prompt_tokens or 0) + (outcome.completion_tokens or 0),
        ),
        lair_meta=LairMeta(
            model_used=settings.CLOUD_PROVIDER_MODEL_ID,
            routed_to_cloud=True,
            cloud_escalation_reason=reason,
        ),
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

    cache_enabled = (
        not request.stream
        and settings.ENABLE_RESPONSE_CACHE
        and not request.lair_no_cache
    )
    cache_key = None

    if cache_enabled:
        cache_key = cache_key_for([m.model_dump() for m in request.messages])
        cached = default_response_cache.get(cache_key)

        if cached is not None:
            return _response_from_cache(cached)

    models = await provider_registry.list_models()

    if not models:
        raise HTTPException(
            status_code=503,
            detail="No AI models are currently available.",
        )

    conversation = Conversation(messages=request.messages)
    task = Task(
        prompt=conversation.latest_user_message(),
        conversation_turns=len(conversation.messages),
    )

    complexity_override = await default_complexity_classifier.classify(task.prompt)

    try:
        plan = routing_engine.route(
            task=task, models=models, complexity_override=complexity_override
        )
    except NoCandidateModelsError:
        raise HTTPException(
            status_code=404,
            detail="No suitable model found for this request.",
        )

    # Cloud escalation (I-06, RFC-0001): non-streaming only for this
    # pass. A failed cloud call falls through to local execution below
    # rather than failing the request -- graceful degradation, not a
    # hard dependency on the cloud tier being available.
    if not request.stream and settings.ENABLE_CLOUD_ESCALATION:
        escalation = evaluate_escalation(
            task.prompt,
            complexity_override or plan.decision.complexity,
            plan.decision.confidence,
        )

        if escalation.should_escalate:
            cloud_result, cloud_outcome = await default_cloud_escalator.execute(
                conversation.messages, request.max_tokens
            )

            if cloud_outcome.success:
                default_cloud_budget_ledger.record(
                    default_cloud_escalator.actual_cost_usd(cloud_outcome)
                )
                return _response_from_cloud(
                    cloud_result.text, cloud_outcome, escalation.reason
                )

    if request.lair_document_id:
        context_window = plan.decision.selected_model.profile.context_window
        retrieval_budget = settings.RAG_RETRIEVAL_TOKEN_BUDGET

        if context_window:
            retrieval_budget = min(retrieval_budget, context_window // 2)

        retrieved_chunks = retrieve_relevant_chunks(
            request.lair_document_id,
            task.prompt,
            settings.RAG_RETRIEVAL_TOP_K,
            retrieval_budget,
        )

        if retrieved_chunks:
            conversation = Conversation(
                messages=[
                    ChatMessage(
                        role="system",
                        content=(
                            "Relevant excerpts from the ingested document:\n\n"
                            + "\n\n---\n\n".join(retrieved_chunks)
                        ),
                    ),
                    *conversation.messages,
                ]
            )

    memory_injected_count = 0

    if settings.ENABLE_PROJECT_MEMORY and request.lair_project_scope:
        context_window = plan.decision.selected_model.profile.context_window
        memory_budget = settings.MEMORY_TOKEN_BUDGET

        if context_window:
            memory_budget = min(memory_budget, context_window // 4)

        retrieved_memories = retrieve_relevant_memories(
            request.lair_project_scope,
            task.prompt,
            settings.MEMORY_RETRIEVAL_TOP_K,
            memory_budget,
            store=default_memory_store,
            embedding_model=default_embedding_model,
        )

        if retrieved_memories:
            memory_injected_count = len(retrieved_memories)
            conversation = Conversation(
                messages=[
                    ChatMessage(
                        role="system",
                        content=(
                            "Relevant memory from earlier in this project:\n\n"
                            + "\n".join(f"- {m}" for m in retrieved_memories)
                        ),
                    ),
                    *conversation.messages,
                ]
            )

    if settings.ENABLE_CONTEXT_COMPRESSION:
        context_window = plan.decision.selected_model.profile.context_window

        if context_window and needs_compression(
            conversation.messages,
            context_window,
            settings.CONTEXT_COMPRESSION_THRESHOLD,
        ):
            conversation = Conversation(
                messages=await default_context_compressor.compress(
                    conversation.messages,
                    settings.CONTEXT_COMPRESSION_KEEP_RECENT_TURNS,
                    settings.CONTEXT_COMPRESSION_SUMMARIZER_MODEL_ID,
                )
            )

    if request.stream:
        return StreamingResponse(
            _stream_chat_completion(
                plan.decision,
                conversation,
                request.max_tokens,
                request.lair_project_scope,
                task.prompt,
                memory_injected_count,
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

    if cache_key is not None:
        default_response_cache.put(
            cache_key,
            CachedResponse(
                text=result.text,
                finish_reason=outcome.finish_reason,
                completion_tokens=outcome.completion_tokens,
                prompt_tokens=outcome.prompt_tokens,
                model_id=plan.decision.selected_model.id,
                cached_at=time.time(),
            ),
        )

    _remember_if_candidate(request.lair_project_scope, task.prompt)

    lair_meta = _estimate_and_record_savings(
        plan.decision.selected_model.id,
        outcome.prompt_tokens,
        outcome.completion_tokens,
    )
    lair_meta.memory_injected_count = memory_injected_count

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
        lair_meta=lair_meta,
    )


async def _stream_chat_completion(
    decision: DecisionRecord,
    conversation: Conversation,
    max_tokens: int,
    project_scope: str | None = None,
    prompt: str = "",
    memory_injected_count: int = 0,
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

    lair_meta = None

    if error is None:
        _remember_if_candidate(project_scope, prompt)
        lair_meta = _estimate_and_record_savings(
            model_id, prompt_tokens, completion_tokens
        )
        lair_meta.memory_injected_count = memory_injected_count

    yield sse(
        ChatCompletionChunk(
            id=completion_id,
            model=model_id,
            choices=[
                ChatCompletionChunkChoice(
                    delta=ChatCompletionChunkDelta(), finish_reason="stop"
                )
            ],
            lair_meta=lair_meta,
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
