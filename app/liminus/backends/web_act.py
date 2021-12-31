from liminus.base import Backend, CorsSettings, CsrfSettings, HeadersAllowedSettings, ListenPathSettings
from liminus.constants import Headers
from liminus.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus.middlewares.cors import GkCorsMiddleware
from liminus.middlewares.public_session_csrf_jwt import PublicSessionMiddleware
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus.settings import config
from liminus.utils import get_env_var


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
        middlewares=[RestrictHeadersMiddleware, AddIpHeadersMiddleware, PublicSessionMiddleware, GkCorsMiddleware],
    )
