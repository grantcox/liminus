from liminus.base.backend import Backend, ListenPathSettings
from liminus.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus.middlewares.staff_auth_session import StaffAuthSessionMiddleware
from liminus.settings import config


devvm_simplesaml_backend = Backend(
    name='devvm-simplesaml',
    listen=ListenPathSettings(
        prefix='/simplesaml/',
        upstream_dsn=config['BACKEND_ADMIN_DSN'],
        strip_prefix=False,
    ),
    middlewares=[StaffAuthSessionMiddleware, AddIpHeadersMiddleware, RestrictHeadersMiddleware],
)
