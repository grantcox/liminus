from http import HTTPStatus
from typing import Optional

from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import Response

from liminus.middlewares.mixins.session_mixin import Session, SessionHandlerMixin
from liminus.proxy_request import http_request
from liminus.redis_client import redis_client
from liminus.settings import logger
from liminus.utils import get_cache_hash_key, to_seconds


class JwtHandlerMixin(SessionHandlerMixin):
    AUTH_JWT_HEADER: str
    JWKS_URL: URL
    REFRESH_JWT_URL: URL
    REFRESH_JWT_IF_TTL_LESS_THAN_SECONDS: int = to_seconds(minutes=30)
    REFRESH_JWT_SEMAPHORE_TTL_SECONDS: int = 10

    async def _store_jwt_if_present(self, response: Response, session: Session) -> bool:
        # if the response has a member auth JWT, create a new session (and CSRF) and add this JWT to it
        if self.AUTH_JWT_HEADER not in response.headers:
            return False

        # store this in the session too
        session.session_data = session.session_data or {}
        session.session_data['jwt'] = response.headers[self.AUTH_JWT_HEADER]

        # we don't want this JWT to be in our response, so remove it
        # if we delete the header entirely then Tyk will keep the upstream value, so we just have to overwrite
        response.headers[self.AUTH_JWT_HEADER] = ''

        # when we change auth levels, we always create a new session id, keeping existing data
        # but destroy the current one first
        await self._store_session(session.session_id, None)
        return True

    async def _append_jwt_if_present(self, request: Request, session: Session) -> Optional[str]:
        if not session.session_data or 'jwt' not in session.session_data:
            # nothing to do
            return None

        valid_jwt = session.session_data['jwt']

        if valid_jwt:
            # append the JWT to the backing service request
            request.state.headers[self.AUTH_JWT_HEADER] = valid_jwt
            logger.debug(f'{request} is for authenticated user, adding {self.AUTH_JWT_HEADER} header')
            return valid_jwt

        return None

    async def _refresh_jwt(self, jwt):
        # set a semaphore in Redis, so we only have one concurrent refresh request at a time
        semaphore_key = get_cache_hash_key('jwt-refresh-', jwt)
        semaphore_created = await redis_client().setnx(semaphore_key, '1')
        if not semaphore_created:
            # the semaphore already existed, this request should not attempt to refresh the JWT
            return jwt

        # this semaphore expires after a few seconds
        # we don't need to explicitly delete it - let it provide poor-man's rate limiting
        await redis_client().expire(semaphore_key, self.REFRESH_JWT_SEMAPHORE_TTL_SECONDS)

        response = await http_request('POST', self.REFRESH_JWT_URL, json={'jwt': jwt})
        if response.status == HTTPStatus.OK:
            if self.AUTH_JWT_HEADER in response.headers:
                # we got a nice new token
                return response.headers.getone(self.AUTH_JWT_HEADER)

        # could not be refreshed
        return None
