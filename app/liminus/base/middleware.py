from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope, Send

from liminus.base import Backend, ReqSettings
from liminus.errors import ErrorResponse
from liminus.settings import logger


class BaseGkHTTPMiddleware(BaseHTTPMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive=receive)

        if not self.middleware_applies_to_scope(scope):
            logger.debug(f'{request} GK middleware {self.__class__.__name__} does not apply')
            await self.app(scope, receive, send)
            return

        logger.debug(f'{request} executing GK middleware {self.__class__.__name__}')
        await super(BaseGkHTTPMiddleware, self).__call__(scope, receive, send)

    def middleware_applies_to_scope(self, scope: Scope) -> bool:
        backend = scope.get('backend')
        if not backend:
            return False

        return self.__class__ in backend.middlewares

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        backend = request.scope['backend']
        settings = request.scope['backend_per_request_settings']

        # run the pre-request hook
        try:
            early_response = await self.handle_request(req=request, settings=settings, backend=backend)
            if early_response and isinstance(early_response, Response):
                return early_response

            # continue with the middleware chain, ending up with actually forwarding the request to a backing service
            response = await call_next(request)

            # run the post-response hook
            replacement_response = await self.handle_response(
                res=response,
                req=request,
                settings=settings,
                backend=backend,
            )
            if replacement_response and isinstance(replacement_response, Response):
                return replacement_response

            return response

        except ErrorResponse as error:
            return error.response

    async def handle_request(self, req: Request, settings: ReqSettings, backend: Backend):
        pass

    async def handle_response(self, res: Response, req: Request, settings: ReqSettings, backend: Backend):
        pass
