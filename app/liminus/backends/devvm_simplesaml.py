from liminus import settings
from liminus.base.backend import Backend, ListenPathSettings
from liminus.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus.middlewares.staff_auth_session import StaffAuthSessionMiddleware


devvm_simplesaml_backend = Backend(
    name='devvm-simplesaml',
    listen=ListenPathSettings(
        prefix='/simplesaml/',
        upstream_dsn=settings.BACKEND_ADMIN_DSN,
        strip_prefix=False,
    ),
    middlewares=[StaffAuthSessionMiddleware, AddIpHeadersMiddleware, RestrictHeadersMiddleware],
)
