from http import HTTPStatus
import http

from starlette.middleware.cors import CORSMiddleware
from starlette.datastructures import Headers
from starlette.responses import Response

from liminus.settings import logger


class CorsMiddleware(CORSMiddleware):

    def preflight_response(self, request_headers: Headers) -> Response:
        response = super().preflight_response(request_headers)
        if response.status_code != HTTPStatus.OK:
            logger.debug(f'request failing CORS with {response.body!r}')

        return response
