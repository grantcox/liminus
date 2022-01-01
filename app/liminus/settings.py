import logging

from liminus.constants import Headers
from liminus.utils import get_env_var, to_seconds


LOG_LEVEL = get_env_var('LOG_LEVEL', default='INFO').upper()

config = {
    'LOG_LEVEL': LOG_LEVEL,
    'DEBUG': get_env_var('DEBUG', '').lower() == 'true',
    ########################################################################################
    # General settings
    ########################################################################################
    'ENABLED_BACKENDS': [be.strip() for be in get_env_var('ENABLED_BACKENDS').split(',')],
    ########################################################################################
    # CORS settings
    ########################################################################################
    'CORSMiddleware_args': {
        'allow_origin_regex': get_env_var('APIS_CORS_ALLOWED_ORIGINS_REGEX'),
        # expose_headers are non-standard headers that client JS can read from a response
        'expose_headers': [Headers.PUBLIC_CSRF_TOKEN],
        # allow_credentials is whether clients should include cookies in requests
        'allow_credentials': True,
    },
    ########################################################################################
    # sentry settings
    ########################################################################################
    'SENTRY_DSN': get_env_var('SENTRY_DSN'),
    'REDIS_DSN': get_env_var('REDIS_DSN', ''),
    ########################################################################################
    # Staff session settings
    ########################################################################################
    'STAFF_SESSION_COOKIE_NAME': get_env_var('STAFF_SESSION_COOKIE_NAME'),
    'STAFF_SESSION_COOKIE_DOMAIN': get_env_var('STAFF_SESSION_COOKIE_DOMAIN'),
    'STAFF_SESSION_IDLE_TIMEOUT_SECONDS': to_seconds(minutes=30),
    'STAFF_SESSION_STRICT_MAX_LIFETIME_SECONDS': to_seconds(hours=12),
    'STAFF_AUTH_INIT_REDIRECT_LOGIN_URL': (
        get_env_var('BASEURL_FOR_SAML_REDIRECT') + '/auth-service/staff/saml/init'
    ),
    ########################################################################################
    # Staff auth JWT verification / refreshing
    ########################################################################################
    'STAFF_AUTH_JWKS_URL': get_env_var('BACKEND_AUTH_SERVICE_DSN') + '/jwks',
    'STAFF_AUTH_JWT_REFRESH_URL': get_env_var('BACKEND_AUTH_SERVICE_DSN') + '/internal/staff/jwt/refresh',
    'STAFF_AUTH_JWT_REFRESH_IF_TTL_LESS_THAN_SECONDS': to_seconds(minutes=30),
    ########################################################################################
    # Public / member session settings
    ########################################################################################
    'PUBLIC_SESSION_COOKIE_NAME': get_env_var('PUBLIC_SESSION_COOKIE_NAME'),
    'PUBLIC_CSRF_HEADER_NAME': 'Gk-Public-Csrf-Token',
    'PUBLIC_COOKIES_DOMAIN': get_env_var('PUBLIC_COOKIES_DOMAIN'),
    'PUBLIC_SESSION_IDLE_TIMEOUT_SECONDS': to_seconds(minutes=30),
    'PUBLIC_SESSION_STRICT_MAX_LIFETIME_SECONDS': to_seconds(hours=24),
    ########################################################################################
    # Member auth JWT verification / refreshing
    ########################################################################################
    'MEMBER_AUTH_JWKS_URL': get_env_var('BACKEND_AUTH_SERVICE_DSN', '') + '/jwks',
    'MEMBER_AUTH_JWT_REFRESH_URL': get_env_var('BACKEND_AUTH_SERVICE_DSN', '') + '/internal/members/jwt/refresh',
    'MEMBER_AUTH_JWT_REFRESH_IF_TTL_LESS_THAN_SECONDS': to_seconds(minutes=30),
    ########################################################################################
    # logging settings
    ########################################################################################
    'LOGGING_CONFIG': {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {'default': {'format': '%(levelname)-6s %(asctime)s %(name)s: %(message)s'}},
        'handlers': {
            'console': {'level': LOG_LEVEL, 'class': 'logging.StreamHandler', 'formatter': 'default'},
        },
        'loggers': {'': {'level': LOG_LEVEL, 'handlers': ['console'], 'propagate': True}},
    },
}
logger = logging.getLogger('liminus')
