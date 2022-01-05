from aioredis.client import Redis

from liminus.settings import config


class RedisHandlerMixin:
    # lazy init redis client
    _redis_client = None

    @property
    def redis_client(self):
        if not self._redis_client:
            self._redis_client = Redis.from_url(config['REDIS_DSN'])

        return self._redis_client
