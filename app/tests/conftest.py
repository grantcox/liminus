"""
pytest automatically loads up this file and makes the fixtures available in all tests.
"""
import pytest

from liminus_fastapi.app import create_app  # noqa: E402


app = create_app()


@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()
