import re

from liminus.base.backend import AuthSettings, Backend, ListenPathSettings
from liminus.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus.middlewares.staff_auth_session import StaffAuthSessionMiddleware
from liminus.settings import config


admin_backend = Backend(
    name='admin',
    listen=ListenPathSettings(
        path_regex=re.compile('^/admin(/|$)'),
        upstream_dsn=config['BACKEND_ADMIN_DSN'],
        strip_prefix=False,
    ),
    auth=AuthSettings(requires_staff_auth=True),
    middlewares=[StaffAuthSessionMiddleware, AddIpHeadersMiddleware, RestrictHeadersMiddleware],
)
