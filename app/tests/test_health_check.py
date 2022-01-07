from starlette.responses import Response


def test_health_check(client):
    response: Response = client.get('/health/ping')
    assert response.status_code == 200
    assert response.content == b'pong'
