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

    is_moe: bool = False

    active_params_b: float | None = None

    # I-16: whether this model is a plausible candidate for the
    # SSD-streaming routing tier (ADR-0021). Always False from a real
    # provider today -- LM Studio doesn't report this, and no provider
    # in this codebase actually executes via mmap/SSD streaming yet.
    # Set via `app.hardware.resource_resolver.detect_streamable()`,
    # never guessed here.
    streamable: bool = False
