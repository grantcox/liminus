import html
import json
import logging
from http import HTTPStatus
from typing import Union
from urllib.parse import urljoin

from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from starlette.routing import Route

from liminus import settings
from liminus.backends import valid_backends
from liminus.proxy_request import http_request
from liminus.utils import loggable_string, loggable_url


SUMMARY_STATUS_PERFECT = 'perfect'
SUMMARY_STATUS_DEGRADED = 'degraded'
CHECK_STATUS_SUCCESS = 'success'
CHECK_STATUS_FAILURE = 'failure'

logger = logging.getLogger('health-check')


async def check_connectivity(request: Request) -> Response:
    request.app
    checks = [
        {'name': 'sentry_http', 'status': await get_http_connection_status(settings.SENTRY_DSN)},
    ]
    # go through each backend and check their upstream DSNs
    for be in valid_backends:
        if not be.listen.upstream_dsn:
            continue

        upstream_dsn_ping = urljoin(str(be.listen.upstream_dsn), '/ping')
        listen_path_label = be.listen.prefix or be.listen.path_regex

        checks.append(
            {
                'name': f'{be.name} {listen_path_label} upstream_dsn',
                'status': await get_http_connection_status(upstream_dsn_ping),
            }
        )

    passing_checks = [check['status'] == CHECK_STATUS_SUCCESS for check in checks]
    summary = SUMMARY_STATUS_PERFECT if all(passing_checks) else SUMMARY_STATUS_DEGRADED

    results = {'checks': checks, 'summary': summary}

    # return HTML for browser requests, return JSON for automated
    if 'text/html' in request.headers.get('accept', ''):
        html = _render_html_results(results)
        return HTMLResponse(html)

    return JSONResponse(results)


async def ping(request: Request) -> Response:
    return PlainTextResponse('pong')


async def sentry(request: Request):
    logger.warning('Test logger.warning()')
    logger.error('Test logger.error()')
    raise Exception('Test exception')


def _render_html_results(results: dict) -> str:
    heading_color = '#6F6' if results['summary'] == SUMMARY_STATUS_PERFECT else '#F66'
    return f'''
        <html>
            <head>
                <title>Liminus Health: {results['summary']}</title>
            </head>
            <body>
                <h2 style='background-color:{heading_color}'>Liminus Health Check: {results['summary']}</h2>
                <h4>Enabled backends: {settings.ENABLED_BACKENDS}</h4>
                <pre>{html.escape(json.dumps(results['checks'], indent=4))}</pre>
            </body>
        </html>
    '''


async def get_http_connection_status(url: Union[str, URL]) -> str:
    if not url:
        return CHECK_STATUS_FAILURE

    try:
        response = await http_request('GET', url, timeout=2)

        if response.status == HTTPStatus.OK:
            return CHECK_STATUS_SUCCESS

        response_body = await response.text()
        logsafe_url = loggable_url(url)
        logsafe_response = loggable_string(response_body, head=100, tail=50)
        return f'GET {logsafe_url} gave HTTP {response.status}: {logsafe_response}'

    except Exception as exc:
        logging.exception('HTTP GET request failed')

        return str(exc)


routes = [
    Route('/health', check_connectivity, methods=['GET']),
    Route('/health/ping', ping, methods=['GET']),
    Route('/health/sentry', sentry, methods=['GET']),
]
