import logging

from starlette.config import Config
from starlette.datastructures import URL, CommaSeparatedStrings, Secret

from liminus.constants import Headers
from liminus.utils import to_seconds, url_join


# this file follows the recommended Starlette config setup
#  see https://www.starlette.io/config/

env = Config('.env')

# General settings
DEBUG = env('DEBUG', cast=bool, default=False)
LOG_LEVEL = env('LOG_LEVEL', default='INFO').upper()
TESTING = env('TESTING', cast=bool, default=False)
IS_LOAD_TESTING = env('IS_LOAD_TESTING', cast=bool, default=False)

SENTRY_DSN = env('SENTRY_DSN', cast=URL)
REDIS_DSN = env('REDIS_DSN', cast=URL)

# Backends
ENABLED_BACKENDS = env('ENABLED_BACKENDS', cast=CommaSeparatedStrings)

BACKEND_AUTH_SERVICE_DSN = env('BACKEND_AUTH_SERVICE_DSN', cast=URL)
BACKEND_DONATIONS_DSN = env('BACKEND_DONATIONS_DSN', cast=URL)
BACKEND_MEMBERS_SERVICE_DSN = env('BACKEND_MEMBERS_SERVICE_DSN', cast=URL)
BACKEND_PETITIONS_SERVICE_DSN = env('BACKEND_PETITIONS_SERVICE_DSN', cast=URL)
BACKEND_STATS_SERVICE_DSN = env('BACKEND_STATS_SERVICE_DSN', cast=URL)
BACKEND_WEB_ACT_DSN = env('BACKEND_WEB_ACT_DSN', cast=URL)
BACKEND_ADMIN_DSN = env('BACKEND_ADMIN_DSN', cast=URL)

BACKEND_DONATIONS_SERVICE_AUTH_JWT = env('DONATION_SERVICE_JWT', cast=Secret)

# Campaign settings, eg for recaptcha
READONLY_DATABASE_DSN = env('READONLY_DATABASE_DSN', cast=URL)
CAMPAIGN_SETTINGS_CACHE_EXPIRY_SECONDS = 30
RECAPTCHA_VERIFY_URL = env('RECAPTCHA_VERIFY_URL', cast=URL)
RECAPTCHA_SECRET = env('RECAPTCHA_SECRET', cast=Secret)

# CORS settings
CORS_MIDDLEWARE_ARGS = {
    'allow_origin_regex': env('APIS_CORS_ALLOWED_ORIGINS_REGEX'),
    # expose_headers are non-standard headers that client JS can read from a response
    'expose_headers': [Headers.PUBLIC_CSRF_TOKEN],
    # allow_headers are non-standard headres that clients can submit with requests
    'allow_headers': [Headers.PUBLIC_CSRF_TOKEN, Headers.X_REQUESTED_WITH],
    # allow_credentials is whether clients should include cookies in requests
    'allow_credentials': True,
    'allow_methods': ['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS'],
}

# Staff session settings
STAFF_SESSION_COOKIE_NAME = env('STAFF_SESSION_COOKIE_NAME')
STAFF_SESSION_COOKIE_DOMAIN = env('STAFF_SESSION_COOKIE_DOMAIN')
STAFF_SESSION_IDLE_TIMEOUT_SECONDS = to_seconds(minutes=30)
STAFF_SESSION_STRICT_MAX_LIFETIME_SECONDS = to_seconds(hours=12)
STAFF_AUTH_INIT_URL = url_join(BACKEND_AUTH_SERVICE_DSN, '/staff/saml/init')

# Staff auth JWT verification / refreshing
STAFF_AUTH_JWKS_URL = url_join(BACKEND_AUTH_SERVICE_DSN, '/jwks')
STAFF_AUTH_JWT_REFRESH_URL = url_join(BACKEND_AUTH_SERVICE_DSN, '/staff/jwt/refresh')
STAFF_AUTH_JWT_REFRESH_IF_TTL_LESS_THAN_SECONDS = to_seconds(minutes=30)

# Public / member session settings
PUBLIC_SESSION_COOKIE_NAME = env('PUBLIC_SESSION_COOKIE_NAME')
PUBLIC_CSRF_HEADER_NAME = 'Gk-Public-Csrf-Token'
PUBLIC_COOKIES_DOMAIN = env('PUBLIC_COOKIES_DOMAIN')
PUBLIC_SESSION_IDLE_TIMEOUT_SECONDS = to_seconds(minutes=30)
PUBLIC_SESSION_STRICT_MAX_LIFETIME_SECONDS = to_seconds(hours=24)

# Member auth JWT verification / refreshing
MEMBER_AUTH_JWKS_URL = url_join(BACKEND_AUTH_SERVICE_DSN, '/jwks')
MEMBER_AUTH_JWT_REFRESH_URL = url_join(BACKEND_AUTH_SERVICE_DSN, '/internal/members/jwt/refresh')
MEMBER_AUTH_JWT_REFRESH_IF_TTL_LESS_THAN_SECONDS = to_seconds(minutes=30)

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'default': {'format': '%(levelname)-6s %(asctime)s %(name)s: %(message)s'}},
    'handlers': {
        'console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'loggers': {'': {'level': LOG_LEVEL, 'handlers': ['console'], 'propagate': True}},
}

# a default logger
logger = logging.getLogger('gk-py')
