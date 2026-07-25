from pydantic import BaseModel


class ModelInfo(BaseModel):
    """Represents a model available to LAIR."""

    id: str
    provider: str
    loaded: bool = True