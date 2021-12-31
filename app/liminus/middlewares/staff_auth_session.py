from urllib.parse import urlencode

from starlette.requests import Request
from starlette.responses import Response, RedirectResponse

from liminus.base import Backend, BaseGkHTTPMiddleware, ReqSettings
from liminus.middlewares.mixins.jwt_mixin import JwtHandlerMixin
from liminus.settings import config, logger


class StaffAuthSessionMiddleware(BaseGkHTTPMiddleware, JwtHandlerMixin):
    """
    This handler manages the session for staff on our campaign admin.
    It ensures a valid auth session and JWT are present for all requests to the campaign admin,
    and if not then it redirects the request to the Auth Service to initiate the Okta
    auth flow
    """

    SESSION_KEY_PREFIX = 'staff_sessions_'
    SESSION_ID_COOKIE_NAME = config['STAFF_SESSION_COOKIE_NAME']
    SESSION_COOKIE_DOMAIN = config['STAFF_SESSION_COOKIE_DOMAIN']
    SESSION_IDLE_TIMEOUT_SECONDS = config['STAFF_SESSION_IDLE_TIMEOUT_SECONDS']
    SESSION_STRICT_MAX_LIFETIME_SECONDS = config['STAFF_SESSION_STRICT_MAX_LIFETIME_SECONDS']

    AUTH_JWT_HEADER = 'Avaaz-Staff-Authentication-Jwt'
    JWKS_URL = config['STAFF_AUTH_JWKS_URL']
    REFRESH_JWT_URL = config['STAFF_AUTH_JWT_REFRESH_URL']
    REFRESH_JWT_IF_TTL_LESS_THAN_SECONDS = config['STAFF_AUTH_JWT_REFRESH_IF_TTL_LESS_THAN_SECONDS']
    REFRESH_JWT_SEMAPHORE_TTL_SECONDS = 10

    STAFF_AUTH_INIT_REDIRECT_LOGIN_URL = config['STAFF_AUTH_INIT_REDIRECT_LOGIN_URL']

    async def handle_request(self, req: Request, settings: ReqSettings, backend: Backend):
        # if they already have a valid session, pull the session data
        # if the session has an auth JWT, add it to the backend request
        # if they don't have an auth JWT and this is a restricted backend, redirect to the login
        session = await self._load_session(req)
        logger.info(f'staff auth session is: {session}')

        # do this JWT check first, as it will actually validate the JWT and remove it
        # if it's expired or otherwise invalid
        # this means below we can just check for any JWT and trust it's valid
        staff_jwt = await self._append_jwt_if_present(req, session)

        # for backwards compatibility, we also want this JWT in the standard Authorization header
        if staff_jwt:
            req.state.headers['Authorization'] = f'Bearer {staff_jwt}'
            logger.info(f'setting staff jwt header to {staff_jwt}')

        request_requires_staff_auth = self._is_staff_authn_required(settings)
        if request_requires_staff_auth and not staff_jwt:
            return self._redirect_to_staff_auth_login(req)

    async def handle_response(self, res: Response, req: Request, settings: ReqSettings, backend: Backend):
        session, is_new_session = await self._ensure_session(req)
        jwt_refresh_session = await self._store_jwt_if_present(res, session)

        if is_new_session or jwt_refresh_session:
            # generate a new session
            session.session_id = await self._generate_unique_session_id()
            self._append_session_cookie_to_response(
                res, session.session_id, age=self.SESSION_STRICT_MAX_LIFETIME_SECONDS
            )

        # we always save the session data even if it hasn't changed, to ensure the TTL is bumped
        await self._store_session(session)

    def _is_staff_authn_required(self, settings: ReqSettings) -> bool:
        if not settings.auth or not settings.auth.requires_staff_auth:
            return False

        return True

    def _redirect_to_staff_auth_login(self, request: Request) -> Response:
        # redirect this request to our Auth Service login init
        # with the initially requested URL as a param, so the user ends up at the right place
        redirect_params = '?' + urlencode({'url': request.url})
        login_redirect_url = self.STAFF_AUTH_INIT_REDIRECT_LOGIN_URL + redirect_params

        return RedirectResponse(login_redirect_url, 302)
