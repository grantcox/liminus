import logging
from json import JSONDecodeError
from typing import Dict, Union
from urllib.parse import parse_qsl

from aiohttp import ClientResponse, ClientSession, ClientTimeout, FormData
from starlette.datastructures import URL, MultiDict, MutableHeaders, UploadFile
from starlette.requests import Request
from starlette.responses import Response

from liminus.base.backend import ListenPathSettings, ReqSettings
from liminus.constants import Headers


logger = logging.getLogger('gk-py-proxy')
aiohttp_session = None


async def get_aiohttp_session() -> ClientSession:
    global aiohttp_session
    if aiohttp_session is None:
        aiohttp_session = ClientSession()
    return aiohttp_session


async def http_request(method: str, url: Union[str, URL], timeout: int = 10, **kwargs) -> ClientResponse:
    return await aiohttp_request(method=method, url=url, timeout=ClientTimeout(total=timeout), **kwargs)


async def aiohttp_request(**kwargs) -> ClientResponse:
    session = await get_aiohttp_session()
    # we need to convert the URL to a string for aoihttp, but we do this after any printing
    # so that secrets will be exposed for as short as possible
    kwargs['url'] = str(kwargs['url'])
    # logger.debug(f'aiohttp_request: {kwargs}')
    return await session.request(**kwargs)


async def proxy_request_to_backend(request: Request) -> Response:
    backend_request_params = await construct_backend_request_params(request)
    backend_request_params['timeout'] = ClientTimeout(total=backend_request_params['timeout'])

    logger.debug(f'{request} proxying to backend {backend_request_params["url"]}')

    backend_response: ClientResponse = await aiohttp_request(allow_redirects=False, **backend_request_params)

    response_log = f'{request} backend responded with HTTP {backend_response.status}'
    if 300 <= backend_response.status <= 308:
        # it's a redirection
        response_log += f' to {backend_response.headers.get("location")}'
    logger.debug(response_log)

    # starlette.Response constructor only accepts a header dict, not multidict
    # but after creation it becomes a multidict, and we can call .append()
    response = Response(
        content=await backend_response.content.read(),
        status_code=backend_response.status,
    )
    for k, v in backend_response.headers.items():
        response.headers.append(k, v)

    return response


async def construct_backend_request_params(request: Request) -> Dict:
    # middleware can add settings to the request state, to override the request settings
    override = request.state
    backend_listener: ListenPathSettings = request.scope['backend_listener']
    backend_settings: ReqSettings = request.scope['backend_per_request_settings']

    # build the upstream URL
    request_path = getattr(override, 'path', request.url.path)
    request_query = getattr(override, 'query', request.url.query)
    upstream_url = backend_listener.get_upstream_url(request_path)
    if request_query:
        query_params = MultiDict(parse_qsl(request_query, keep_blank_values=True))
        upstream_url = upstream_url.include_query_params(**query_params)

    # we always use the mutable headers set in the middleware runner, so that
    # other middleware steps can delete / change request headers
    request_headers: MutableHeaders = override.headers

    # since we re-encode the data, remove any existing content-type
    # as multipart would also define a boundary, which will not be accurate
    del request_headers['content-type']

    # ensure we have our request id sent upstream
    request_headers[Headers.X_REQUEST_ID] = request.scope['request_id']

    # the listener may define custom headers
    for header_name, header_value in backend_listener.extra_headers:
        request_headers.append(header_name, header_value)

    # these are all passed as kwargs to httpx.request() / aiohttp.request()
    backend_request_params = {
        'method': getattr(override, 'method', request.method),
        'url': upstream_url,
        'headers': request_headers,
        'cookies': getattr(override, 'cookies', request.cookies),
        'timeout': backend_settings.timeout,
    }

    # if some middleware provided a new body, that takes precedence
    override_json = getattr(override, 'json', None)
    if override_json:
        backend_request_params['json'] = override_json
    else:
        # proxy the original request data
        # rather than just blindly proxying the binary request upstream, we parse it here and re-encode
        # this will hopefully protect our backing services against any weird content attacks
        request_body = await request.body()
        if request_body:
            # there is a body, which we should parse and include in the upstream request
            try:
                json_data = await request.json()
                backend_request_params['json'] = json_data
            except (JSONDecodeError, UnicodeDecodeError):
                # it's not json, try normal form data
                request_form = await request.form()

                backend_form = FormData()
                for field_name, field_data in request_form.multi_items():
                    if isinstance(field_data, UploadFile):
                        file_data = await field_data.read()
                        backend_form.add_field(
                            field_name, file_data, filename=field_data.filename, content_type=field_data.content_type
                        )
                    else:
                        backend_form.add_field(field_name, field_data)

                backend_request_params['data'] = backend_form

    return backend_request_params
