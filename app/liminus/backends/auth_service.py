import re

from liminus import settings
from liminus.base.backend import Backend, ListenPathSettings, PathRewrites
from liminus.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus.middlewares.staff_auth_session import StaffAuthSessionMiddleware


auth_service_backend = Backend(
    name='auth-service',
    listen=ListenPathSettings(
        path_regex=re.compile('^/(auth|auth-service)/'),
        upstream_dsn=settings.BACKEND_AUTH_SERVICE_DSN,
        strip_prefix=True,
        rewrites=[
            PathRewrites(path_from='/auth/saml/metadata', path_to='/staff/saml/metadata'),
            PathRewrites(path_from='/auth/saml/callback', path_to='/staff/saml/callback/login'),
        ],
    ),
    middlewares=[StaffAuthSessionMiddleware, AddIpHeadersMiddleware, RestrictHeadersMiddleware],
)
