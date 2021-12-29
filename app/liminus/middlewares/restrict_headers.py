from typing import Optional

from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.responses import Response

from liminus.base import Backend, BaseGkHTTPMiddleware, HeadersAllowedSettings, ReqSettings


class RestrictHeadersMiddleware(BaseGkHTTPMiddleware):
    async def handle_request(self, req: Request, settings: ReqSettings, backend: Backend):
        self._filter_headers(req.state.headers, settings.allowed_request_headers)

    async def handle_response(self, res: Response, req: Request, settings: ReqSettings, backend: Backend):
        self._filter_headers(res.headers, settings.allowed_response_headers)

    def _filter_headers(self, headers: MutableHeaders, headers_allowed: Optional[HeadersAllowedSettings]):
        if not headers_allowed:
            return

        # if we have an allowlist, it takes precedence
        allowlist = headers_allowed.allowlist
        if allowlist is not None and allowlist != ['*']:
            for header in headers.keys():
                if header not in allowlist:
                    del headers[header]

        blocklist = headers_allowed.blocklist
        if blocklist is not None:
            for header in blocklist:
                if header in headers:
                    del headers[header]
