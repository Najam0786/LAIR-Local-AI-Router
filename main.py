from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.models import router as models_router
from app.core.settings import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Local AI Router (LAIR)",
)

app.include_router(health_router)
app.include_router(models_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to LAIR",
        "docs": "/docs",
        "health": "/health",
    }