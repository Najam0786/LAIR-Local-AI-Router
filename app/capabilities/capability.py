from enum import Enum

from pydantic import BaseModel, Field


class CapabilityType(str, Enum):
    """
    Core capabilities supported by AI models.
    """

    TEXT_GENERATION = "text_generation"

    REASONING = "reasoning"

    CODING = "coding"

    VISION = "vision"

    EMBEDDING = "embedding"

    FUNCTION_CALLING = "function_calling"

    TOOL_USE = "tool_use"

    TRANSLATION = "translation"

    SUMMARIZATION = "summarization"


class Capability(BaseModel):
    """
    Represents a single capability exposed by a model.
    """

    type: CapabilityType

    enabled: bool = True

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )