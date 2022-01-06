import asyncio
from http import HTTPStatus
from secrets import token_urlsafe

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from liminus.background_tasks import run_background_task
from liminus.base.backend import ReqSettings
from liminus.errors import ErrorResponse
from liminus.middlewares.mixins.redis_mixin import RedisHandlerMixin
from liminus.settings import config, logger
from liminus.utils import get_cache_hash_key


class CsrfHandlerMixin(RedisHandlerMixin):
    CSRF_HEADER_NAME = ''
    CSRF_SESSION_KEY = 'csrf-token'
    # allow a CSRF to be used more than once, during this very-short TTL
    CSRF_REUSE_GRACE_TTL_SECONDS = 3

    async def _rotate_csrf_if_needed(
        self, request: Request, response: Response, session_id: str, force_refresh: bool = False
    ):
        rotate_csrf = getattr(request.state, 'rotate_csrf', None) is not None
        if rotate_csrf or force_refresh:
            # generate a new CSRF token, add it to a custom response header
            # we would prefer to set the CSRF in a cookie too (as then browsers will always pick it up)
            # but Tyk only allows a single 'Set-Cookie' header per response,
            # so it could conflict with the session cookie
            new_csrf_token = token_urlsafe(32)
            await self._store_new_csrf(session_id, new_csrf_token)
            response.headers[self.CSRF_HEADER_NAME] = new_csrf_token

    async def _verify_csrf_if_needed(self, request: Request, session_id: str, settings: ReqSettings) -> bool:
        if not settings.csrf or not settings.csrf.require_token:
            # we don't need any CSRF for this backend
            return True

        if request.method not in settings.csrf.require_on_methods:
            # we don't need to check a CSRF token for this kind of request
            return True

        csrf_token_from_header = request.headers.get(self.CSRF_HEADER_NAME, '')
        if await self._is_valid_csrf(session_id, csrf_token_from_header):
            # a valid CSRF token was provided in the request headers

            if settings.csrf.single_use:
                # any time we use a token, we want to rotate it
                # this requires setting a response header in the response hook, not in this pre-hook
                # so set a flag here that we will pick up in the response hook
                await self._consume_csrf(session_id, csrf_token_from_header)
                request.state.rotate_csrf = True

            return True

        if config['IS_LOAD_TESTING']:
            # when load testing we check the redis keys, but don't actually fail out
            return True

        # CSRF token is required but not provided, fail out
        logger.info(f'{request} does not have expected CSRF token, failing out')
        # if we're failing due to an invalid CSRF token, we should also give them a new one
        new_csrf_token = token_urlsafe(32)
        await self._store_new_csrf(session_id, new_csrf_token)
        error_response = JSONResponse(
            {'error': 'Invalid CSRF Token'},
            status_code=HTTPStatus.UNAUTHORIZED,
            headers={self.CSRF_HEADER_NAME: new_csrf_token},
        )

        raise ErrorResponse(error_response)

    async def _store_new_csrf(self, session_id: str, new_csrf_token: str):
        # add a new token to this session's valid list
        cache_key = self._get_csrf_cache_key(session_id, new_csrf_token)
        await self.redis_client.set(cache_key, '1')

    async def _consume_csrf(self, session_id: str, csrf_token: str):
        cache_key = self._get_csrf_cache_key(session_id, csrf_token)
        await self.redis_client.expire(cache_key, self.CSRF_REUSE_GRACE_TTL_SECONDS)
        run_background_task(self._delete_csrf_after_grace_delay(cache_key))

    async def _delete_csrf_after_grace_delay(self, cache_key: str):
        await asyncio.sleep(self.CSRF_REUSE_GRACE_TTL_SECONDS)
        logger.info(f'deleting CSRF token after delay: {cache_key}')
        await self.redis_client.delete(cache_key)

    async def _is_valid_csrf(self, session_id: str, csrf_token: str) -> bool:
        if not csrf_token:
            return False

        cache_key = self._get_csrf_cache_key(session_id, csrf_token)
        value = await self.redis_client.get(cache_key)
        return (value is not None)

    def _get_csrf_cache_key(self, session_id: str, csrf_token: str) -> str:
        return get_cache_hash_key('csrf-', f'{session_id}-{csrf_token}')
