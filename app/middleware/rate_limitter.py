import time
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.redis import redis_client


RATE_LIMIT = 100        # requests
WINDOW_SIZE = 60        # seconds


class RateLimiterMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        if request.url.path.startswith("/api/v1/health"):
            return await call_next(request)

        api_key = getattr(request.state, "api_key", None)

        if not api_key:
            return await call_next(request)

        redis_key = f"rate_limit:{api_key}"
        current_time = time.time()
        window_start = current_time - WINDOW_SIZE

      
        await redis_client.zremrangebyscore(redis_key, 0, window_start)

        
        request_count = await redis_client.zcard(redis_key)

        if request_count >= RATE_LIMIT:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
            )

        
        await redis_client.zadd(
            redis_key,
            {str(current_time): current_time},
        )

        await redis_client.expire(redis_key, WINDOW_SIZE)

        return await call_next(request)