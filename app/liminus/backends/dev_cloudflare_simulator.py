from liminus.base import Backend, ListenPathSettings
from liminus.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus.middlewares.staff_auth_session import StaffAuthSessionMiddleware
from liminus.settings import config
from liminus.utils import get_env_var


service_name = 'dev-cf-simulator'
dev_cfsimulator_backend = None

if service_name in config['ENABLED_BACKENDS']:
    dev_cfsimulator_backend = Backend(
        name=service_name,
        listen=[
            ListenPathSettings(
                prefix_regex='/(page|campaign|community_petitions|static)(/|$)',
                upstream_dsn=get_env_var('BACKEND_WEB_ACT_DSN'),
                strip_prefix=False,
            ),
        ],
        middlewares=[RestrictHeadersMiddleware, AddIpHeadersMiddleware, StaffAuthSessionMiddleware],
    )
