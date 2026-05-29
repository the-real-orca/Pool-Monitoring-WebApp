import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from ai import ImageAnalysisResult

os.environ["API_TOKEN"] = "test-token"


@pytest.fixture
def client():
    if "main" in sys.modules:
        del sys.modules["main"]
    with patch("mqtt.publish", return_value=True), \
         patch("mqtt.is_connected", return_value=True):
        from main import app
        yield TestClient(app)


@pytest.fixture
def mock_analyze_image():
    with patch("ai.analyze_pool_image", new_callable=AsyncMock) as mock:
        mock.return_value = ImageAnalysisResult(ph=7.2, cl=1.5)
        yield mock
