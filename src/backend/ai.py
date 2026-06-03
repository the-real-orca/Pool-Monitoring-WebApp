import base64
import hashlib
import json
import logging
import os
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import openrouter
from openrouter.components import (
    ChatContentImage,
    ChatFormatJSONSchemaConfig,
    ChatJSONSchemaConfig,
    ChatSystemMessage,
    ChatUserMessage,
)
from openrouter.errors import UnauthorizedResponseError, RequestTimeoutResponseError
from pydantic import BaseModel, ValidationError

log = logging.getLogger(__name__)

AI_PROVIDER = os.getenv("AI_PROVIDER", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "google/gemini-3-flash-preview")
AI_TIMEOUT_SECONDS = int(os.getenv("AI_TIMEOUT_SECONDS", "30"))
AI_IMAGE_STORAGE_PATH = os.getenv("AI_IMAGE_STORAGE_PATH", "/data/ai")
AI_IMAGE_RETENTION_DAYS = int(os.getenv("AI_IMAGE_RETENTION_DAYS", "30"))
AI_MAX_IMAGE_BYTES = int(os.getenv("AI_MAX_IMAGE_BYTES", "10485760"))


class AIRefusalError(Exception):
    pass


class AISchemaError(Exception):
    pass


class AIAuthError(Exception):
    pass


class AITimeoutError(Exception):
    pass


class AIServiceError(Exception):
    pass


SYSTEM_PROMPT = """You are an expert at analyzing pool test strip images. Given an image of a test strip next to a color reference scale, extract the following values:

- pH (0.0-14.0, one decimal). Return -1 if the pH pad cannot be reliably matched.
- cl (chlorine, 0.0-10.0, one decimal). Return -1 if the Cl pad cannot be reliably matched.

When a pad is clearly visible and matches the reference scale, interpolate between the nearest reference colors to find the best intermediate value. Do NOT round to the nearest reference value – estimate the true midpoint.

If lighting, blur, orientation, or other image issues make a pad unreadable, set that value to -1 instead of guessing. It is better to return -1 than to fabricate a plausible-looking number.

Populate the "warnings" list ONLY for significant image-quality problems that make analysis unreliable, such as: severe blur, very poor lighting, reversed orientation, or obstructed pads. Do NOT warn about minor imperfections (e.g. slight glare, minor shadows, or standard lighting variation) – these are expected in real-world photos and do not meaningfully affect accuracy. Do NOT warn about the values themselves – extreme readings, interpolation, or values between reference points are expected and handled correctly by the numeric fields.

Return ONLY the structured analysis result, no additional text."""


class ImageAnalysisResult(BaseModel):
    ph: float
    cl: float
    refusal: str | None = None
    warnings: list[str] | None = None
    image: str | None = None


_ALIAS_MAP = {"pH": "ph", "PH": "ph", "Cl": "cl", "P_H": "ph", "chlorine": "cl"}


def _normalize_keys(d: dict) -> dict:
    return {_ALIAS_MAP.get(k, k): v for k, v in d.items()}


def _persist_image(image_bytes: bytes, result: ImageAnalysisResult) -> str | None:
    if not AI_IMAGE_STORAGE_PATH:
        return None
    try:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        date_dir = Path(AI_IMAGE_STORAGE_PATH) / date_str
        date_dir.mkdir(parents=True, exist_ok=True)
        img_hash = hashlib.sha256(image_bytes).hexdigest()[:12]
        ts = int(time.time())
        base = f"{ts}_{img_hash}"
        img_path = date_dir / f"{base}.jpg"
        json_path = date_dir / f"{base}.json"
        with open(img_path, "wb") as f:
            f.write(image_bytes)
        with open(json_path, "w") as f:
            json.dump(result.model_dump(mode="json"), f)
        return f"{date_str}/{base}.jpg"
    except Exception as e:
        log.warning("Failed to persist AI image: %s", e)
        return None


def _prune_old_images() -> None:
    if not AI_IMAGE_STORAGE_PATH:
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=AI_IMAGE_RETENTION_DAYS)
    try:
        date_dir = Path(AI_IMAGE_STORAGE_PATH)
        for subdir in date_dir.iterdir():
            if subdir.is_dir():
                try:
                    dir_date = datetime.strptime(subdir.name, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if dir_date < cutoff:
                        shutil.rmtree(subdir)
                except ValueError:
                    pass
    except Exception as e:
        log.warning("Failed to prune old AI images: %s", e)


class AIClient:
    def __init__(self) -> None:
        self._client: openrouter.OpenRouter | None = None
        self._started = False

    async def startup(self) -> None:
        if not AI_API_KEY:
            log.info("AI feature disabled: AI_API_KEY not set")
            return
        self._client = openrouter.OpenRouter(api_key=AI_API_KEY)
        self._started = True
        log.warning("AI client initialized (provider=%s, model=%s)", AI_PROVIDER, AI_MODEL)
        _prune_old_images()

    async def shutdown(self) -> None:
        self._client = None
        self._started = False

    def is_configured(self) -> bool:
        return self._started and self._client is not None


_client = AIClient()


def get_client() -> AIClient:
    return _client


async def analyze_pool_image(image_bytes: bytes, mime: str) -> ImageAnalysisResult:
    if not _client.is_configured():
        raise AIServiceError("AI client not configured")

    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:{mime};base64,{base64_image}"

    image_content = ChatContentImage(
        type="image_url",
        image_url={"url": data_uri, "detail": "high"},
    )

    system_msg = ChatSystemMessage(content=SYSTEM_PROMPT, role="system")
    user_msg = ChatUserMessage(content=[image_content], role="user")

    schema_config = ChatFormatJSONSchemaConfig(
        json_schema=ChatJSONSchemaConfig(
            name="ImageAnalysisResult",
            description="Pool test strip analysis result",
            schema_=ImageAnalysisResult.model_json_schema(),
        ),
        type="json_schema",
    )

    try:
        response = await _client._client.chat.send_async(
            messages=[system_msg, user_msg],
            model=AI_MODEL,
            response_format=schema_config,
            timeout_ms=AI_TIMEOUT_SECONDS * 1000,
        )
    except UnauthorizedResponseError as e:
        raise AIAuthError(f"AI authentication failed: {e}") from e
    except RequestTimeoutResponseError as e:
        raise AITimeoutError(f"AI request timed out after {AI_TIMEOUT_SECONDS}s") from e
    except Exception as e:
        raise AIServiceError(f"AI service error: {e}") from e

    if not response.choices:
        raise AIServiceError("Empty response from AI service")

    choice = response.choices[0]
    finish_reason = getattr(choice, "finish_reason", None)
    if finish_reason == "refuse":
        raise AIRefusalError("AI refused to analyze the image")

    content = choice.message.content
    refusal = choice.message.refusal

    if refusal:
        raise AIRefusalError(f"AI refused: {refusal}")

    if not content:
        raise AISchemaError("AI returned empty response")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise AISchemaError(f"AI returned unparseable response: {e}") from e

    try:
        result = ImageAnalysisResult.model_validate(_normalize_keys(parsed))
    except ValidationError as e:
        raise AISchemaError(f"AI returned invalid schema: {e}") from e

    if result.refusal:
        raise AIRefusalError(f"AI refused: {result.refusal}")

    image_path = _persist_image(image_bytes, result)
    if image_path:
        result.image = image_path
    return result