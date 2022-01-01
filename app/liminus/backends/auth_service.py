from liminus.base.backend import Backend, ListenPathSettings
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
            prefix='/auth-service/',
            upstream_dsn=get_env_var('BACKEND_AUTH_SERVICE_DSN'),
            strip_prefix=True,
        ),
        middlewares=[StaffAuthSessionMiddleware, AddIpHeadersMiddleware, RestrictHeadersMiddleware],
    )
