import os
import redis.asyncio as redis
from fastapi import HTTPException, Request

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

CACHE_TTL = 3600  # 1 hour

async def get_cached_url(short_code: str) -> str | None:
    return await redis_client.get(f"url:{short_code}")

async def set_cached_url(short_code: str, original_url: str):
    await redis_client.setex(f"url:{short_code}", CACHE_TTL, original_url)

async def rate_limiter(request: Request, limit: int = 10, window: int = 60):
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{client_ip}"
    
    current = await redis_client.incr(key)
    if current == 1:
        await redis_client.expire(key, window)
    if current > limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

