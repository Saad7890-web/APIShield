from fastapi import FastAPI
from app.core.config import get_settings
from app.api.v1 import health

from app.api.v1 import organizations
from app.api.v1 import api_keys

from app.middleware.auth import APIKeyMiddleware
from app.middleware.rate_limitter import RateLimiterMiddleware
from app.core.seed import seed_plans


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
)

@app.on_event("startup")
async def startup_event():
    await seed_plans()

app.add_middleware(APIKeyMiddleware)
app.add_middleware(RateLimiterMiddleware)

app.include_router(health.router, prefix="/api/v1")
app.include_router(organizations.router, prefix="/api/v1")
app.include_router(api_keys.router, prefix="/api/v1")