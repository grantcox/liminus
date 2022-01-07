from starlette.requests import Request
from starlette.responses import Response

from liminus.base.backend import Backend, ReqSettings


class GkRequestMiddleware:
    async def handle_request(self, req: Request, reqset: ReqSettings, backend: Backend):
        pass

    async def handle_response(self, res: Response, req: Request, reqset: ReqSettings, backend: Backend):
        pass

    def __str__(self) -> str:
        return self.__class__.__name__
