from unittest.mock import AsyncMock, patch

from ai import AIRefusalError, AITimeoutError


def test_post_measurement_201(client):
    response = client.post(
        "/api/measurements",
        json={
            "time": 1755724982,
            "name": "Pool",
            "pH": 7.2,
            "cl": 1.0,
            "temp": 24.6,
            "status": "Cloudy",
        },
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


def test_get_pools_200(client):
    response = client.get("/api/pools", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert {"name": "Pool"} in data


def test_get_pools_401(client):
    response = client.get("/api/pools", headers={"Authorization": "Bearer wrong-token"})
    assert response.status_code == 401


def test_get_status_200(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "mqttConnected" in data
    assert "uptime" in data
    assert "version" in data
    assert data["version"] == "1.0.0"


# --- /api/analyze-image tests ---

def test_analyze_image_200(client, mock_analyze_image):
    response = client.post(
        "/api/analyze-image",
        files={"image": ("test.jpg", b"fake-image-data", "image/jpeg")},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ph"] == 7.2
    assert data["cl"] == 1.5
    assert data["time"] == 1716518400
    assert "requestsRemainingToday" in data


def test_analyze_image_400_wrong_mime(client):
    response = client.post(
        "/api/analyze-image",
        files={"image": ("test.txt", b"fake", "text/plain")},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 400
    assert "Unsupported MIME type" in response.json()["detail"]


def test_analyze_image_400_oversized(client):
    big_data = b"x" * 20_000_000
    response = client.post(
        "/api/analyze-image",
        files={"image": ("test.jpg", big_data, "image/jpeg")},
        headers={"Authorization": "Bearer test-token"},
    )
    assert response.status_code == 400
    assert "Image too large" in response.json()["detail"]


def test_analyze_image_401_missing_token(client):
    response = client.post(
        "/api/analyze-image",
        files={"image": ("test.jpg", b"data", "image/jpeg")},
    )
    assert response.status_code == 422


def test_analyze_image_422_refusal(client):
    with patch("ai.analyze_pool_image", new_callable=AsyncMock) as mock:
        mock.side_effect = AIRefusalError("AI cannot process this image")
        response = client.post(
            "/api/analyze-image",
            files={"image": ("test.jpg", b"data", "image/jpeg")},
            headers={"Authorization": "Bearer test-token"},
        )
    assert response.status_code == 422
    assert "AI cannot process" in response.json()["detail"]


def test_analyze_image_503_timeout(client):
    with patch("ai.analyze_pool_image", new_callable=AsyncMock) as mock:
        mock.side_effect = AITimeoutError("AI request timed out")
        response = client.post(
            "/api/analyze-image",
            files={"image": ("test.jpg", b"data", "image/jpeg")},
            headers={"Authorization": "Bearer test-token"},
        )
    assert response.status_code == 503
    assert "timed out" in response.json()["detail"]


def test_analyze_image_429_rate_limit(client):
    with patch("ai.analyze_pool_image", new_callable=AsyncMock) as mock:
        mock.return_value = __import__("ai").ImageAnalysisResult(ph=7.2, cl=1.5, time=1716518400)
        for _ in range(10):
            resp = client.post(
                "/api/analyze-image",
                files={"image": ("test.jpg", b"data", "image/jpeg")},
                headers={"Authorization": "Bearer test-token"},
            )
            assert resp.status_code == 200
        resp = client.post(
            "/api/analyze-image",
            files={"image": ("test.jpg", b"data", "image/jpeg")},
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 429
    assert "Daily image-analysis limit reached" in resp.json()["detail"]


def test_analyze_image_midnight_rollover(client):
    from datetime import datetime, timezone
    import main

    mock_result = __import__("ai").ImageAnalysisResult(ph=7.2, cl=1.5, time=1716518400)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Day 1: fill up limit by manipulating counter directly
    main._ai_counter_date = today
    main._ai_counter = {today: 10}

    with patch("ai.analyze_pool_image", new_callable=AsyncMock, return_value=mock_result):
        resp = client.post(
            "/api/analyze-image",
            files={"image": ("test.jpg", b"data", "image/jpeg")},
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 429

    # Day 2: counter resets (_ai_counter_date differs from today)
    main._ai_counter_date = "2099-01-01"
    main._ai_counter = {"2099-01-01": 0}

    with patch("ai.analyze_pool_image", new_callable=AsyncMock, return_value=mock_result):
        resp = client.post(
            "/api/analyze-image",
            files={"image": ("test.jpg", b"data", "image/jpeg")},
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 200

