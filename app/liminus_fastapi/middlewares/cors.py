from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send


class GkCorsMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        settings = scope.get('backend_per_request_settings')
        if not settings or not settings.CORS or not settings.CORS.enable:
            await self.app(scope, receive, send)
            return

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

        # just run the Starlette CORS middleware
        await settings.CORS.cors_middleware_instance(scope, receive, send)
