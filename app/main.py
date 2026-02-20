from fastapi import FastAPI
from app.core.config import get_settings
from app.api.v1 import health

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
)

app.include_router(health.router, prefix="/api/v1")