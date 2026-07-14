from pydantic import BaseModel, Field

from app.capabilities.capability import CapabilityType


class RoutingPolicy(BaseModel):
    """
    Single source of truth for routing scoring weights.
    """

    version: str = "v2"

    streaming_weight: float = Field(default=10.0, ge=0.0)

    context_window_weight: float = Field(default=0.00001, ge=0.0)

    benchmark_weight: float = Field(default=0.1, ge=0.0)

    capability_weights: dict[CapabilityType, float] = Field(
        default_factory=lambda: {
            CapabilityType.REASONING: 15.0,
            CapabilityType.CODING: 12.0,
            CapabilityType.VISION: 10.0,
            CapabilityType.TEXT_GENERATION: 8.0,
            CapabilityType.FUNCTION_CALLING: 8.0,
            CapabilityType.TOOL_USE: 8.0,
            CapabilityType.SUMMARIZATION: 6.0,
            CapabilityType.TRANSLATION: 6.0,
            CapabilityType.EMBEDDING: 4.0,
        }
    )


default_policy = RoutingPolicy()
