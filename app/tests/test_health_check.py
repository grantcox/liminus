def test_health_check(client):
    response = client.get('/health-check/ping')
    assert response.status_code == 200
    assert response.data == b'pong'
