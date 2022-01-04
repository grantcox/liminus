from starlette.requests import Request
from starlette.responses import Response

from liminus.base.backend import Backend, ReqSettings
from liminus.base.middleware import GkRequestMiddleware
from liminus.middlewares.mixins.csrf_mixin import CsrfHandlerMixin
from liminus.middlewares.mixins.jwt_mixin import JwtHandlerMixin
from liminus.settings import config


class PublicSessionMiddleware(GkRequestMiddleware, CsrfHandlerMixin, JwtHandlerMixin):
    """
    This handler manages three functions regarding members on our public site:
     - Ensuring all public site visitors have a session, and CSRF token
     - Ensuring CSRF tokens are provided for all relevant requests (depending on backend and HTTP method)
     - Store authenticated member JWTs, and append these to all backend requests
    """

    SESSION_KEY_PREFIX = 'public_session_'
    SESSION_ID_COOKIE_NAME = config['PUBLIC_SESSION_COOKIE_NAME']
    SESSION_COOKIE_DOMAIN = config['PUBLIC_COOKIES_DOMAIN']
    SESSION_IDLE_TIMEOUT_SECONDS = config['PUBLIC_SESSION_IDLE_TIMEOUT_SECONDS']
    SESSION_STRICT_MAX_LIFETIME_SECONDS = config['PUBLIC_SESSION_STRICT_MAX_LIFETIME_SECONDS']

    CSRF_HEADER_NAME = config['PUBLIC_CSRF_HEADER_NAME']
    CSRF_SESSION_KEY = 'csrf-token'
    # allow a CSRF to be used more than once, during this very-short TTL
    CSRF_REUSE_GRACE_TTL_SECONDS = 3

    AUTH_JWT_HEADER = 'Member-Authentication-Jwt'
    JWKS_URL = config['MEMBER_AUTH_JWKS_URL']
    REFRESH_JWT_URL = config['MEMBER_AUTH_JWT_REFRESH_URL']
    REFRESH_JWT_IF_TTL_LESS_THAN_SECONDS = config['MEMBER_AUTH_JWT_REFRESH_IF_TTL_LESS_THAN_SECONDS']
    REFRESH_JWT_SEMAPHORE_TTL_SECONDS = 10

    async def handle_request(self, req: Request, settings: ReqSettings, backend: Backend):
        # if they already have a valid session, pull the session data
        # if this request needs a valid CSRF, validate it
        # if the session has an auth JWT, add it to the backend request
        session = await self._load_session(req)

        await self._verify_csrf_if_needed(req, session.session_id, settings)
        await self._append_jwt_if_present(req, session)

    async def handle_response(self, res: Response, req: Request, settings: ReqSettings, backend: Backend):
        session, is_new_session = await self._ensure_session(req)
        jwt_refresh_session = await self._store_jwt_if_present(res, session)

        needs_new_session = is_new_session or jwt_refresh_session
        if needs_new_session:
            # generate a new session
            session.session_id = self._generate_unique_session_id()
            self._append_session_cookie_to_response(res, session.session_id)

        await self._rotate_csrf_if_needed(req, res, session.session_id, force_refresh=needs_new_session)

        # we always save the session data even if it hasn't changed, to ensure the TTL is bumped
        await self._store_session(session)
