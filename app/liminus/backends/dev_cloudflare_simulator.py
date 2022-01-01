import re

from liminus.base.backend import Backend, ListenPathSettings
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus.settings import config
from liminus.utils import get_env_var


service_name = 'dev-cf-simulator'
dev_cfsimulator_backend = None

if service_name in config['ENABLED_BACKENDS']:
    dev_cfsimulator_backend = Backend(
        name=service_name,
        listen=ListenPathSettings(
            path_regex=re.compile('^/(page|campaign|community_petitions|static)(/|$)'),
            upstream_dsn=get_env_var('BACKEND_WEB_ACT_DSN'),
            strip_prefix=False,
        ),
        middlewares=[RestrictHeadersMiddleware],
    )
