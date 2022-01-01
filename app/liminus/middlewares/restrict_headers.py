from os import write
from typing import Optional, Union

from starlette.datastructures import Headers, MutableHeaders
from starlette.requests import Request
from starlette.responses import Response

from liminus.base.backend import Backend, HeadersAllowedSettings, ReqSettings
from liminus.base.middleware import GkRequestMiddleware
from liminus.settings import logger


class RestrictHeadersMiddleware(GkRequestMiddleware):
    async def handle_request(self, req: Request, settings: ReqSettings, backend: Backend):
        # we have to filter the client-supplied request headers, not any added by our trusted middleware
        self._filter_headers(req, 'request', req.headers, req.state.headers, settings.allowed_request_headers)

    async def handle_response(self, res: Response, req: Request, settings: ReqSettings, backend: Backend):
        self._filter_headers(req, 'response', res.headers, res.headers, settings.allowed_response_headers)

    def _filter_headers(self, req: Request, type: str,
                        read_headers: Union[Headers, MutableHeaders],
                        write_headers: MutableHeaders,
                        headers_allowed: Optional[HeadersAllowedSettings]):
        if not headers_allowed:
            return

        dropped_allowlist_headers = set()
        # if we have an allowlist, it takes precedence
        allowlist = headers_allowed.allowlist
        if allowlist is not None and '*' not in allowlist:
            for header in read_headers.keys():
                if header not in allowlist and header in write_headers:
                    del write_headers[header]
                    dropped_allowlist_headers.add(header)

        if len(dropped_allowlist_headers):
            logger.debug(f'{req} dropping {type} headers not in allowlist: {dropped_allowlist_headers}')

        dropped_blocklist_headers = set()
        blocklist = headers_allowed.blocklist
        if blocklist is not None:
            for header in blocklist:
                if header in write_headers:
                    del write_headers[header]
                    dropped_blocklist_headers.add(header)

        if len(dropped_blocklist_headers):
            logger.debug(f'{req} dropping {type} headers in blocklist: {dropped_blocklist_headers}')