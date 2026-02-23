from fastapi import FastAPI
from app.core.config import get_settings
from app.api.v1 import health

from app.api.v1 import organizations
from app.api.v1 import api_keys

from app.middleware.auth import APIKeyMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
)

app.add_middleware(APIKeyMiddleware)
app.add_middleware(RateLimiterMiddleware)

app.include_router(health.router, prefix="/api/v1")
app.include_router(organizations.router, prefix="/api/v1")
app.include_router(api_keys.router, prefix="/api/v1")