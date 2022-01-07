from aioredis.client import Redis

from liminus import settings


# lazy init redis client
_redis_client = None


def redis_client():
    global _redis_client
    if not _redis_client:
        _redis_client = Redis.from_url(str(settings.REDIS_DSN))

    return _redis_client
