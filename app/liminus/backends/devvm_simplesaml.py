from liminus.base import AuthSettings, Backend, CorsSettings, HeadersAllowedSettings, ListenPathSettings
from liminus.constants import Headers
from liminus.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus.middlewares.staff_auth_session import StaffAuthSessionMiddleware
from liminus.settings import config
from liminus.utils import get_env_var


service_name = 'devvm-simplesaml'
devvm_simplesaml_backend = None

if service_name in config['ENABLED_BACKENDS']:
    devvm_simplesaml_backend = Backend(
        name=service_name,
        listen=[
            ListenPathSettings(
                prefix='/simplesaml/',
                upstream_dsn=get_env_var('BACKEND_ADMIN_DSN'),
                strip_prefix=False,
            ),
        ],
        middlewares=[RestrictHeadersMiddleware, AddIpHeadersMiddleware, StaffAuthSessionMiddleware],
    )
