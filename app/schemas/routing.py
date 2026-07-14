from pydantic import BaseModel, Field

from app.routing.execution_plan import ExecutionPlan


class RoutingRequest(BaseModel):
    """
    Request sent to the routing engine.
    """

    prompt: str = Field(
        ...,
        min_length=1,
        description="User prompt to analyze.",
    )


class RoutingResponse(BaseModel):
    """
    Response returned by the routing engine.
    """

    plan: ExecutionPlan
