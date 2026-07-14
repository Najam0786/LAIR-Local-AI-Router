from pydantic import BaseModel

from app.capabilities.profile import CapabilityProfile
from app.providers.model_metadata import ModelMetadata


class AIModel(BaseModel):
    """
    Represents an AI model known to LAIR.
    """

    id: str
    provider: str

    loaded: bool = True

    profile: CapabilityProfile

    metadata: ModelMetadata | None = None