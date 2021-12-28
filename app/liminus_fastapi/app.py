import logging

import sentry_sdk
from fastapi import FastAPI
from fastapi.requests import Request
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette_early_data import EarlyDataMiddleware

from liminus_fastapi import health_check
from liminus_fastapi.middlewares.add_ip_headers import AddIpHeadersMiddleware
from liminus_fastapi.middlewares.cors import GkCorsMiddleware
from liminus_fastapi.middlewares.gk_backend_selector import GatekeeperBackendSelectorMiddleware
from liminus_fastapi.middlewares.restrict_headers import RestrictHeadersMiddleware
from liminus_fastapi.proxy_request import proxy_request_to_backend
from liminus_fastapi.settings import config


def create_app():
    configure_logging()

    app = FastAPI(
        title='Gatekeeper FastAPI',
    )
    # we have to add all the possible GK middlewares
    # they will each exit early if they're not relevant to each request
    app.add_middleware(GkCorsMiddleware)
    app.add_middleware(AddIpHeadersMiddleware)
    app.add_middleware(RestrictHeadersMiddleware)

    # the "backend selector" middleware must be added after all other GK middlewares
    # so it actually executes first and sets up the request scope
    app.add_middleware(GatekeeperBackendSelectorMiddleware)

    # then add all middlewares that don't relate to specific backends
    app.add_middleware(GZipMiddleware)
    app.add_middleware(EarlyDataMiddleware, deny_all=True)
    app.add_middleware(SentryAsgiMiddleware)

    # the health check routes are handled directly
    app.include_router(health_check.router)

    # every other request that makes it through the middleware is proxied to the appropriate backend
    @app.route('/{full_path:path}')
    async def catch_all(request: Request):
        response = await proxy_request_to_backend(request)
        return response

    return app


def configure_logging():
    # python warnings should be logged
    logging.captureWarnings(True)
    logging.config.dictConfig(config['LOGGING_CONFIG'])

    sentry_sdk.init(dsn=config['SENTRY_DSN'])
