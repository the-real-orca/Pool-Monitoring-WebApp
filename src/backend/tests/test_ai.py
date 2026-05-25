import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

import ai

TEST_IMAGE = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"x" * 100


def _make_send_mock(parsed, finish_reason="stop", refusal=None):
    choice = MagicMock()
    choice.finish_reason = finish_reason
    choice.message.content = json.dumps(parsed) if parsed else None
    choice.message.refusal = refusal
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.mark.asyncio
async def test_happy_path():
    mock_sdk = MagicMock()
    mock_sdk.chat.send_async = AsyncMock(return_value=_make_send_mock({"ph": 7.2, "cl": 1.5, "time": 1716518400}))

    with patch.object(ai._client, "is_configured", return_value=True), \
         patch.object(ai._client, "_client", mock_sdk):
        result = await ai.analyze_pool_image(TEST_IMAGE, "image/jpeg")

    assert isinstance(result, ai.ImageAnalysisResult)
    assert result.ph == 7.2
    assert result.cl == 1.5
    assert result.time == 1716518400
    assert result.refusal is None
    assert result.warnings is None


@pytest.mark.asyncio
async def test_ph_uppercase_p():
    mock_sdk = MagicMock()
    mock_sdk.chat.send_async = AsyncMock(return_value=_make_send_mock({"pH": 7.2, "cl": 1.5, "time": 1716518400}))

    with patch.object(ai._client, "is_configured", return_value=True), \
         patch.object(ai._client, "_client", mock_sdk):
        result = await ai.analyze_pool_image(TEST_IMAGE, "image/jpeg")

    assert result.ph == 7.2
    assert result.cl == 1.5


@pytest.mark.asyncio
async def test_warnings_field():
    mock_sdk = MagicMock()
    mock_sdk.chat.send_async = AsyncMock(return_value=_make_send_mock(
        {"ph": 7.0, "cl": 0.5, "time": 1716518400, "warnings": ["Reversed strip orientation"]}
    ))

    with patch.object(ai._client, "is_configured", return_value=True), \
         patch.object(ai._client, "_client", mock_sdk):
        result = await ai.analyze_pool_image(TEST_IMAGE, "image/jpeg")

    assert result.warnings == ["Reversed strip orientation"]


@pytest.mark.asyncio
async def test_refusal_finish_reason():
    mock_sdk = MagicMock()
    mock_sdk.chat.send_async = AsyncMock(return_value=_make_send_mock({"ph": 7.2, "cl": 1.5, "time": 1716518400}, finish_reason="refuse"))

    with patch.object(ai._client, "is_configured", return_value=True), \
         patch.object(ai._client, "_client", mock_sdk):
        with pytest.raises(ai.AIRefusalError, match="AI refused"):
            await ai.analyze_pool_image(TEST_IMAGE, "image/jpeg")


@pytest.mark.asyncio
async def test_refusal_in_result():
    mock_sdk = MagicMock()
    mock_sdk.chat.send_async = AsyncMock(return_value=_make_send_mock({"ph": 7.2, "cl": 1.5, "time": 1716518400, "refusal": "Cannot analyze image"}))

    with patch.object(ai._client, "is_configured", return_value=True), \
         patch.object(ai._client, "_client", mock_sdk):
        with pytest.raises(ai.AIRefusalError, match="AI refused"):
            await ai.analyze_pool_image(TEST_IMAGE, "image/jpeg")


@pytest.mark.asyncio
async def test_schema_error():
    mock_sdk = MagicMock()
    mock_sdk.chat.send_async = AsyncMock(return_value=_make_send_mock({"ph": "invalid", "cl": 1.5, "time": "not-an-int"}))

    with patch.object(ai._client, "is_configured", return_value=True), \
         patch.object(ai._client, "_client", mock_sdk):
        with pytest.raises(ai.AISchemaError):
            await ai.analyze_pool_image(TEST_IMAGE, "image/jpeg")


@pytest.mark.asyncio
async def test_auth_error():
    from openrouter.errors import UnauthorizedResponseError

    mock_sdk = MagicMock()
    mock_sdk.chat.send_async = AsyncMock(side_effect=UnauthorizedResponseError(MagicMock(), MagicMock()))

    with patch.object(ai._client, "is_configured", return_value=True), \
         patch.object(ai._client, "_client", mock_sdk):
        with pytest.raises(ai.AIAuthError):
            await ai.analyze_pool_image(TEST_IMAGE, "image/jpeg")


@pytest.mark.asyncio
async def test_timeout():
    from openrouter.errors import RequestTimeoutResponseError

    mock_sdk = MagicMock()
    mock_sdk.chat.send_async = AsyncMock(side_effect=RequestTimeoutResponseError(MagicMock(), MagicMock()))

    with patch.object(ai._client, "is_configured", return_value=True), \
         patch.object(ai._client, "_client", mock_sdk):
        with pytest.raises(ai.AITimeoutError):
            await ai.analyze_pool_image(TEST_IMAGE, "image/jpeg")


@pytest.mark.asyncio
async def test_persistence(tmp_path):
    storage = tmp_path / "ai_images"
    ai.AI_IMAGE_STORAGE_PATH = str(storage)

    mock_sdk = MagicMock()
    mock_sdk.chat.send_async = AsyncMock(return_value=_make_send_mock({"ph": 7.2, "cl": 1.5, "time": 1716518400}))

    with patch.object(ai._client, "is_configured", return_value=True), \
         patch.object(ai._client, "_client", mock_sdk):
        await ai.analyze_pool_image(TEST_IMAGE, "image/jpeg")

    files = list(storage.rglob("*"))
    jpg_files = [f for f in files if f.suffix == ".jpg"]
    json_files = [f for f in files if f.suffix == ".json"]
    assert len(jpg_files) == 1
    assert len(json_files) == 1
    assert jpg_files[0].read_bytes() == TEST_IMAGE


@pytest.mark.asyncio
async def test_hash_dedup(tmp_path):
    storage = tmp_path / "ai_images"
    ai.AI_IMAGE_STORAGE_PATH = str(storage)

    mock_sdk = MagicMock()
    mock_sdk.chat.send_async = AsyncMock(return_value=_make_send_mock({"ph": 7.2, "cl": 1.5, "time": 1716518400}))

    with patch.object(ai._client, "is_configured", return_value=True), \
         patch.object(ai._client, "_client", mock_sdk):
        await ai.analyze_pool_image(TEST_IMAGE, "image/jpeg")
        await ai.analyze_pool_image(TEST_IMAGE, "image/jpeg")

    files = list(storage.rglob("*"))
    jpg_files = [f for f in files if f.suffix == ".jpg"]
    assert len(jpg_files) == 1  # same hash + same timestamp → dedup (overwrite)


@pytest.mark.asyncio
async def test_not_configured():
    with patch.object(ai._client, "is_configured", return_value=False):
        with pytest.raises(ai.AIServiceError, match="AI client not configured"):
            await ai.analyze_pool_image(TEST_IMAGE, "image/jpeg")
