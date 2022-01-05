from secrets import token_hex
from timeit import default_timer as timer

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from liminus.constants import Headers
from liminus.settings import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # the request id doesn't need to be globally unique, just for concurrent requests
        # and we don't want huge identifiers in logs
        request_id = token_hex(4)
        request.scope['request_id'] = request_id

        start = timer()
        logger.debug(f'{request} start proxying {request.method} {request.url.path}')

        response: Response = await call_next(request)
        response.headers[Headers.X_REQUEST_ID] = request_id

        end = timer()
        logger.debug(f'{request} completed in {end - start} secs, responding with HTTP {response.status_code}')

        return response
