import re

from liminus.base.backend import Backend, ListenPathSettings, PathRewrites
from liminus.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus.middlewares.staff_auth_session import StaffAuthSessionMiddleware
from liminus.settings import config
from liminus.utils import get_env_var


service_name = 'auth-service'
auth_service_backend = None

if service_name in config['ENABLED_BACKENDS']:
    auth_service_backend = Backend(
        name=service_name,
        listen=ListenPathSettings(
            path_regex=re.compile('^/(auth|auth-service)/'),
            upstream_dsn=get_env_var('BACKEND_AUTH_SERVICE_DSN'),
            strip_prefix=True,
            rewrites=[
                PathRewrites(path_from='/auth/saml/metadata', path_to='/staff/saml/metadata'),
                PathRewrites(path_from='/auth/saml/callback', path_to='/staff/saml/callback/login'),
            ],
        ),
        middlewares=[StaffAuthSessionMiddleware, AddIpHeadersMiddleware, RestrictHeadersMiddleware],
    )
