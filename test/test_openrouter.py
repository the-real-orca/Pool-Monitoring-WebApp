"""
OpenRouter connectivity test.

Usage (from src/backend/):
    AI_API_KEY=sk-or-... python ../../test_openrouter.py

Tests:
  1. Simple text-only chat completion
  2. Image analysis (same payload as the app sends)
"""

import asyncio
import base64
import json
import os
import sys
from pathlib import Path


# Load defaults from src/.env without external dependency.
# Environment variables take precedence.
_env_path = Path(__file__).resolve().parent.parent / "src" / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _key, _val = _line.split("=", 1)
        _key = _key.strip()
        _val = _val.strip().strip("\"'")
        if _key in ("AI_API_KEY", "AI_MODEL") and _key not in os.environ:
            os.environ[_key] = _val

import openrouter
from openrouter.components import (
    ChatContentImage,
    ChatContentText,
    ChatFormatJSONSchemaConfig,
    ChatJSONSchemaConfig,
    ChatSystemMessage,
    ChatUserMessage,
)
from openrouter.errors import UnauthorizedResponseError, RequestTimeoutResponseError
from pydantic import BaseModel


API_KEY = os.environ.get("AI_API_KEY", "")
MODEL = os.environ.get("AI_MODEL", "")
TIMEOUT_MS = int(os.environ.get("AI_TIMEOUT_SECONDS", "10")) * 1000
MAX_IMAGE_DIMENSION = int(os.environ.get("AI_MAX_IMAGE_DIMENSION", 2048))  # Set to 0 to disable resizing


class ImageAnalysisResult(BaseModel):
    ph: float
    cl: float
    time: int
    refusal: str | None = None
    warnings: list[str] | None = None


_ALIAS_MAP = {"pH": "ph", "PH": "ph", "Cl": "cl", "P_H": "ph", "chlorine": "cl"}


def _normalize_keys(d: dict) -> dict:
    return {_ALIAS_MAP.get(k, k): v for k, v in d.items()}


SYSTEM_PROMPT = """You are an expert at analyzing pool test strip images. Given an image of a test strip next to a color reference scale, extract the following values:

- pH (0.0-14.0, one decimal)
- cl (chlorine, 0.0-10.0, one decimal)
- time (Unix timestamp when the photo was taken, in seconds; if unknown use the current time)

When the color on the strip falls between two reference colors, interpolate to find the best intermediate value. Do NOT round to the nearest reference value – estimate the true midpoint.

Populate the "warnings" list ONLY for significant image-quality problems that make analysis unreliable, such as: severe blur, very poor lighting, reversed orientation, or obstructed pads. Do NOT warn about minor imperfections (e.g. slight glare, minor shadows, or standard lighting variation) – these are expected in real-world photos and do not meaningfully affect accuracy. Do NOT warn about the values themselves – extreme readings, interpolation, or values between reference points are expected and handled correctly by the numeric fields.

Return ONLY the structured analysis result, no additional text."""


def _resize_image(image_bytes: bytes, max_dim: int) -> bytes:
    from PIL import Image
    import io
    img = Image.open(io.BytesIO(image_bytes))
    if max(img.width, img.height) > max_dim:
        img.thumbnail((max_dim, max_dim))
        buf = io.BytesIO()
        fmt = img.format or "JPEG"
        img.save(buf, format=fmt)
        return buf.getvalue()
    return image_bytes


async def test_text_only():
    print(f"\n{'='*60}")
    print("TEST 1: Text-only chat completion")
    print(f"{'='*60}")
    print(f"Model: {MODEL}")
    print(f"Timeout: {TIMEOUT_MS}ms\n")

    client = openrouter.OpenRouter(api_key=API_KEY)

    response = await client.chat.send_async(
        messages=[
            {"role": "system", "content": "Antworte kurz auf Deutsch."},
            {"role": "user", "content": "Sag 'Hallo Welt – OpenRouter Verbindung steht'"},
        ],
        model=MODEL,
        timeout_ms=TIMEOUT_MS,
    )

    print(f"Status: {getattr(response, 'status_code', 'OK')}")
    print(f"Model used: {response.model}")
    print(f"Response: {response.choices[0].message.content}")
    if response.usage:
        print(f"   📊 Tokens: {response.usage.prompt_tokens}↑ + {response.usage.completion_tokens}↓ = {response.usage.total_tokens}")
    print("✅ TEST 1 PASSED\n")
    return response, response.id


