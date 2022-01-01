from timeit import default_timer as timer

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from liminus.settings import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = timer()
        logger.debug(f'{request} start proxying {request.method} {request.url.path}')

        response = await call_next(request)

        end = timer()
        logger.debug(f'{request} completed in {end - start} secs, responding with HTTP {response.status_code}')

        return response
