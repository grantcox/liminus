from liminus.base.backend import AuthSettings, Backend, ListenPathSettings
from liminus.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus.middlewares.staff_auth_session import StaffAuthSessionMiddleware
from liminus.settings import config


stats_service_backend = Backend(
    name='stats-service',
    listen=ListenPathSettings(
        prefix='/stats-internal/',
        upstream_dsn=config['BACKEND_STATS_SERVICE_DSN'],
        strip_prefix=True,
    ),
    auth=AuthSettings(requires_staff_auth=True),
    middlewares=[StaffAuthSessionMiddleware, AddIpHeadersMiddleware, RestrictHeadersMiddleware],
)
