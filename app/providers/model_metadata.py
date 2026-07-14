from pydantic import BaseModel


class ModelMetadata(BaseModel):
    """
    Provider-agnostic metadata a provider can report about a model.

    Providers translate their own API shape into this before it
    reaches CapabilityResolver/ResourceResolver -- neither resolver
    should ever see provider-specific field names.
    """

    is_vision: bool = False

    is_embedding: bool = False

    supports_tool_use: bool = False

    context_window: int | None = None

    quantization: str | None = None

    loaded: bool = True
