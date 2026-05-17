import os
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

os.environ["API_TOKEN"] = "test-token"


@pytest.fixture
def client():
    if "main" in sys.modules:
        del sys.modules["main"]
    with patch("mqtt.publish", return_value=True), \
         patch("mqtt.is_connected", return_value=True):
        from main import app
        yield TestClient(app)
