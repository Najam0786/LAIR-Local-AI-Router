import time

from pydantic import BaseModel, Field

from app.execution.conversation import ChatMessage


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


class OpenAIModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = 0
    owned_by: str


class OpenAIModelListResponse(BaseModel):
    object: str = "list"
    data: list[OpenAIModelInfo]
