import logging

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.applications import Starlette
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette_early_data import EarlyDataMiddleware
from starlette.routing import Route
from starlette.middleware import Middleware

from liminus_fastapi import health_check
from liminus_fastapi.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus_fastapi.middlewares.cors import GkCorsMiddleware
from liminus_fastapi.middlewares.gk_backend_selector import GatekeeperBackendSelectorMiddleware
from liminus_fastapi.middlewares.request_logging import RequestLoggingMiddleware
from liminus_fastapi.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus_fastapi.proxy_request import proxy_request_to_backend
from liminus_fastapi.settings import config


def create_app():
    configure_logging()

    async def catch_all(request: Request):
        response = await proxy_request_to_backend(request)
        return response

    routes = [
        # the health check routes are handled directly
        *health_check.routes,
        # every other request that makes it through the middleware is proxied to the appropriate backend
        Route('/{rest_of_path:path}', catch_all),
    ]

    middlewares = [
        Middleware(RequestLoggingMiddleware),
        Middleware(SentryAsgiMiddleware),
        Middleware(GZipMiddleware),
        Middleware(EarlyDataMiddleware, deny_all=True),

        # the "backend selector" middleware must be added before all other GK middlewares
        # so it sets up the request scope
        Middleware(GatekeeperBackendSelectorMiddleware),

        # we have to add all the possible GK middlewares
        # they will each exit early if they're not relevant to each request
        Middleware(GkCorsMiddleware),
        Middleware(AddIpHeadersMiddleware),
        Middleware(RestrictHeadersMiddleware),
    ]

    app = Starlette(routes=routes, middleware=middlewares)
    return app


def configure_logging():
    # all existing loggers should use our root logging config
    # otherwise we get duplicate uvicorn.error logs
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # python warnings should be logged
    logging.captureWarnings(True)
    logging.config.dictConfig(config['LOGGING_CONFIG'])

    sentry_sdk.init(dsn=config['SENTRY_DSN'])
