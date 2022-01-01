import re

from liminus.base.backend import Backend, ListenPathSettings


health_check_backend = Backend(
    name='health-check',
    listen=ListenPathSettings(
        path_regex=re.compile('^/health(/|$)'),
    ),
    middlewares=[],
)
