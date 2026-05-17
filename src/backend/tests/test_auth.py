

def test_correct_token_201(client):
    response = client.post(
        "/api/measurements",
        json={"time": 1755724982, "name": "Pool", "pH": 7.2, "cl": 1.0, "temp": 24.6},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 201


def test_wrong_token_401(client):
    response = client.post(
        "/api/measurements",
        json={"time": 1755724982, "name": "Pool", "pH": 7.2, "cl": 1.0, "temp": 24.6},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 401


def test_missing_header_422(client):
    response = client.post(
        "/api/measurements",
        json={"time": 1755724982, "name": "Pool", "pH": 7.2, "cl": 1.0, "temp": 24.6},
    )
    assert response.status_code == 422
