from fastapi import APIRouter

from app.registry.registry import registry

router = APIRouter(tags=["Models"])


@router.get("/models")
async def list_models():
    """
    Return all models currently available from the registry.
    """
    return await registry.list_models()