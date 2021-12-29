from secrets import token_hex
from timeit import default_timer as timer
from starlette.middleware.base import BaseHTTPMiddleware

from liminus_fastapi.settings import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = timer()
        # the request id doesn't need to be globally unique, just for concurrent requests
        # and we don't want huge identifiers in logs
        request_id = token_hex(4)
        request.scope['request_id'] = request_id
        logger.debug(f'req={request_id} start proxying {request.url.path}')

        response = await call_next(request)

        end = timer()
        logger.debug(f'req={request_id} completed in {end - start} secs, responding with HTTP {response.status_code}')

        return response
