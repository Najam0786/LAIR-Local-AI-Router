from pydantic import BaseModel, Field

from app.capabilities.capability import CapabilityType


class CapabilityRequirement(BaseModel):
    """
    Represents a capability required to satisfy a user request.
    """

    capability: CapabilityType

    required: bool = True

    minimum_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    weight: float = Field(
        default=1.0,
        ge=0.0,
    )