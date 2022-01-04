from http import HTTPStatus
from secrets import token_urlsafe

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from liminus.base.backend import ReqSettings
from liminus.errors import ErrorResponse
from liminus.middlewares.mixins.redis_mixin import RedisHandlerMixin
from liminus.settings import logger
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
            csrf_token = await self._add_new_csrf(session_id)
            response.headers[self.CSRF_HEADER_NAME] = csrf_token

    async def _verify_csrf_if_needed(self, request: Request, session_id: str, settings: ReqSettings) -> bool:
        if not settings.CSRF or not settings.CSRF.require_token:
            # we don't need any CSRF for this backend
            return True

        if request.method not in settings.CSRF.require_on_methods:
            # we don't need to check a CSRF token for this kind of request
            return True

        csrf_token_from_header = request.headers.get(self.CSRF_HEADER_NAME, '')
        if await self._is_valid_current_csrf(session_id, csrf_token_from_header):
            # a valid CSRF token was provided in the request headers

            if settings.CSRF.single_use:
                # any time we use a token, we want to rotate it
                # this requires setting a response header in the response hook, not in this pre-hook
                # so set a flag here that we will pick up in the response hook
                self._consume_csrf(session_id, csrf_token_from_header)
                request.state.rotate_csrf = True

            return True

        if self._is_just_used_csrf(session_id, csrf_token_from_header):
            # this CSRF token has already been consumed, but very recently (probably from a concurrent request)
            # let this request go through, but we will not attach a fresh CSRF to this response
            return True

        await self._fail_with_csrf_token_error(request, session_id)
        return False

    async def _add_new_csrf(self, session_id: str) -> str:
        # add a new token to this session's valid list
        valid_keys_key = self._get_valid_csrfs_cache_key(session_id)
        new_csrf_token = token_urlsafe(32)

        await self.redis_client.lpush(valid_keys_key, new_csrf_token)
        # ensure we only allow 3 concurrent CSRF tokens
        await self.redis_client.ltrim(valid_keys_key, start=0, end=2)

        return new_csrf_token

    async def _consume_csrf(self, session_id: str, csrf_token: str):
        # remove the CSRF from the valid list, and put it in a key with very short TTL for concurrent requests
        # add the 'just used' first, so there is no possible race condition where the CSRF is missing
        just_used_key = self._get_just_used_csrf_cache_key(session_id, csrf_token)
        await self.redis_client.setex(just_used_key, self.CSRF_REUSE_GRACE_TTL_SECONDS, 'used')

        # delete this key from the list of unused keys
        valid_keys_key = self._get_valid_csrfs_cache_key(session_id)
        await self.redis_client.lrem(valid_keys_key, count=0, value=csrf_token)

    async def _is_valid_current_csrf(self, session_id: str, csrf_token: str) -> bool:
        if not csrf_token:
            return False

        valid_keys_key = self._get_valid_csrfs_cache_key(session_id)
        valid_keys = await self.redis_client.lrange(valid_keys_key, 0, 3)
        return bytes(csrf_token, 'utf-8') in valid_keys

    async def _is_just_used_csrf(self, session_id: str, csrf_token: str) -> bool:
        just_used_key = self._get_just_used_csrf_cache_key(session_id, csrf_token)
        just_used = await self.redis_client.get(just_used_key)
        return just_used == b'used'

    def _get_valid_csrfs_cache_key(self, session_id: str) -> str:
        return get_cache_hash_key('valid-csrfs-', session_id)

    def _get_just_used_csrf_cache_key(self, session_id: str, csrf_token: str) -> str:
        return get_cache_hash_key('just_used-csrf-', f'{session_id}-{csrf_token}')

    async def _fail_with_csrf_token_error(self, request: Request, session_id: str):
        logger.info(f'{request} does not have expected CSRF token')

        # if we're failing due to an invalid CSRF token, we should also give them a new one
        csrf_token = await self._add_new_csrf(session_id)
        error_response = JSONResponse(
            {'error': 'Invalid CSRF Token'},
            status_code=HTTPStatus.UNAUTHORIZED,
            headers={self.CSRF_HEADER_NAME: csrf_token},
        )

        raise ErrorResponse(error_response)
