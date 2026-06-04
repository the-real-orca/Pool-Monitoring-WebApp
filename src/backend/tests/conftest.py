import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ai import ImageAnalysisResult

os.environ["API_TOKEN"] = "test-token"


@pytest.fixture
def tmp_db_path(tmp_path):
    """Return a path inside tmp_path for the live-data SQLite DB."""
    return str(tmp_path / "data.db")


@pytest.fixture(autouse=True)
def _reset_module_state():
    """L6: autouse fixture that resets module-global state before every
    test so individual tests don't leak database connections or MQTT
    subscriptions into each other."""
    import db
    import mqtt

    db.close()
    mqtt.clear_subscriptions()
    yield
    db.close()
    mqtt.clear_subscriptions()


@pytest.fixture
def client(tmp_path):
    """Yield a TestClient with the lifespan heavy-lifters patched:
    - ``db.init_db`` is redirected to a per-test tmp SQLite file
    - ``mqtt.connect``/``disconnect`` are no-ops
    - ``mqtt.publish``/``mqtt.is_connected`` always report success
    - the aggregator is started and stopped without scheduling a real task
    """
    if "main" in sys.modules:
        del sys.modules["main"]
    db_path = str(tmp_path / "data.db")

    # We need the un-patched init_db so we don't recurse into the patch.
    import db as _dbmod
    _orig_init_db = _dbmod.init_db

    def fake_init_db(path):
        _dbmod.close()
        return _orig_init_db(db_path)

    with patch("mqtt.publish", return_value=True), \
         patch("mqtt.is_connected", return_value=True), \
         patch("mqtt.connect"), \
         patch("mqtt.disconnect"), \
         patch("mqtt.subscribe") as mock_subscribe, \
         patch("aggregator.Aggregator.start", return_value=None), \
         patch("aggregator.Aggregator.stop", new_callable=AsyncMock), \
         patch("db.init_db", side_effect=fake_init_db):
        from main import app
        # Make the lifespan short: start the TestClient, yield, done.
        with TestClient(app) as tc:
            yield tc


@pytest.fixture
def mock_analyze_image():
    with patch("ai.analyze_pool_image", new_callable=AsyncMock) as mock:
        mock.return_value = ImageAnalysisResult(ph=7.2, cl=1.5)
        yield mock
