from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    application: str
    version: str