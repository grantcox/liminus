import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope, Send

from liminus_fastapi.base import Backend, ReqSettings


logger = logging.getLogger(__name__)


class BaseGkHTTPMiddleware(BaseHTTPMiddleware):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not self.middleware_applies_to_scope(scope):
            logger.info(f'{self.__class__.__name__} does not apply to this request')
            await self.app(scope, receive, send)
            return

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
        early_response = await self.handle_request(req=request, settings=settings, backend=backend)
        if early_response:
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
        if replacement_response:
            return replacement_response

        return response

    async def handle_request(self, req: Request, settings: ReqSettings, backend: Backend):
        pass

    async def handle_response(self, res: Response, req: Request, settings: ReqSettings, backend: Backend):
        pass
