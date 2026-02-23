from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.api_key import APIKey
from app.core.security import hash_api_key


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        if request.url.path.startswith("/api/v1/health"):
            return await call_next(request)

        api_key = request.headers.get("x-api-key")

        if not api_key:
            raise HTTPException(status_code=401, detail="Missing API key")

        key_hash = hash_api_key(api_key)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(APIKey).where(
                    APIKey.key_hash == key_hash,
                    APIKey.is_active == True,
                )
            )
            db_key = result.scalar_one_or_none()

            if not db_key:
                raise HTTPException(status_code=401, detail="Invalid API key")

            request.state.organization_id = db_key.organization_id
            request.state.api_key = api_key

        return await call_next(request)