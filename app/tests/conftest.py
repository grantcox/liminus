from unittest.mock import patch

import fakeredis.aioredis
import pytest
from starlette.config import environ
from starlette.testclient import TestClient


# provide explicit test environment variables
# make sure we overwrite anything that could be sensitive to run tests against
environ['TESTING'] = 'TRUE'
environ['READONLY_DATABASE_DSN'] = ''
environ['RECAPTCHA_VERIFY_URL'] = ''
environ['DONATION_SERVICE_JWT'] = ''

environ['BACKEND_DONATIONS_DSN'] = 'https://unit-tests/'
environ['BACKEND_WEB_ACT_DSN'] = 'https://unit-tests/'
environ['BACKEND_ADMIN_DSN'] = 'https://unit-tests/'
environ['BACKEND_PETITIONS_SERVICE_DSN'] = 'https://unit-tests/'
environ['BACKEND_STATS_SERVICE_DSN'] = 'https://unit-tests/'
environ['BACKEND_MEMBERS_SERVICE_DSN'] = 'https://unit-tests/'
environ['BACKEND_AUTH_SERVICE_DSN'] = 'https://unit-tests/'

environ['APIS_CORS_ALLOWED_ORIGINS_REGEX'] = '.*\\.unit-tests\\.dev'


@pytest.fixture()
def client():
    from liminus.app import create_app

    app = create_app()

    redis_pool = fakeredis.aioredis.FakeRedis()
    with patch('liminus.redis_client._redis_client', redis_pool):
        with TestClient(app) as test_client:
            yield test_client
