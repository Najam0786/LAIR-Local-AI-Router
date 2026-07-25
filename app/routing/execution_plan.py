from pydantic import BaseModel, Field

from app.routing.decision import DecisionRecord


class ExecutionStep(BaseModel):
    """
    One unit of work in an ExecutionPlan.
    """

    role: str = "primary"

    model_id: str

    provider: str

    depends_on: list[int] = Field(default_factory=list)


class ExecutionPlan(BaseModel):
    """
    Concrete, resolved sequence of ExecutionSteps for one Task.

    Contains a single step until a real Execution Planner exists.
    """

    steps: list[ExecutionStep]

    decision: DecisionRecord
