import re
from unittest.mock import ANY

import pytest
from starlette.datastructures import MutableHeaders
from starlette.responses import Response

from liminus.base.backend import HeadersAllowedSettings
from liminus.middlewares.restrict_headers import RestrictHeadersMiddleware

from .mock_http_proxy import MockHttpProxy


base_headers = {
    'cookie': 'a=b',
    'host': 'domain.com',
    'referer': 'a.b.c/page',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'no-cors',
}


@pytest.fixture
def headers():
    return MutableHeaders(base_headers)


def test_allow_none(headers):
    filter = HeadersAllowedSettings(allowlist=set(), blocklist=set())

    RestrictHeadersMiddleware()._filter_headers(headers, headers, filter)
    assert dict(headers) == {}


def test_default_allows_all(headers):
    filter = HeadersAllowedSettings()
    expected_headers = base_headers

    RestrictHeadersMiddleware()._filter_headers(headers, headers, filter)
    assert dict(headers) == expected_headers


def test_allow_wildcard(headers):
    filter = HeadersAllowedSettings(allowlist={'*'}, blocklist=set())
    expected_headers = base_headers

    RestrictHeadersMiddleware()._filter_headers(headers, headers, filter)
    assert dict(headers) == expected_headers


def test_blocklist_case_insensitive(headers):
    filter = HeadersAllowedSettings(blocklist={'SEC-FETCH-SITE', 'Sec-Fetch-Mode'})
    expected_headers = {k: base_headers[k] for k in ['cookie', 'host', 'referer']}

    RestrictHeadersMiddleware()._filter_headers(headers, headers, filter)
    assert dict(headers) == expected_headers


def test_allowlist_case_insensitive(headers):
    filter = HeadersAllowedSettings(
        allowlist={'Host', 'COOKIE'},
    )
    expected_headers = {k: base_headers[k] for k in ['cookie', 'host']}

    RestrictHeadersMiddleware()._filter_headers(headers, headers, filter)
    assert dict(headers) == expected_headers


def test_blocklist_has_priority(headers):
    filter = HeadersAllowedSettings(allowlist={'Host', 'cookie'}, blocklist={'cookie'})
    expected_headers = {k: base_headers[k] for k in ['host']}

    results = RestrictHeadersMiddleware()._filter_headers(headers, headers, filter)
    assert dict(headers) == expected_headers, f'{results}'


def test_integration(client):
    # these should all make it to the backend
    expected_passthrough_request_headers = {
        'accept-encoding': 'utf8',
        'accept': 'zipfile',
        'accept-language': 'en',
        'cookie': 'a=b',
        'host': 'domain.com',
        'referer': 'a.b.c/page',
        'user-agent': 'chrome',
        'x-requested-with': 'ajax',
    }
    request_with_headers = {
        **expected_passthrough_request_headers,
        # these should all be stripped
        'authority': 'none',
        'sec-ch-ua-mobile': '?0',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-dest': 'image',
    }
    expected_backend_request_headers = {
        # these are added by our middlewares
        'proxied-by': 'Gatekeeper',
        'x-request-id': ANY,
        # these are from the original request
        **expected_passthrough_request_headers,
    }

    expected_passthrough_response_headers = {
        # these should all make it to the client
        'cache-control': 'max-age=31536000, public',
        'content-length': '606',
        'content-type': 'image/svg+xml',
    }
    backend_respond_with_headers = {
        **expected_passthrough_response_headers,
        # these should be stripped
        'member-authentication-jwt': '2j4il2423m',
        'staff-authentication-jwt': 'k432jfie',
        'x-powered-by': 'php',
        'server': 'nginx',
    }
    expected_final_response_headers = {
        # these are added by our middlewares
        'gk-public-csrf-token': ANY,
        'set-cookie': ANY,
        'x-request-id': ANY,
        # these are from the backend response
        **expected_passthrough_response_headers,
    }

    with MockHttpProxy() as m:
        # mock what the backend response will be
        m.add(re.compile('.*'), 'GET', headers=backend_respond_with_headers)

        # issue the incoming request
        final_response: Response = client.get('/act/cities.php', headers=request_with_headers)

        # assert the backend request was made with expected headers
        m.active_mock.assert_called_once()
        backend_request_args = m.active_mock.call_args.kwargs
        assert dict(backend_request_args['headers']) == expected_backend_request_headers

        # and that the final client response also had the expected headers
        assert dict(final_response.headers) == expected_final_response_headers
