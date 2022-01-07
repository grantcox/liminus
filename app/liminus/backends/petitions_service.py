from liminus import settings
from liminus.base.backend import AuthSettings, Backend, ListenPathSettings
from liminus.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus.middlewares.staff_auth_session import StaffAuthSessionMiddleware
from liminus.utils import url_join


petitions_service_backend = Backend(
    name='petitions-service',
    listen=ListenPathSettings(
        prefix='/petitions-internal/',
        upstream_dsn=url_join(settings.BACKEND_PETITIONS_SERVICE_DSN, '/internal'),
        strip_prefix=True,
    ),
    auth=AuthSettings(requires_staff_auth=True),
    middlewares=[StaffAuthSessionMiddleware, AddIpHeadersMiddleware, RestrictHeadersMiddleware],
)
