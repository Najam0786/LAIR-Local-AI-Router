import time

from pydantic import BaseModel, Field

from app.execution.conversation import ChatMessage
from app.schemas.savings import LairMeta


class ChatCompletionRequest(BaseModel):
    """
    OpenAI-compatible /v1/chat/completions request.
    """

    model: str = Field(
        default="",
        description="Accepted for client compatibility; LAIR's routing "
        "decides the model actually used, ignoring this value.",
    )
    messages: list[ChatMessage]
    max_tokens: int = Field(
        default=1024,
        description="Deliberately not reusing BaseProvider.complete()'s "
        "default of 64, which was tuned for quick benchmark pings.",
    )
    stream: bool = False
    lair_no_cache: bool = Field(
        default=False,
        description="Per-request opt-out of the response cache (I-07), "
        "even when Settings.ENABLE_RESPONSE_CACHE is on. Not part of the "
        "OpenAI schema; unknown fields are safe for other clients to send.",
    )
    lair_document_id: str | None = Field(
        default=None,
        description="References a document ingested via POST "
        "/v1/lair/documents (I-08). When set, chunks relevant to the "
        "latest user message are retrieved and injected before "
        "forwarding to the model. Not part of the OpenAI schema.",
    )
    lair_project_scope: str | None = Field(
        default=None,
        description="Opaque project identifier for persistent memory "
        "(I-18, RFC-0002). When set and Settings.ENABLE_PROJECT_MEMORY "
        "is on, relevant memories are retrieved and injected, and new "
        "durable statements from this exchange are remembered under "
        "this scope. Not part of the OpenAI schema.",
    )


class ChatCompletionMessage(BaseModel):
    role: str = "assistant"
    content: str


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatCompletionMessage
    finish_reason: str | None = None


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: list[ChatCompletionChoice]
    usage: Usage
    lair_meta: LairMeta | None = None


class ChatCompletionChunkDelta(BaseModel):
    role: str | None = None
    content: str | None = None


class ChatCompletionChunkChoice(BaseModel):
    index: int = 0
    delta: ChatCompletionChunkDelta
    finish_reason: str | None = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: list[ChatCompletionChunkChoice]
    lair_meta: LairMeta | None = None


class OpenAIModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = 0
    owned_by: str


class OpenAIModelListResponse(BaseModel):
    object: str = "list"
    data: list[OpenAIModelInfo]
