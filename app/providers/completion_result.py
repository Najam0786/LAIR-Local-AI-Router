from pydantic import BaseModel, Field


class CompletionResult(BaseModel):
    """
    Raw output of a single completion call to a provider.
    """

    text: str

    completion_tokens: int = Field(ge=0)

    latency_seconds: float = Field(ge=0.0)
