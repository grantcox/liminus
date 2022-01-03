from http import HTTPStatus
from typing import Callable, Dict, List, Tuple, Type

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

from liminus import bench
from liminus.backends import valid_backends
from liminus.base.backend import Backend, ListenPathSettings, ReqSettings
from liminus.base.middleware import GkRequestMiddleware
from liminus.errors import ErrorResponse
from liminus.settings import config, logger


class GatekeeperMiddlewareRunner(BaseHTTPMiddleware):
    _middleware_instances: Dict[str, GkRequestMiddleware] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            # go through all our backends, find the first that match this request path (no url params)
            backend, listener = self._get_matching_backend_and_listener(request)
            settings = self._get_req_settings(request, backend, listener)
            logger.debug(f'{request} found matching backend: {backend}')

            # add all relevant backend details to this request state
            self._augment_request_scope(request, backend, listener, settings)

            # run the pre-request hooks
            with bench.measure('handle_request'):
                for mw in backend.middleware_instances:
                    # logger.debug(f'{request} running {mw}.handle_request()')

                    with bench.measure(f'{mw.__class__.__name__}.handle_request'):
                        early_response = await mw.handle_request(request, settings, backend)
                        if early_response and isinstance(early_response, Response):
                            logger.debug(f'{request} {mw}.handle_request() returned early response {early_response}')
                            return early_response

            # continue with the middleware chain, ending up with actually forwarding the request to a backing service
            response = await call_next(request)

            # run the post-response hooks
            with bench.measure('handle_response'):
                for mw in backend.middleware_instances:
                    # logger.debug(f'{request} running {mw}.handle_response()')
                    with bench.measure(f'{mw.__class__.__name__}.handle_response'):
                        replacement_response = await mw.handle_response(
                            response,
                            request,
                            settings,
                            backend,
                        )
                        if replacement_response and isinstance(replacement_response, Response):
                            logger.debug(f'{request} {mw}.handle_response() returned replacement response {early_response}')
                            return replacement_response

            return response

        except ErrorResponse as error:
            logger.debug(f'{request} middleware processing raised error response {error.response}')
            return error.response

    @bench.measure_function
    def _get_matching_backend_and_listener(self, request: Request) -> Tuple[Backend, ListenPathSettings]:
        for be in valid_backends:
            if be.listen.matches_path(request.url.path):
                return (be, be.listen)

        # if there are no matching backends, return a 404
        msg = f'{request}: No backend found to proxy {request.url.path}' if config['DEBUG'] else ''
        response = PlainTextResponse(msg, HTTPStatus.NOT_FOUND)
        raise ErrorResponse(response)

    def _augment_request_scope(
        self, request: Request, backend: Backend, listener: ListenPathSettings, settings: ReqSettings
    ):
        request.scope['backend'] = backend
        request.scope['backend_listener'] = listener
        request.scope['backend_per_request_settings'] = settings
        request.state.headers = request.headers.mutablecopy()

        # and every request through GK gets a special header indicating that
        request.state.headers['Proxied-By'] = 'Gatekeeper'

    @bench.measure_function
    def _get_req_settings(self, request: Request, backend: Backend, listener: ListenPathSettings) -> ReqSettings:
        # the backend settings have a priority:
        #  1. exact path match
        #  2. regex path match
        #  3. listener
        for route in backend.routes:
            if route.route_exactly_matches(request.url.path, request.method):
                return route

        for route in backend.routes:
            if route.route_matches(request.url.path, request.method):
                return route

        # if this request does not match any routes, it means we do not proceed
        msg = (
            f'{request}: Backend {backend} has no route to proxy {request.method} {request.url.path}'
            if config['DEBUG']
            else ''
        )
        response = PlainTextResponse(msg, HTTPStatus.NOT_FOUND)
        raise ErrorResponse(response)
