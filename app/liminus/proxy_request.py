from json import JSONDecodeError
from typing import Dict

import aiohttp
import httpx
from starlette.datastructures import UploadFile, MutableHeaders
from starlette.requests import Request
from starlette.responses import Response

from liminus.base.backend import ListenPathSettings, ReqSettings
from liminus.settings import logger


httpx_client = httpx.AsyncClient()
aiohttp_session = None


async def proxy_request_to_backend_httpx(request: Request) -> Response:
    upstream_request_params = await construct_upstream_request_params(request)
    upstream_request_params['headers'] = upstream_request_params['headers'].raw
    logger.debug(f'{request} proxying to {upstream_request_params["url"]}')

    upstream_request = httpx_client.build_request(**upstream_request_params)
    upstream_response = await httpx_client.send(upstream_request, follow_redirects=False)
    logger.debug(
        f'{request} upstream responded with HTTP {upstream_response.status_code} '
        f'after {upstream_response.elapsed}'
    )

    # starlette.Response constructor only accepts a header dict, not multidict
    # but after creation it becomes a multidict, and we can call .append()
    response = Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
    )
    for k, v in upstream_response.headers.multi_items():
        response.headers.append(k, v)

    return response


async def get_aiohttp_session():
    global aiohttp_session
    if aiohttp_session is None:
        aiohttp_session = aiohttp.ClientSession()
    return aiohttp_session


async def proxy_request_to_backend_aiohttp(request: Request) -> Response:
    upstream_request_params = await construct_upstream_request_params(request)
    upstream_request_params['timeout'] = aiohttp.ClientTimeout(total=upstream_request_params['timeout'])

    logger.debug(f'{request} proxying to {upstream_request_params["url"]}')
    session = await get_aiohttp_session()

    upstream_response: aiohttp.ClientResponse = await session.request(allow_redirects=False, **upstream_request_params)
    logger.debug(
        f'{request} upstream responded with HTTP {upstream_response.status}'
    )

    # starlette.Response constructor only accepts a header dict, not multidict
    # but after creation it becomes a multidict, and we can call .append()
    response = Response(
        content=await upstream_response.content.read(),
        status_code=upstream_response.status,
    )
    for k, v in upstream_response.headers.items():
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
    request_headers: MutableHeaders = override.headers

    upstream_url = backend_listener.get_upstream_url(request_path)
    if request_query:
        upstream_url = upstream_url + '?' + request_query

    # these are passed as kwargs to httpx.request()
    upstream_request_params = {
        'method': getattr(override, 'method', request.method),
        'url': upstream_url,
        'headers': request_headers,
        'cookies': getattr(override, 'cookies', request.cookies),
        'timeout': backend_settings.timeout
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
