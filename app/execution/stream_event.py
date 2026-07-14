from pydantic import BaseModel


class StreamEvent(BaseModel):
    """
    One unit yielded by execution.runtime.stream_execute().

    Mirrors execute()'s never-raises contract for the streaming case:
    once a StreamingResponse has started, HTTP status can't change, so
    a failure becomes an event with `error` set instead of a raised
    exception.
    """

    delta: str = ""

    finish_reason: str | None = None

    completion_tokens: int | None = None

    prompt_tokens: int | None = None

    error: str | None = None
