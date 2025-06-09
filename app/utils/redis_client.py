import os, aioredis, asyncio

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis: aioredis.Redis | None = None

async def init_redis_pool():
    global redis
    try:
        redis = await aioredis.from_url(
            REDIS_URL,
            encoding="utf8", decode_responses=True
        )
    except Exception as e:
        print(f"⚠️ Redis не доступен ({e}), кэширование отключено")
        redis = None
