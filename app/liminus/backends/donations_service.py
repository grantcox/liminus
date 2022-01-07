import re

from liminus import settings
from liminus.base.backend import (
    Backend,
    CsrfSettings,
    HeadersAllowedSettings,
    ListenPathSettings,
    RecaptchaEnabled,
    RecaptchaSettings,
    RouteSettings,
)
from liminus.constants import Headers, HttpMethods
from liminus.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus.middlewares.public_session_csrf_jwt import PublicSessionMiddleware
from liminus.middlewares.recaptcha_check import RecaptchaCheckMiddleware
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware


donation_service_backend = Backend(
    name='donations',
    listen=ListenPathSettings(
        prefix='/donation/',
        upstream_dsn=settings.BACKEND_DONATIONS_DSN,
        strip_prefix=True,
        extra_headers=[(Headers.AUTHORIZATION, f'JWT {str(settings.BACKEND_DONATIONS_SERVICE_AUTH_JWT)}')],
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
    middlewares=[AddIpHeadersMiddleware, PublicSessionMiddleware, RecaptchaCheckMiddleware, RestrictHeadersMiddleware],
    routes=[
        RouteSettings(path='/donation/public_api/ping', allow_methods=[HttpMethods.GET]),
        RouteSettings(
            path='/donation/public_api/new_donation',
            allow_methods=[HttpMethods.POST],
            recaptcha=RecaptchaSettings(enabled=RecaptchaEnabled.CAMPAIGN_SETTING),
        ),
        RouteSettings(
            path_regex=re.compile(
                '/donation/public_api/({})'.format(
                    '|'.join(
                        [
                            'get_donation_form_context',
                            'get_donation_receipt',
                            'get_user_donation_settings',
                            'oneclick_donation',
                            'replace_donation',
                            'set_user_donation_settings',
                        ]
                    )
                )
            ),
            allow_methods=[HttpMethods.POST],
        ),
    ],
)
