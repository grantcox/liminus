import re

from liminus.base.backend import Backend, ListenPathSettings
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus.settings import config


dev_cfsimulator_backend = Backend(
    name='dev-cf-simulator',
    listen=ListenPathSettings(
        path_regex=re.compile('^/(page|campaign|community_petitions|static)(/|$)'),
        upstream_dsn=config['BACKEND_WEB_ACT_DSN'],
        strip_prefix=False,
    ),
    middlewares=[RestrictHeadersMiddleware],
)
