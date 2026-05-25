"""
OpenRouter benchmark: runs AI analysis on test images and scores against ground truth.

Usage:
    AI_API_KEY=sk-or-... python benchmark_openrouter.py

Reads ground_truth.csv from test_images/ next to this script.
"""

import asyncio
import base64
import csv
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Load defaults from src/.env
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
TIMEOUT_MS = int(os.environ.get("AI_TIMEOUT_SECONDS", "30")) * 1000
MAX_IMAGE_DIMENSION = int(os.environ.get("AI_MAX_IMAGE_DIMENSION", 2048))


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

When the color on the strip falls between two reference colors, interpolate to find the best intermediate value. Do NOT round to the nearest reference value – estimate the true midpoint.

Populate the "warnings" list ONLY for significant image-quality problems that make analysis unreliable, such as: severe blur, very poor lighting, reversed orientation, or obstructed pads. Do NOT warn about minor imperfections (e.g. slight glare, minor shadows, or standard lighting variation) – these are expected in real-world photos and do not meaningfully affect accuracy. Do NOT warn about the values themselves – extreme readings, interpolation, or values between reference points are expected and handled correctly by the numeric fields.

Return ONLY the structured analysis result, no additional text."""


@dataclass
class GroundTruth:
    image: str
    ph: float
    cl: float
    date: str
    warnings: list[str] = field(default_factory=list)


@dataclass
class BenchmarkResult:
    image: str
    ground_truth: GroundTruth
    predicted: ImageAnalysisResult | None
    ph_score: float
    cl_score: float
    total_score: float
    error: str | None = None


def _load_ground_truth(csv_path: str) -> list[GroundTruth]:
    rows: list[GroundTruth] = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = {k.strip(): (v or "").strip() for k, v in row.items()}
            warnings_list: list[str] = []
            raw = row.get("warnings", "")
            if raw:
                warnings_list = [w.strip() for w in raw.split(",") if w.strip()]
            rows.append(GroundTruth(
                image=row["image"],
                ph=float(row["pH"]),
                cl=float(row["Cl"]),
                date=row.get("date", ""),
                warnings=warnings_list,
            ))
    return rows


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


def _score_value(actual: float, expected: float, tolerance: float) -> float:
    diff = abs(actual - expected)
    return max(0.0, 100.0 * (1.0 - diff / tolerance))




async def _analyze_one(client: openrouter.OpenRouter, image_path: str, hint: str | None = None) -> tuple[ImageAnalysisResult | None, str | None]:
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    if MAX_IMAGE_DIMENSION:
        image_bytes = _resize_image(image_bytes, MAX_IMAGE_DIMENSION)

    base64_image = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{base64_image}"

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
    except (UnauthorizedResponseError, RequestTimeoutResponseError, Exception):
        return None, None

    choice = response.choices[0]
    if getattr(choice, "finish_reason", None) == "refuse":
        return None, None
    content = choice.message.content
    refusal_text = getattr(choice.message, "refusal", None)
    if refusal_text or not content:
        return None, None

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None, None
    result = ImageAnalysisResult.model_validate(_normalize_keys(parsed))
    if result.refusal:
        return None, None
    return result, response.id


async def _lookup_cost(client: openrouter.OpenRouter, generation_id: str) -> float | None:
    delay = 1.0
    for attempt in range(8):
        if attempt:
            await asyncio.sleep(delay)
            delay = min(delay * 1.5, 5.0)
        try:
            gen = await client.generations.get_generation_async(id=generation_id)
            return gen.data.total_cost
        except openrouter.errors.NotFoundResponseError:
            continue
        except Exception:
            return None
    return None


async def main():
    if not API_KEY:
        print("❌ AI_API_KEY environment variable is not set")
        sys.exit(1)

    script_dir = Path(__file__).resolve().parent
    csv_path = script_dir / "test_images" / "ground_truth.csv"
    if not csv_path.exists():
        print(f"❌ ground_truth.csv not found at {csv_path}")
        sys.exit(1)

    ground_truths = _load_ground_truth(str(csv_path))
    if not ground_truths:
        print("❌ No entries in ground_truth.csv")
        sys.exit(1)

    images_dir = script_dir / "test_images"
    client = openrouter.OpenRouter(api_key=API_KEY)

    print(f"OpenRouter SDK version: {openrouter.__version__}")
    print(f"Model: {MODEL}")
    print(f"Images: {len(ground_truths)}\n")

    results: list[BenchmarkResult] = []
    gen_ids: list[str] = []

    PH_TOLERANCE = 1.0
    CL_TOLERANCE = 1.0
    for gt in ground_truths:
        img_path = images_dir / gt.image
        if not img_path.exists():
            print(f"  {gt.image} not found, skipping")
            continue

        print(f"  Analyzing {gt.image} ...", end=" ", flush=True)
        result, gen_id = await _analyze_one(client, str(img_path))
        if gen_id:
            gen_ids.append(gen_id)
        if result:
            print("OK")
            ph_score = _score_value(result.ph, gt.ph, PH_TOLERANCE)
            cl_score = _score_value(result.cl, gt.cl, CL_TOLERANCE)
            total_score = (ph_score + cl_score) / 2
            results.append(BenchmarkResult(
                image=gt.image, ground_truth=gt, predicted=result,
                ph_score=ph_score, cl_score=cl_score, total_score=total_score,
            ))
        else:
            print("FAILED")
            results.append(BenchmarkResult(
                image=gt.image, ground_truth=gt, predicted=None,
                ph_score=0, cl_score=0, total_score=0,
                error="analysis failed",
            ))

    # ---- Print results ----
    print(f"\n{'='*60}")
    print("BENCHMARK RESULTS")
    print(f"{'='*60}\n")

    passed = 0

    for r in results:
        print(f"  {r.image}")
        print(f"    Ground truth:  pH={r.ground_truth.ph}, Cl={r.ground_truth.cl}  ({r.ground_truth.date})")
        if r.predicted:
            print(f"    Predicted:     pH={r.predicted.ph}, Cl={r.predicted.cl}")
            print(f"    Scores:        pH={r.ph_score:.0f}%  Cl={r.cl_score:.0f}%  =>  Total: {r.total_score:.0f}%")
            if r.total_score >= 50:
                passed += 1
        else:
            print(f"    Error: {r.error}")
        print()

    scores = [r.total_score for r in results]
    n = len(results)

    print(f"  {'─'*40}")
    print(f"  Scores:   avg={sum(scores)/n:.1f}%  min={min(scores):.0f}%  max={max(scores):.0f}%")
    print(f"  Passed (≥50%):      {passed}/{n}")
    print()

    # Cost summary (parallel lookup so the slow generations have time to be indexed
    # while the fast ones return immediately)
    if gen_ids:
        print(f"{'='*60}")
        print("COST SUMMARY")
        print(f"{'='*60}")
        costs = await asyncio.gather(*[_lookup_cost(client, gid) for gid in gen_ids])
        known = [c for c in costs if c is not None]
        avg_cost = sum(known) / len(known) if known else 0.0
        total_cost = 0.0
        for gid, cost in zip(gen_ids, costs):
            if cost is not None:
                print(f"  {gid}: ${cost:.6f}")
                total_cost += cost
            elif avg_cost:
                print(f"  {gid}: ${avg_cost:.6f} (estimated)")
                total_cost += avg_cost
            else:
                print(f"  {gid}: unknown (no data)")
        print(f"  {'─'*40}")
        print(f"  Total: ${total_cost:.6f}")
        print()

    print("Done.")


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    asyncio.run(main())