async def test_image_analysis(image_path: str, hint: str | None = None):
    print(f"\n{'='*60}")
    print("TEST 2: Image analysis (JSON schema mode)")
    print(f"{'='*60}")
    print(f"Image: {image_path}")
    print(f"Model: {MODEL}\n")

    with open(image_path, "rb") as f:
        image_bytes = f.read()
    print(f"Original size: {len(image_bytes)} bytes")

    if MAX_IMAGE_DIMENSION:
        image_bytes = _resize_image(image_bytes, MAX_IMAGE_DIMENSION)
    print(f"Resized to max {MAX_IMAGE_DIMENSION}px: {len(image_bytes)} bytes")

    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{base64_image}"

    client = openrouter.OpenRouter(api_key=API_KEY)

    image_content = ChatContentImage(
        type="image_url",
        image_url={"url": data_uri, "detail": "high"},
    )
    content_parts: list = [image_content]
    if hint:
        content_parts.append(ChatContentText(type="text", text=hint))

    system_msg = ChatSystemMessage(content=SYSTEM_PROMPT, role="system")
    user_msg = ChatUserMessage(content=content_parts, role="user")

    schema_config = ChatFormatJSONSchemaConfig(
        json_schema=ChatJSONSchemaConfig(
            name="ImageAnalysisResult",
            description="Pool test strip analysis result",
            schema_=ImageAnalysisResult.model_json_schema(),
        ),
        type="json_schema",
    )

    try:
        response = await client.chat.send_async(
            messages=[system_msg, user_msg],
            model=MODEL,
            response_format=schema_config,
            timeout_ms=TIMEOUT_MS,
        )
    except UnauthorizedResponseError as e:
        print(f"❌ AUTH ERROR: {e}")
        print("   Check that your AI_API_KEY is valid and has credits.")
        return None
    except RequestTimeoutResponseError as e:
        print(f"❌ TIMEOUT: {e}")
        return None
    except Exception as e:
        print(f"❌ SERVICE ERROR: {e}")
        return None

    print(f"Status: {getattr(response, 'status_code', 'OK')}")
    print(f"Model used: {response.model}")
    if response.usage:
        print(f"   📊 Tokens: {response.usage.prompt_tokens}↑ + {response.usage.completion_tokens}↓ = {response.usage.total_tokens}")

    choice = response.choices[0]
    finish_reason = getattr(choice, "finish_reason", None)
    print(f"Finish reason: {finish_reason}")

    if finish_reason == "refuse":
        print("❌ REFUSAL: AI refused to analyze the image")
        return None

    content = choice.message.content
    refusal_text = getattr(choice.message, "refusal", None)

    if refusal_text:
        print(f"❌ REFUSAL in message: {refusal_text}")
        return None

    if not content:
        print("❌ SCHEMA ERROR: AI returned empty response")
        return None

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ SCHEMA ERROR: AI returned unparseable response: {e}")
        print(f"   Raw content: {content[:500]}")
        return None

    result = ImageAnalysisResult.model_validate(_normalize_keys(parsed))

    if result.refusal:
        print(f"❌ REFUSAL in result: {result.refusal}")
        return None

    print(f"\n🎯 Extracted values:")
    print(f"   pH:  {result.ph}")
    print(f"   cl:  {result.cl}")
    print(f"   time: {result.time} ({datetime.fromtimestamp(result.time)})")
    if result.warnings:
        for w in result.warnings:
            print(f"   ⚠️  {w}")
    print("✅ TEST 2 PASSED\n")
    return result, response.id


async def _lookup_cost(client: openrouter.OpenRouter, generation_id: str) -> float | None:
    delay = 1.0
    for attempt in range(12):
        if attempt:
            await asyncio.sleep(delay)
            delay = min(delay * 1.5, 5.0)
        try:
            gen = await client.generations.get_generation_async(id=generation_id)
            return gen.data.total_cost
        except openrouter.errors.NotFoundResponseError:
            continue
        except Exception as e:
            print(f"   [DEBUG] Cost lookup failed for {generation_id} with {type(e).__name__}: {e}")
            return None
    return None


async def main():
    if not API_KEY:
        print("❌ AI_API_KEY environment variable is not set")
        print("   Usage: AI_API_KEY=sk-or-... python test_openrouter.py")
        sys.exit(1)

    print(f"OpenRouter SDK version: {openrouter.__version__}")
    client = openrouter.OpenRouter(api_key=API_KEY)
    gen_ids: list[str] = []

    # Test 1: text completion
    result = await test_text_only()
    if isinstance(result, tuple):
        gen_ids.append(result[1])

    # Test 2: image analysis (if test_images available)
    image_paths = [
        "test_images/20260524_115452.jpg",
        "test_images/20260524_115506.jpg",
    ]

    for img_path in image_paths:
        if os.path.exists(img_path):
            result = await test_image_analysis(img_path, hint="Pool test strip, extract pH and chlorine")
            if isinstance(result, tuple):
                gen_ids.append(result[1])

    if not gen_ids:
        print("\n⚠️  No test images found at ../../test_images/")
        print("   Place images there or adjust the path and re-run.")

    # Sum up costs (parallel lookup so the slow generations have time to be indexed
    # while the fast ones return immediately)
    if gen_ids:
        print(f"\n{'='*60}")
        print("COST SUMMARY")
        print(f"{'='*60}")
        costs = await asyncio.gather(*[_lookup_cost(client, gid) for gid in gen_ids])
        known = [c for c in costs if c is not None]
        avg_cost = sum(known) / len(known) if known else 0.0
        total = 0.0
        for gid, cost in zip(gen_ids, costs):
            if cost is not None:
                print(f"   {gid}: ${cost:.6f}")
                total += cost
            elif avg_cost:
                print(f"   {gid}: ${avg_cost:.6f} (estimated)")
                total += avg_cost
            else:
                print(f"   {gid}: unknown (no data)")
        print(f"   {'─'*40}")
        print(f"   Total: ${total:.6f}")
        print()

    print("Done.")


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    from datetime import datetime
    asyncio.run(main())
