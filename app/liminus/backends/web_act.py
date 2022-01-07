from liminus import settings
from liminus.base.backend import Backend, CsrfSettings, HeadersAllowedSettings, ListenPathSettings
from liminus.constants import Headers
from liminus.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus.middlewares.public_session_csrf_jwt import PublicSessionMiddleware
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware


web_act_backend = Backend(
    name='web-act',
    listen=ListenPathSettings(
        prefix='/act/',
        upstream_dsn=settings.BACKEND_WEB_ACT_DSN,
        strip_prefix=False,
    ),
    csrf=CsrfSettings(require_token=True, single_use=True),
    allowed_request_headers=HeadersAllowedSettings(
        allowlist=set(
            [
                *Headers.REQUEST_DEFAULT_ALLOW,
                'cf-ipcountry',
            ]
        )
    ),
    middlewares=[PublicSessionMiddleware, AddIpHeadersMiddleware, RestrictHeadersMiddleware],
)
