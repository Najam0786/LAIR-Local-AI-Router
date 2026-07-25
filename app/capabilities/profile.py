from pydantic import BaseModel, Field

from app.capabilities.capability import Capability


class CapabilityProfile(BaseModel):
    """
    Describes the capabilities and metadata of an AI model.
    """

    model_id: str
    provider: str

    capabilities: list[Capability] = Field(default_factory=list)

    context_window: int | None = None

    max_output_tokens: int | None = None

    supports_streaming: bool = True