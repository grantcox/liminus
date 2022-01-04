from liminus.base.backend import AuthSettings, Backend, ListenPathSettings
from liminus.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus.middlewares.staff_auth_session import StaffAuthSessionMiddleware
from liminus.settings import config
from liminus.utils import get_env_var


service_name = 'petitions-service'
petitions_service_backend = None

if service_name in config['ENABLED_BACKENDS']:
    petitions_service_backend = Backend(
        name=service_name,
        listen=ListenPathSettings(
            prefix='/petitions-internal/',
            upstream_dsn=get_env_var('BACKEND_PETITIONS_SERVICE_DSN') + '/internal',
            strip_prefix=True,
        ),
        auth=AuthSettings(requires_staff_auth=True),
        middlewares=[StaffAuthSessionMiddleware, AddIpHeadersMiddleware, RestrictHeadersMiddleware],
    )
