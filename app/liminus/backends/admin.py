import re

from liminus.base.backend import AuthSettings, Backend, ListenPathSettings
from liminus.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus.middlewares.staff_auth_session import StaffAuthSessionMiddleware
from liminus.settings import config
from liminus.utils import get_env_var


service_name = 'admin'
admin_backend = None

if service_name in config['ENABLED_BACKENDS']:
    admin_backend = Backend(
        name=service_name,
        listen=ListenPathSettings(
            path_regex=re.compile('^/admin(/|$)'),
            upstream_dsn=get_env_var('BACKEND_ADMIN_DSN'),
            strip_prefix=False,
        ),
        auth=AuthSettings(requires_staff_auth=True),
        middlewares=[StaffAuthSessionMiddleware, AddIpHeadersMiddleware, RestrictHeadersMiddleware],
    )
