import re

from liminus import settings
from liminus.base.backend import Backend, ListenPathSettings
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware


dev_cfsimulator_backend = Backend(
    name='dev-cf-simulator',
    listen=ListenPathSettings(
        path_regex=re.compile('^/(page|campaign|community_petitions|static)(/|$)'),
        upstream_dsn=settings.BACKEND_WEB_ACT_DSN,
        strip_prefix=False,
    ),
    middlewares=[RestrictHeadersMiddleware],
)
