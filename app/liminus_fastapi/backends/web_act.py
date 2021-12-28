from liminus_fastapi.base import Backend, CorsSettings, CsrfSettings, HeadersAllowedSettings, ListenPathSettings
from liminus_fastapi.constants import Headers
from liminus_fastapi.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus_fastapi.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus_fastapi.settings import config
from liminus_fastapi.utils import get_env_var


service_name = 'web-act'
web_act_backend = None

if service_name in config['ENABLED_BACKENDS']:
    web_act_backend = Backend(
        name=service_name,
        listen=[
            ListenPathSettings(
                prefix='/act/',
                upstream_dsn=get_env_var('BACKEND_WEB_ACT_DSN'),
                strip_prefix=False,
            ),
        ],
        CORS=CorsSettings(
            enable=True,
            allow_methods=['GET', 'POST'],
            expose_headers=[Headers.PUBLIC_CSRF_TOKEN],
            allow_credentials=False,
        ),
        CSRF=CsrfSettings(require_token=True, single_use=True),
        allowed_request_headers=HeadersAllowedSettings(
            allowlist=[
                *Headers.REQUEST_DEFAULT_ALLOW,
                'cf-ipcountry',
            ]
        ),
        middlewares=[RestrictHeadersMiddleware, AddIpHeadersMiddleware],
    )
