import os
import redis.asyncio as aioredis
from app.config import settings

_redis_client = None

async def get_redis():
    if settings.DEMO_MODE:
        return None
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client

async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
