import aioredis

from liminus.settings import config


class RedisHandlerMixin:
    # lazy init redis client
    _redis_client = None

    @property
    def redis_client(self):
        if not self._redis_client:
            if not config['REDIS_DSN']:
                raise EnvironmentError('No REDIS_DSN env var defined')
            self._redis_client = aioredis.from_url(config['REDIS_DSN'])
        return self._redis_client
