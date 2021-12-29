from liminus.base import (
    Backend,
    CorsSettings,
    CsrfSettings,
    HeadersAllowedSettings,
    ListenPathSettings,
    RouteSettings,
)
from liminus.constants import Headers, HttpMethods
from liminus.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus.settings import config
from liminus.utils import get_env_var


service_name = 'donations'
donation_service_backend = None

if service_name in config['ENABLED_BACKENDS']:
    donation_service_backend = Backend(
        name=service_name,
        listen=[
            ListenPathSettings(
                prefix='/donation/',
                upstream_dsn=get_env_var('BACKEND_DONATIONS_DSN'),
                strip_prefix=True,
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
        routes=[
            RouteSettings(path='/donation/public_api/ping', allow_methods=[HttpMethods.GET]),
            RouteSettings(
                path_regex=(
                    '^/donation/public_api/'
                    '(get_donation_form_context|get_recurring_upsell_amount'
                    '|get_donation_receipt|get_user_donation_settings)/?$'
                ),
                allow_methods=[HttpMethods.GET],
            ),
            RouteSettings(
                path_regex=(
                    '/donation/public_api/'
                    '(new_donation|oneclick_donation|replace_donation|set_user_donation_settings)'
                ),
                allow_methods=[HttpMethods.POST],
            ),
        ],
    )
