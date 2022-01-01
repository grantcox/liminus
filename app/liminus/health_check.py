import html
import json
import logging

import httpx
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse
from starlette.routing import Route

from liminus.backends import valid_backends
from liminus.settings import config, logger
from liminus.utils import loggable_string, loggable_url


SUMMARY_STATUS_PERFECT = 'perfect'
SUMMARY_STATUS_DEGRADED = 'degraded'
CHECK_STATUS_SUCCESS = 'success'
CHECK_STATUS_FAILURE = 'failure'


async def check_connectivity(request):
    checks = [
        {'name': 'sentry_http', 'status': await get_http_connection_status(config['SENTRY_DSN'])},
    ]
    # go through each backend and check their upstream dsns
    for be in valid_backends:
        if not be.listen.upstream_dsn:
            continue

        upstream_dsn_ping = be.listen.upstream_dsn.rstrip('/') + '/ping'
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


async def ping(request):
    return PlainTextResponse('pong')


async def sentry(request):
    logger.warning('Test logger.warning()')
    logger.error('Test logger.error()')
    raise Exception('Test exception')


def _render_html_results(results):
    heading_color = '#6F6' if results['summary'] == SUMMARY_STATUS_PERFECT else '#F66'
    return f'''
        <html>
            <head>
                <title>Liminus Health: {results['summary']}</title>
            </head>
            <body>
                <h2 style='background-color:{heading_color}'>Liminus Health Check: {results['summary']}</h2>
                <h4>Enabled backends: {config['ENABLED_BACKENDS']}</h4>
                <pre>{html.escape(json.dumps(results['checks'], indent=4))}</pre>
            </body>
        </html>
    '''


async def get_http_connection_status(url) -> str:
    if not url:
        return CHECK_STATUS_FAILURE

    try:
        response = httpx.get(url, timeout=2)

        if response.status_code == httpx.codes.OK:
            return CHECK_STATUS_SUCCESS

        logsafe_url = loggable_url(url)
        logsafe_response = loggable_string(response.content.decode('utf-8'), head=100, tail=50)
        return f'GET {logsafe_url} gave HTTP {response.status_code}: {logsafe_response}'

    except Exception as exc:
        logging.exception('HTTP GET request failed')

        return str(exc)


routes = [
    Route('/health', check_connectivity, methods=['GET']),
    Route('/health/ping', ping, methods=['GET']),
    Route('/health/sentry', sentry, methods=['GET']),
]
