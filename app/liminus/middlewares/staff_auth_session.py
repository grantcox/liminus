from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from liminus import settings
from liminus.base.backend import Backend, ReqSettings
from liminus.base.middleware import GkRequestMiddleware
from liminus.middlewares.mixins.jwt_mixin import JwtHandlerMixin


logger = settings.logger


class StaffAuthSessionMiddleware(GkRequestMiddleware, JwtHandlerMixin):
    """
    This handler manages the session for staff on our campaign admin.
    It ensures a valid auth session and JWT are present for all requests to the campaign admin,
    and if not then it redirects the request to the Auth Service to initiate the Okta
    auth flow
    """

    SESSION_KEY_PREFIX = 'staff_sessions_'
    SESSION_ID_COOKIE_NAME = settings.STAFF_SESSION_COOKIE_NAME
    SESSION_COOKIE_DOMAIN = settings.STAFF_SESSION_COOKIE_DOMAIN
    SESSION_IDLE_TIMEOUT_SECONDS = settings.STAFF_SESSION_IDLE_TIMEOUT_SECONDS
    SESSION_STRICT_MAX_LIFETIME_SECONDS = settings.STAFF_SESSION_STRICT_MAX_LIFETIME_SECONDS

    AUTH_JWT_HEADER = 'Staff-Authentication-Jwt'
    JWKS_URL = settings.STAFF_AUTH_JWKS_URL
    REFRESH_JWT_URL = settings.STAFF_AUTH_JWT_REFRESH_URL
    REFRESH_JWT_IF_TTL_LESS_THAN_SECONDS = settings.STAFF_AUTH_JWT_REFRESH_IF_TTL_LESS_THAN_SECONDS
    REFRESH_JWT_SEMAPHORE_TTL_SECONDS = 10

    STAFF_AUTH_INIT_REDIRECT_LOGIN_URL = settings.STAFF_AUTH_INIT_REDIRECT_LOGIN_URL

    async def handle_request(self, req: Request, reqset: ReqSettings, backend: Backend):
        # if they already have a valid session, pull the session data
        # if the session has an auth JWT, add it to the backend request
        # if they don't have an auth JWT and this is a restricted backend, redirect to the login
        session = await self._load_session(req)

        # do this JWT check first, as it will actually validate the JWT and remove it
        # if it's expired or otherwise invalid
        # this means below we can just check for any JWT and trust it's valid
        staff_jwt = await self._append_jwt_if_present(req, session)

        # for backwards compatibility, we also want this JWT in the standard Authorization header
        if staff_jwt:
            req.state.headers['Authorization'] = f'Bearer {staff_jwt}'

        request_requires_staff_auth = self._is_staff_authn_required(reqset)
        if request_requires_staff_auth and not staff_jwt:
            logger.debug(f'{req} requires staff auth but none yet present, redirecting to SAML login flow')
            # TODO: just make a sub-request to the Auth Service, and return that response
            return self._redirect_to_staff_auth_login(req)

    async def handle_response(self, res: Response, req: Request, reqset: ReqSettings, backend: Backend):
        session, is_new_session = await self._ensure_session(req)
        jwt_refresh_session = await self._store_jwt_if_present(res, session)

        if is_new_session or jwt_refresh_session:
            # generate a new session
            session.session_id = self._generate_unique_session_id()
            self._append_session_cookie_to_response(
                res, session.session_id, age=self.SESSION_STRICT_MAX_LIFETIME_SECONDS
            )

        # we always save the session data even if it hasn't changed, to ensure the TTL is bumped
        await self._store_session(session)

    def _is_staff_authn_required(self, reqset: ReqSettings) -> bool:
        if not reqset.auth or not reqset.auth.requires_staff_auth:
            return False

        return True

    def _redirect_to_staff_auth_login(self, request: Request) -> Response:
        # redirect this request to our Auth Service login init
        # with the initially requested URL as a param, so the user ends up at the right place
        after_login = request.url.replace(scheme='https')
        login_redirect_url = self.STAFF_AUTH_INIT_REDIRECT_LOGIN_URL.include_query_params(url=after_login)

        return RedirectResponse(str(login_redirect_url), 302)
