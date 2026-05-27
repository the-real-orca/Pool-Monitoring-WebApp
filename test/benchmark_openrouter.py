"""
OpenRouter benchmark: runs AI analysis on test images and scores against ground truth.

Usage:
    AI_API_KEY=sk-or-... python benchmark_openrouter.py
    AI_BENCHMARK_LIMIT=5 AI_API_KEY=sk-or-... python benchmark_openrouter.py

Reads ground_truth.csv from test_images/ next to this script.
Set AI_BENCHMARK_LIMIT=n to only test the first n images.
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
PH_TOLERANCE = float(os.environ.get("AI_PH_TOLERANCE", "1.0"))
CL_TOLERANCE = float(os.environ.get("AI_CL_TOLERANCE", "1.0"))
# Cl tolerance in "stops" (log2 doublings). The Cl color scale is roughly exponential
# (0.5, 1, 3, 5, 10 ppm) so absolute error is misleading. 1 stop = 1 doubling/halving.
# E.g. expected=3.0, actual=6.0 → 1 stop → 0%; expected=3.0, actual=4.2 → 0.5 stops → 50%.
CL_TOLERANCE_STOPS = float(os.environ.get("AI_CL_TOLERANCE_STOPS", "1.0"))


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

- pH (0.0-14.0, one decimal). Return -1 if the pH pad cannot be reliably matched.
- cl (chlorine, 0.0-10.0, one decimal). Return -1 if the Cl pad cannot be reliably matched.

When a pad is clearly visible and matches the reference scale, interpolate between the nearest reference colors to find the best intermediate value. Do NOT round to the nearest reference value – estimate the true midpoint.

If lighting, blur, orientation, or other image issues make a pad unreadable, set that value to -1 instead of guessing. It is better to return -1 than to fabricate a plausible-looking number.

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
    warnings_mismatch: bool = False
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
    if actual < 0 and expected < 0:
        return 100.0
    if actual < 0 or expected < 0:
        return 0.0
    diff = abs(actual - expected)
    return max(0.0, 100.0 * (1.0 - diff / tolerance))


# Logarithmic scoring for Cl: measures deviation in doublings ("stops").
# Cl test-strip color scale is roughly exponential, so absolute error is misleading.
# 1 stop = factor-of-2 deviation (e.g. 3.0 vs 6.0 or 3.0 vs 1.5).
# When actual or expected is ≤ 0.5, falls back to linear scoring (no sensible log2
# from such small values; the reference scale starts at 0.5 ppm).
def _score_log_value(actual: float, expected: float, tolerance_stops: float) -> float:
    import math
    if actual < 0 and expected < 0:
        return 100.0
    if actual < 0 or expected < 0:
        return 0.0
    if expected <= 0.5 or actual <= 0.5:
        return _score_value(actual, expected, CL_TOLERANCE)
    stops = abs(math.log2(actual / expected))
    return max(0.0, 100.0 * (1.0 - stops / tolerance_stops))




def _get_image_size(image_bytes: bytes) -> tuple[int, int]:
    from PIL import Image
    import io
    img = Image.open(io.BytesIO(image_bytes))
    return img.width, img.height

async def _analyze_one(client: openrouter.OpenRouter, image_path: str, hint: str | None = None) -> tuple[ImageAnalysisResult | None, str | None, tuple[int, int, float]]:
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    if MAX_IMAGE_DIMENSION:
        image_bytes = _resize_image(image_bytes, MAX_IMAGE_DIMENSION)
    sent_w, sent_h = _get_image_size(image_bytes)
    sent_kb = len(image_bytes) / 1024
    sent_info = (sent_w, sent_h, sent_kb)

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
        return None, None, sent_info

    choice = response.choices[0]
    if getattr(choice, "finish_reason", None) == "refuse":
        return None, None, sent_info
    content = choice.message.content
    refusal_text = getattr(choice.message, "refusal", None)
    if refusal_text or not content:
        return None, None, sent_info

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None, None, sent_info
    result = ImageAnalysisResult.model_validate(_normalize_keys(parsed))
    if result.refusal:
        return None, None, sent_info
    return result, response.id, sent_info


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
            print(f"  [DEBUG] Cost lookup failed for {generation_id} with {type(e).__name__}: {e}")
            return None
    return None


async def main():
    limit_env = os.environ.get("AI_BENCHMARK_LIMIT", "0")
    limit = int(limit_env)

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

    if limit > 0:
        ground_truths = ground_truths[:limit]

    images_dir = script_dir / "test_images"
    client = openrouter.OpenRouter(api_key=API_KEY)

    print(f"OpenRouter SDK version: {openrouter.__version__}")
    print(f"Model: {MODEL}")
    print(f"Images: {len(ground_truths)}\n")

    results: list[BenchmarkResult] = []
    gen_ids: list[str] = []

    for gt in ground_truths:
        img_path = images_dir / gt.image
        if not img_path.exists():
            print(f"  {gt.image} not found, skipping")
            continue

        with open(img_path, "rb") as f:
            orig_bytes = f.read()
        orig_w, orig_h = _get_image_size(orig_bytes)
        result, gen_id, (sent_w, sent_h, sent_kb) = await _analyze_one(client, str(img_path))
        print(f"  Analyzing {gt.image} ({orig_w}×{orig_h} → {sent_w}×{sent_h} px, {sent_kb:.0f} KB) ...", end=" ", flush=True)
        if gen_id:
            gen_ids.append(gen_id)
        if result:
            print("OK")
            ph_score = _score_value(result.ph, gt.ph, PH_TOLERANCE)
            cl_score = _score_log_value(result.cl, gt.cl, CL_TOLERANCE_STOPS)
            total_score = (ph_score + cl_score) / 2
            gt_has_warnings = len(gt.warnings) > 0
            ai_has_warnings = bool(result.warnings)
            warnings_mismatch = gt_has_warnings != ai_has_warnings
            if warnings_mismatch:
                total_score *= 0.75
            results.append(BenchmarkResult(
                image=gt.image, ground_truth=gt, predicted=result,
                ph_score=ph_score, cl_score=cl_score, total_score=total_score,
                warnings_mismatch=warnings_mismatch,
            ))
        else:
            print("FAILED → -1")
            fallback = ImageAnalysisResult(ph=-1.0, cl=-1.0, time=0, warnings=["analysis failed or refused"])
            results.append(BenchmarkResult(
                image=gt.image, ground_truth=gt, predicted=fallback,
                ph_score=_score_value(-1.0, gt.ph, PH_TOLERANCE),
                cl_score=_score_log_value(-1.0, gt.cl, CL_TOLERANCE_STOPS),
                total_score=(_score_value(-1.0, gt.ph, PH_TOLERANCE) + _score_log_value(-1.0, gt.cl, CL_TOLERANCE_STOPS)) / 2,
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
            gt_w = ", ".join(r.ground_truth.warnings) if r.ground_truth.warnings else "–"
            ai_w = ", ".join(r.predicted.warnings) if r.predicted.warnings else "–"
            print(f"    Warnings:      GT: {gt_w}  |  AI: {ai_w}")
            warn = "  ⚠ mismatch (-25%)" if r.warnings_mismatch else ""
            print(f"    Scores:        pH={r.ph_score:.0f}%  Cl={r.cl_score:.0f}%  =>  Total: {r.total_score:.0f}%{warn}")
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
