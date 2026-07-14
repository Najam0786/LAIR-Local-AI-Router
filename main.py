from fastapi import FastAPI

from app.api.benchmarks import router as benchmarks_router
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.models import router as models_router
from app.api.routing import router as routing_router
from app.core.settings import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.include_router(health_router)
app.include_router(models_router)
app.include_router(routing_router)
app.include_router(benchmarks_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }