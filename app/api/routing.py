from fastapi import APIRouter, HTTPException

from app.models.task import Task
from app.registry.provider_registry import provider_registry
from app.routing.routing_engine import routing_engine
from app.routing.selector import NoCandidateModelsError
from app.schemas.routing import RoutingRequest, RoutingResponse

router = APIRouter(tags=["Routing"])


@router.post("/route", response_model=RoutingResponse)
async def route_request(request: RoutingRequest) -> RoutingResponse:
    """
    Route a prompt to the most suitable AI model.
    """

    models = await provider_registry.list_models()

    if not models:
        raise HTTPException(
            status_code=503,
            detail="No AI models are currently available.",
        )

    task = Task(prompt=request.prompt)

    try:
        plan = routing_engine.route(
            task=task,
            models=models,
        )

    except NoCandidateModelsError:
        raise HTTPException(
            status_code=404,
            detail="No suitable model found for this request.",
        )

    return RoutingResponse(plan=plan)
