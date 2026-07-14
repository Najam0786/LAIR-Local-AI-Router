from pydantic import BaseModel


class ProviderStreamChunk(BaseModel):
    """
    One incremental piece of a provider's streaming completion.
    """

    delta: str = ""

    finish_reason: str | None = None

    completion_tokens: int | None = None

    prompt_tokens: int | None = None
