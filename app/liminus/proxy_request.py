from json import JSONDecodeError
from typing import Dict

import httpx
from starlette.requests import Request
from starlette.responses import Response
from starlette.datastructures import FormData, UploadFile

from liminus.base import ListenPathSettings, ReqSettings
from liminus.settings import logger


async def proxy_request_to_backend(request: Request) -> Response:
    upstream_request_params = await construct_upstream_request_params(request)
    logger.debug(f'{request} proxying to {upstream_request_params["url"]}')

    async with httpx.AsyncClient() as client:
        upstream_request = client.build_request(**upstream_request_params)
        upstream_response = await client.send(upstream_request, follow_redirects=False)
        logger.debug(f'{request} upstream responded with HTTP {upstream_response.status_code} '
                     f'after {upstream_response.elapsed}')

        # starlette.Response constructor expect a dict for headers
        # but our httpx.Response has a multi-dict, eg supporting multiple items with the same key
        # so we need to manually append these headers
        response = Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
        )
        for k, v in upstream_response.headers.multi_items():
            response.headers.append(k, v)

    return response


async def construct_upstream_request_params(request: Request) -> Dict:
    # middleware can add settings to the request state, to override the request settings
    override = request.state
    backend_listener: ListenPathSettings = request.scope['backend_listener']
    backend_settings: ReqSettings = request.scope['backend_per_request_settings']

    # build the upstream URL
    request_path = getattr(override, 'path', request.url.path)
    request_query = getattr(override, 'query', request.url.query)

    upstream_url = backend_listener.get_upstream_url(request_path)
    if request_query:
        upstream_url = upstream_url + '?' + request_query

    # these are passed as kwargs to httpx.request()
    upstream_request_params = {
        'method': getattr(override, 'method', request.method),
        'url': upstream_url,
        'headers': override.headers.raw,
        'timeout': backend_settings.timeout,
        'cookies': getattr(override, 'cookies', request.cookies),
    }

    # if some middleware provided a new body, that takes precedence
    override_json = getattr(override, 'json', None)
    if override_json:
        upstream_request_params['json'] = override_json
    else:
        # proxy the original request data
        # rather than just blindly proxying the binary request upstream, we parse it here and re-encode
        # this will hopefully protect our backing services against any weird content attacks
        request_body = await request.body()
        if request_body:
            # there is a body, which we should parse and include in the upstream request
            try:
                json_data = await request.json()
                upstream_request_params['json'] = json_data
            except JSONDecodeError:
                # it's not json, try normal form data
                form_data = await request.form()

                # httpx data should be a dict
                httpx_data = {}
                for key, value in form_data.multi_items():
                    if isinstance(value, UploadFile):
                        # TODO: extract any files into upstream_request_params['files']
                        continue
                    httpx_data[key] = value
                    # TODO: support the case of having duplicate keys

                upstream_request_params['data'] = httpx_data

    return upstream_request_params
