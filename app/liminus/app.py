import logging
import logging.config

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.routing import Route
from starlette_early_data import EarlyDataMiddleware

from liminus import health_check, settings
from liminus.background_tasks import complete_all_background_tasks
from liminus.middleware_runner import GatekeeperMiddlewareRunner
from liminus.middlewares.cors import CorsMiddleware
from liminus.middlewares.request_logging import RequestLoggingMiddleware
from liminus.proxy_request import proxy_request_to_backend


def create_app():
    configure_logging()
    monkey_patch_starlette_request_tostring()

    async def catch_all(request: Request):
        response = await proxy_request_to_backend(request)
        return response

    routes = [
        # the health check routes are handled directly
        *health_check.routes,
        # every other request that makes it through the middleware is proxied to the appropriate backend
        Route('/{rest_of_path:path}', catch_all, methods=['GET', 'POST']),
    ]

    middlewares = [
        Middleware(RequestLoggingMiddleware),
        Middleware(SentryAsgiMiddleware),
        Middleware(GZipMiddleware),
        Middleware(CorsMiddleware, **settings.CORS_MIDDLEWARE_ARGS),
        Middleware(EarlyDataMiddleware, deny_all=True),
        Middleware(GatekeeperMiddlewareRunner),
    ]

    async def on_app_shutdown():
        # finish all running background coroutines
        await complete_all_background_tasks(timeout=10)

    app = Starlette(routes=routes, middleware=middlewares, on_shutdown=[on_app_shutdown], debug=settings.DEBUG)
    return app


def configure_logging():
    # all existing loggers should use our root logging config
    # otherwise we get duplicate uvicorn.error logs
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # python warnings should be logged
    logging.captureWarnings(True)
    logging.config.dictConfig(settings.LOGGING_CONFIG)

    sentry_sdk.init(dsn=str(settings.SENTRY_DSN))


def monkey_patch_starlette_request_tostring():
    # monkey patch the Request.__str__ so it will print a request_id
    def monkey_request_str(self: Request) -> str:
        # the request id doesn't need to be globally unique, just for concurrent requests
        # and we don't want huge identifiers in logs
        if self.scope.get('request_id'):
            return f"req={self.scope['request_id']}"
        return f'req={self.url.path}'

    Request.__str__ = monkey_request_str
