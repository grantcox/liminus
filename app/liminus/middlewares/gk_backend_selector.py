from http import HTTPStatus
from typing import Any, Callable, List, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

from liminus.backends import valid_backends
from liminus.base import Backend, ListenPathSettings, ReqSettings
from liminus.settings import config, logger


class GatekeeperBackendSelectorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # go through all our backends, find the first that match this request path (no url params)
        matching_backend, listener = self._get_matching_backend_and_listener(request.url.path)
        logger.debug(f'{request} found matching backend: {matching_backend}')

        # if there are no matching backends, return a 404
        if not matching_backend or not listener:
            msg = (
                f'{request}: No backend found to proxy {request.url.path}'
                if config['DEBUG']
                else ''
            )
            return PlainTextResponse(msg, HTTPStatus.NOT_FOUND)

        # add all relevant backend details to this request state
        coalesced_path_settings = self._get_path_settings(request.url.path, matching_backend, listener)

        request.scope['backend'] = matching_backend
        request.scope['backend_listener'] = listener
        request.scope['backend_per_request_settings'] = coalesced_path_settings
        request.state.headers = request.headers.mutablecopy()

        response = await call_next(request)
        return response

    def _get_matching_backend_and_listener(
        self, request_path: str
    ) -> Tuple[Optional[Backend], Optional[ListenPathSettings]]:
        for be in valid_backends:
            for listen_path in be.listen:
                if listen_path.matches_path(request_path):
                    return be, listen_path
        return None, None

    def _get_path_settings(self, request_path: str, backend: Backend, listener: ListenPathSettings) -> ReqSettings:
        # the backend settings have a priority:
        #  1. exact path match
        #  2. regex path match
        #  3. listener
        #  4. backend
        setting_sources: List[Any] = []

        for route in backend.routes:
            if route.path_exactly_matches(request_path):
                setting_sources.insert(0, route)

            elif route.path_matches(request_path):
                setting_sources.append(route)

        setting_sources.append(listener)
        setting_sources.append(backend)

        # now coalese all these down
        combined_settings = ReqSettings()
        for setting_source in setting_sources:
            for prop in combined_settings.dict():
                if getattr(combined_settings, prop) is None:
                    setattr(combined_settings, prop, getattr(setting_source, prop))

        return combined_settings
