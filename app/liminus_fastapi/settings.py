import logging
from os import getenv

from liminus_fastapi.utils import get_env_var


LOG_LEVEL = get_env_var('LOG_LEVEL', default='INFO').upper()
config = {
    'LOG_LEVEL': LOG_LEVEL,
    'DEBUG': get_env_var('DEBUG', '').lower() == 'true',
    ########################################################################################
    # General settings
    ########################################################################################
    'ENABLED_BACKENDS': get_env_var('ENABLED_BACKENDS').split(','),
    ########################################################################################
    # CORS settings
    ########################################################################################
    'APIS_CORS_ALLOWED_ORIGINS_REGEX': get_env_var('APIS_CORS_ALLOWED_ORIGINS_REGEX', ''),
    ########################################################################################
    # sentry settings
    ########################################################################################
    'SENTRY_DSN': getenv('SENTRY_DSN'),
    ########################################################################################
    # logging settings
    ########################################################################################
    'LOGGING_CONFIG': {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(levelname)-6s %(asctime)s %(name)s: %(message)s'
            }

        },
        'handlers': {
            'console': {'level': LOG_LEVEL, 'class': 'logging.StreamHandler', 'formatter': 'default'},
        },
        'loggers': {'': {'level': LOG_LEVEL, 'handlers': ['console'], 'propagate': True}},
    },

}
logger = logging.getLogger('liminus')
