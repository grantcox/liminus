import re
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.datastructures import Headers, MutableHeaders

from liminus.settings import logger


class GkCorsMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive=receive)

        settings = scope.get('backend_per_request_settings')
        if not settings or not settings.CORS or not settings.CORS.enable:
            logger.debug(f'{request} GK middleware {self.__class__.__name__} does not apply')
            await self.app(scope, receive, send)
            return
        logger.debug(f'{request} executing GK middleware {self.__class__.__name__} with settings: {settings.CORS.dict()}')

        # compiled_allow_origin_regex = re.compile(settings.CORS.allow_origin_regex)
        # headers = Headers(scope=scope)
        # origin = headers.get("origin")

        # logger.info(f'origin: {origin}')
        # logger.info(f'compiled_allow_origin_regex: {compiled_allow_origin_regex}')
        # if origin is not None:
        #     logger.info(f'compiled_allow_origin_regex.fullmatch(origin): {compiled_allow_origin_regex.fullmatch(origin)}')

        if not getattr(settings.CORS, 'cors_middleware_instance', None):
            settings.CORS.cors_middleware_instance = CORSMiddleware(
                app=self.app,
                allow_origins=settings.CORS.allow_origins,
                allow_methods=settings.CORS.allow_methods,
                allow_headers=settings.CORS.allow_headers,
                allow_credentials=settings.CORS.allow_credentials,
                allow_origin_regex=settings.CORS.allow_origin_regex,
                expose_headers=settings.CORS.expose_headers,
                max_age=settings.CORS.max_age,
            )
            logger.info(f'just created cors middleware with settings: {settings.CORS.dict()}')

        # just run the Starlette CORS middleware
        await settings.CORS.cors_middleware_instance(scope, receive, send)
