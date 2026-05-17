from unittest.mock import patch


def test_post_measurement_201(client):
    response = client.post(
        "/api/measurements",
        json={"time": 1755724982, "name": "Pool", "pH": 7.2, "cl": 1.0, "temp": 24.6},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "success"


def test_post_measurement_400_invalid_body(client):
    response = client.post(
        "/api/measurements",
        json={"time": "not-an-int", "name": "Pool"},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 422


def test_post_measurement_400_missing_fields(client):
    response = client.post(
        "/api/measurements",
        json={"time": 1755724982},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 422


def test_post_measurement_503_mqtt_down(client):
    with patch("mqtt.publish", return_value=False):
        response = client.post(
            "/api/measurements",
            json={"time": 1755724982, "name": "Pool", "pH": 7.2, "cl": 1.0, "temp": 24.6},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 503
        assert "MQTT unavailable" in response.json()["detail"]


def test_get_status_200(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "mqttConnected" in data
    assert "uptime" in data
    assert "version" in data
    assert data["version"] == "1.0.0"
