import json
import logging
import os
import re
import secrets as _secrets
import threading
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator
from starlette.middleware.base import BaseHTTPMiddleware

import ai
import aggregator
import db
import live_state
import mqtt

log = logging.getLogger(__name__)

_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

API_TOKEN = os.getenv("API_TOKEN", "")
API_RATE_LIMIT_REQUESTS = int(os.getenv("API_RATE_LIMIT_REQUESTS", "60"))
API_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("API_RATE_LIMIT_WINDOW_SECONDS", "60"))
# Read-only polling endpoints (history, pump-events, live state) must stay
# exempt — the chart reloads / backfills and the live view poll the API
# continuously and would otherwise trip the limiter. Write endpoints
# (measurements, event, analyze-image) keep the per-IP throttling.
RATE_LIMIT_EXEMPT_PREFIXES = (
    "/api/history",
    "/api/pump-events",
    "/api/live",
)
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASS = os.getenv("MQTT_PASS", "")
POOL_LIST = json.loads(os.getenv("POOL_LIST", '[{"name": "Pool", "topic": "pool"}]'))
POOL_NAMES = {pool["name"] for pool in POOL_LIST}
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

_mqtt_tls_env = os.getenv("MQTT_TLS", "")
if _mqtt_tls_env:
    MQTT_TLS = _mqtt_tls_env.lower() == "true"
else:
    MQTT_TLS = MQTT_PORT == 8883
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

AI_MAX_REQUESTS_PER_DAY = int(os.getenv("AI_MAX_REQUESTS_PER_DAY", "10"))
AI_MAX_IMAGE_BYTES = int(os.getenv("AI_MAX_IMAGE_BYTES", "10485760"))
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}
_ai_counter: dict[str, int] = {}
_ai_counter_date: str = ""

# Live-Data configuration (Phase 20+)
LIVE_AGGREGATION_WINDOW_MINUTES = int(os.getenv("LIVE_AGGREGATION_WINDOW_MINUTES", "60"))
LIVE_RETENTION_DAYS = int(os.getenv("LIVE_RETENTION_DAYS", "90"))
LIVE_DB_PATH = os.getenv("LIVE_DB_PATH", "/data/history/data.db")
LIVE_SAMPLE_RING_SIZE = int(os.getenv("LIVE_SAMPLE_RING_SIZE", "5"))
LIVE_STALE_AFTER_SECONDS = int(os.getenv("LIVE_STALE_AFTER_SECONDS", "600"))
# Minimum seconds between two persisted pump events for the same pool.
# State still updates in memory so the UI stays current, but we throttle
# DB writes to keep the pump_events table from being flooded by a
# compromised broker (M2).
LIVE_PUMP_MIN_EVENT_INTERVAL = int(os.getenv("LIVE_PUMP_MIN_EVENT_INTERVAL", "5"))
_pump_event_throttle: dict[str, int] = {}

VALID_METRICS = ("temp", "pH", "cl")
METRIC_UNITS = {"temp": "°C", "pH": "", "cl": "mg/l"}
PUMP_FIELDS = ("mainPump", "solarPump")
# Pool names must not contain MQTT wildcards (+, #, $) because they are
# substituted into subscribe topics. Anything outside this allow-list would
# let a misconfigured POOL_LIST match foreign pools.
_POOL_NAME_RE = re.compile(r"^[A-Za-z0-9 _\-]{1,32}$")
# Base topic must end with a normal segment (no wildcards) and must not be
# empty. It is the prefix of every MQTT topic the pool uses.
_BASE_TOPIC_RE = re.compile(r"^[A-Za-z0-9_\-]+(/[A-Za-z0-9_\-]+)*$")


def _is_valid_pool_name(name: str) -> bool:
    return bool(_POOL_NAME_RE.match(name))


def _is_valid_base_topic(topic: str) -> bool:
    return bool(topic) and bool(_BASE_TOPIC_RE.match(topic))


def _base_topic_for(pool: dict) -> str | None:
    """Return the configured base topic for a pool, or None if invalid."""
    topic = pool.get("topic")
    if not isinstance(topic, str) or not _is_valid_base_topic(topic):
        return None
    return topic


# Reserved topic suffixes under a pool's base topic.
# - ``/manual``  : measurement form publish target (back-end → MQTT)
# - ``/event``   : event form publish target (back-end → MQTT)
# - ``/pump``    : pump status publisher (ESP firmware → back-end)
# - ``/alert``   : any alert publisher (intermediate ``+`` is allowed for
#                  downstream services like mqtt2mail)
# - ``/+`` (wildcard) : catch-all subscription for back-end + mqtt2mail
RESERVED_SUFFIXES = ("manual", "event", "pump")


def ai_rate_check_and_increment() -> tuple[bool, int]:
    global _ai_counter, _ai_counter_date
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if today != _ai_counter_date:
        _ai_counter = {}
        _ai_counter_date = today
    remaining = AI_MAX_REQUESTS_PER_DAY - _ai_counter.get(today, 0)
    if remaining <= 0:
        return False, 0
    _ai_counter[today] = _ai_counter.get(today, 0) + 1
    return True, AI_MAX_REQUESTS_PER_DAY - _ai_counter[today]


APP_VERSION = "2.0"
_start_time = time.time()

# Module-level live state (initialised in lifespan)
_state: live_state.LiveState | None = None
_aggregator: aggregator.Aggregator | None = None


def _get_state() -> live_state.LiveState:
    assert _state is not None, "LiveState not initialised"
    return _state


def _base_to_pool() -> dict[str, str]:
    """Map base topic (no wildcards) → pool name. Populated in lifespan."""
    return _base_to_pool_map


# base topic → pool name; built once in lifespan from POOL_LIST.
_base_to_pool_map: dict[str, str] = {}


def _resolve_pool_for_topic(topic: str) -> str | None:
    """Find the pool name matching a concrete incoming topic.

    Walks the configured base topics and returns the pool whose base topic
    is a prefix of ``topic``. Wildcards are intentionally not expanded here:
    the MQTT client already filters, so the topic is always concrete.
    """
    for base, pool in _base_to_pool_map.items():
        if topic == base or topic.startswith(base + "/"):
            return pool
    return None


def _handle_pool_message(topic: str, payload: dict) -> None:
    """Single dispatcher for every subscribed ``<base>/+`` topic.

    The handler inspects the JSON payload rather than the topic suffix, so
    an ESP firmware can publish BLE values, pump state, or both on the same
    topic without a per-topic subscription. Anything that is neither a
    recognised metric nor a known pump field is logged at debug level and
    silently ignored (e.g. event payloads from the application backend).
    """
    pool = _resolve_pool_for_topic(topic)
    if pool is None or pool not in POOL_NAMES:
        return
    ts_raw = payload.get("time")
    ts = int(ts_raw) if ts_raw is not None else int(time.time())
    state = _get_state()

    metrics_seen = False
    for metric in VALID_METRICS:
        if metric in payload and payload[metric] is not None:
            metrics_seen = True
            try:
                v = float(payload[metric])
                state.push_sample(pool, metric, v, ts)
            except (TypeError, ValueError) as e:
                log.warning("MQTT payload on %s: bad %s value: %s", topic, metric, e)

    pumps_seen = False
    for pump_name, field in (("main", "mainPump"), ("solar", "solarPump")):
        if field not in payload:
            continue
        pumps_seen = True
        try:
            new_state = _strict_bool(payload[field], field)
        except ValueError as e:
            log.warning("MQTT payload on %s: %s", topic, e)
            continue
        if state.set_pump(pool, pump_name, new_state, ts) and db.is_configured():
            if _should_persist_pump_event(pool, int(time.time())):
                db.insert_pump_event(pool, pump_name, new_state, ts, int(time.time()))

    if not metrics_seen and not pumps_seen:
        log.debug("MQTT payload on %s ignored: no recognised fields", topic)


_TRUTHY = {"1", "true", "on", "yes"}
_FALSY = {"0", "false", "off", "no", ""}


def _strict_bool(value: Any, field: str) -> bool:
    """Strict bool coercion for MQTT pump payloads.

    Rejects truthy strings such as ``"false"`` (non-empty strings would
    otherwise coerce to ``True`` under plain ``bool()``) and silently drops
    unparseable values so a single bad publisher cannot poison state.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value in (0, 1):
            return bool(value)
        raise ValueError(f"{field}: numeric value must be 0 or 1, got {value}")
    if isinstance(value, str):
        s = value.strip().lower()
        if s in _TRUTHY:
            return True
        if s in _FALSY:
            return False
    raise ValueError(f"{field}: cannot coerce {value!r} to bool")


def _should_persist_pump_event(pool: str, now: int) -> bool:
    """M2 throttle: persist at most one pump event per pool per
    LIVE_PUMP_MIN_EVENT_INTERVAL seconds. State in ``LiveState`` is still
    updated on every publish; this only gates the DB write."""
    last = _pump_event_throttle.get(pool, 0)
    if now - last < LIVE_PUMP_MIN_EVENT_INTERVAL:
        return False
    _pump_event_throttle[pool] = now
    return True


if not FRONTEND_URL:
    log.warning("FRONTEND_URL not set – CORS will block cross-origin requests in production")


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, times: int = 20, seconds: int = 60):
        super().__init__(app)
        self.times = times
        self.seconds = seconds
        self.requests: dict[str, list[datetime]] = {}
        self._lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/") and not any(
            path.startswith(p) for p in RATE_LIMIT_EXEMPT_PREFIXES
        ):
            client_ip = get_client_ip(request)
            now = datetime.now()
            cutoff = now - timedelta(seconds=self.seconds)
            with self._lock:
                bucket = [t for t in self.requests.get(client_ip, []) if t > cutoff]
                if len(bucket) >= self.times:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many requests"}
                    )
                bucket.append(now)
                self.requests[client_ip] = bucket
                # Drop empty buckets to keep the dict small (I1 memory).
                if not self.requests[client_ip]:
                    self.requests.pop(client_ip, None)

        response = await call_next(request)
        return response


class Measurement(BaseModel):
    time: int
    name: str = Field(min_length=1, max_length=50)
    sensorType: str = "manual"
    pH: float = Field(ge=0.0, le=14.0)
    cl: float = Field(ge=0.0, le=10.0)
    temp: float = Field(ge=5.0, le=45.0)
    status: str | None = Field(default=None, max_length=100)
    aiPH: float | None = None
    aiCL: float | None = None
    aiImage: str | None = Field(default=None, max_length=200)
    aiCorrected: bool | None = None

    @field_validator("name")
    @classmethod
    def valid_pool_name(cls, v: str) -> str:
        if v not in POOL_NAMES:
            raise ValueError(f"Unknown pool name: {v}")
        return v

    @field_validator("pH", "cl", "temp")
    @classmethod
    def one_decimal(cls, v: float) -> float:
        return round(v, 1)


class EventType(str, Enum):
    CHLORINE = "chlorine"
    PH = "ph"
    FLOCCULANT = "flocculant"
    REFILL = "refill"
    BACKWASH = "backwash"
    WINTER = "winter"


class EventUnit(str, Enum):
    ML = "ml"
    G = "g"
    KG = "kg"
    TABS = "tabs"
    L = "l"
    MIN = "min"


class Event(BaseModel):
    time: int
    name: str = Field(min_length=1, max_length=50)
    eventType: EventType
    amount: float | None = Field(default=None)
    unit: EventUnit | None = None
    note: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def valid_pool_name(cls, v: str) -> str:
        if v not in POOL_NAMES:
            raise ValueError(f"Unknown pool name: {v}")
        return v

    @field_validator("amount")
    @classmethod
    def one_decimal(cls, v: float | None) -> float | None:
        if v is None:
            return None
        return round(v, 1)

    @model_validator(mode="after")
    def validate_amount_unit_pair(self) -> "Event":
        if (self.amount is None) != (self.unit is None):
            raise ValueError("amount and unit must be set together")
        return self


def build_mqtt_payload(m: Measurement) -> tuple[str, dict]:
    base = next((_base_topic_for(p) for p in POOL_LIST if p["name"] == m.name), None)
    topic = f"{base}/manual" if base else "pool/manual"
    payload = {
        "time": m.time,
        "name": m.name,
        "sensorType": m.sensorType,
        "temp": m.temp,
        "pH": m.pH,
        "cl": m.cl,
    }
    if m.status:
        payload["status"] = m.status
    if m.aiPH is not None:
        payload["aiPH"] = m.aiPH
    if m.aiCL is not None:
        payload["aiCL"] = m.aiCL
    if m.aiImage:
        payload["aiImage"] = m.aiImage
    if m.aiCorrected is not None:
        payload["aiCorrected"] = m.aiCorrected
    return topic, payload


def build_event_payload(e: Event) -> tuple[str, dict]:
    base = next((_base_topic_for(p) for p in POOL_LIST if p["name"] == e.name), None)
    topic = f"{base}/event" if base else "pool/event"
    payload = {
        "time": e.time,
        "name": e.name,
        "eventType": e.eventType.value,
    }
    if e.amount is not None:
        payload["amount"] = e.amount
        payload["unit"] = e.unit.value
    if e.note:
        payload["note"] = e.note
    return topic, payload


async def verify_token(authorization: str = Header(alias="Authorization")):
    expected = f"Bearer {API_TOKEN}"
    if not API_TOKEN or not _secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _state, _aggregator, _base_to_pool_map

    db.init_db(LIVE_DB_PATH)
    _state = live_state.LiveState(
        ring_size=LIVE_SAMPLE_RING_SIZE,
        stale_after_seconds=LIVE_STALE_AFTER_SECONDS,
    )
    _aggregator = aggregator.Aggregator(
        _state,
        window_minutes=LIVE_AGGREGATION_WINDOW_MINUTES,
        tick_seconds=30,
        retention_days=LIVE_RETENTION_DAYS,
    )

    # Build the base-topic→pool map from POOL_LIST and subscribe to a
    # single wildcard per pool (``<base>/+``). The handler inspects the
    # JSON payload to distinguish BLE samples from pump-state messages
    # (and silently ignore event payloads).
    _base_to_pool_map = {}
    for pool in POOL_LIST:
        name = pool["name"]
        base = _base_topic_for(pool)
        if not _is_valid_pool_name(name):
            log.error("Pool name %r rejected: only A-Z a-z 0-9 _ - space allowed, max 32 chars (would inject MQTT wildcards)", name)
            continue
        if base is None:
            log.error("Pool %r has invalid base topic %r, skipping subscription", name, pool.get("topic"))
            continue
        if "+" in base or "#" in base or "$" in base:
            log.error("Base topic %r for pool %s contains MQTT wildcard, skipping", base, name)
            continue
        if name in _base_to_pool_map.values():
            log.error("Duplicate pool name %r in POOL_LIST, ignoring", name)
            continue
        _base_to_pool_map[base] = name
        sub = f"{base}/+"
        mqtt.subscribe(sub, _handle_pool_message)
        log.info("Subscribed to live data for %s: %s", name, sub)

    mqtt.connect(MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS, MQTT_TLS)
    await ai.get_client().startup()
    _aggregator.start()
    try:
        yield
    finally:
        if _aggregator is not None:
            await _aggregator.stop()
        await ai.get_client().shutdown()
        mqtt.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL] if FRONTEND_URL else [],
    allow_methods=["POST", "GET"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(
    RateLimitMiddleware,
    times=API_RATE_LIMIT_REQUESTS,
    seconds=API_RATE_LIMIT_WINDOW_SECONDS,
)


@app.get("/api/pools", dependencies=[Depends(verify_token)])
async def get_pools():
    return [{"name": pool["name"]} for pool in POOL_LIST]


@app.post("/api/measurements", status_code=201, dependencies=[Depends(verify_token)])
async def post_measurement(m: Measurement):
    topic, payload = build_mqtt_payload(m)
    if not mqtt.publish(topic, payload):
        raise HTTPException(status_code=503, detail="MQTT unavailable")
    return {"status": "success", "message": "Measurement published to MQTT"}


@app.post("/api/event", status_code=201, dependencies=[Depends(verify_token)])
async def post_event(e: Event):
    topic, payload = build_event_payload(e)
    if not mqtt.publish(topic, payload):
        raise HTTPException(status_code=503, detail="MQTT unavailable")
    return {"status": "success", "message": "Event published to MQTT"}


@app.post("/api/analyze-image", dependencies=[Depends(verify_token)])
async def analyze_image(
    image: UploadFile = File(...),
):
    if image.content_type not in ALLOWED_IMAGE_MIMES:
        raise HTTPException(status_code=400, detail=f"Unsupported MIME type: {image.content_type}")

    image_bytes = await image.read()
    if len(image_bytes) > AI_MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail=f"Image too large: {len(image_bytes)} > {AI_MAX_IMAGE_BYTES} bytes")

    ok, remaining = ai_rate_check_and_increment()
    if not ok:
        raise HTTPException(status_code=429, detail="Daily image-analysis limit reached")

    try:
        result = await ai.analyze_pool_image(image_bytes, image.content_type)
    except ai.AIRefusalError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ai.AISchemaError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ai.AIAuthError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ai.AITimeoutError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ai.AIServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {
        "ph": result.ph,
        "cl": result.cl,
        "warnings": result.warnings,
        "image": result.image,
        "requestsRemainingToday": remaining,
    }


# --- Live Data endpoints (Phase 20) ---

def _resolve_pool(pool: str) -> str:
    if pool not in POOL_NAMES:
        raise HTTPException(status_code=422, detail=f"Unknown pool: {pool}")
    return pool


@app.get("/api/pools/live", dependencies=[Depends(verify_token)])
async def get_pools_live():
    state = _get_state()
    names = [pool["name"] for pool in POOL_LIST]
    return [{"name": n, "hasData": state.has_data(n)} for n in names]


@app.get("/api/live", dependencies=[Depends(verify_token)])
async def get_live(pool: str = Query(...)):
    pool = _resolve_pool(pool)
    return _get_state().get_snapshot(pool)


@app.get("/api/history", dependencies=[Depends(verify_token)])
async def get_history(
    pool: str = Query(...),
    metric: str = Query(...),
    days: int = Query(7, ge=1, le=30),
    before_ts: int | None = Query(None, ge=0),
):
    pool = _resolve_pool(pool)
    if metric not in VALID_METRICS:
        raise HTTPException(status_code=422, detail=f"Unknown metric: {metric}")
    if not db.is_configured():
        return {"pool": pool, "metric": metric, "unit": METRIC_UNITS[metric], "points": []}
    if before_ts is not None:
        end_ts = int(before_ts)
        start_ts = end_ts - days * 86400
        rows = db.get_aggregates_range(pool, metric, start_ts, end_ts)
    else:
        since_ts = int(time.time()) - days * 86400
        rows = db.get_aggregates(pool, metric, since_ts)
    return {
        "pool": pool,
        "metric": metric,
        "unit": METRIC_UNITS[metric],
        "points": [{"t": r["t"], "v": r["v"]} for r in rows],
    }


@app.get("/api/pump-events", dependencies=[Depends(verify_token)])
async def get_pump_events(
    pool: str = Query(...),
    days: int = Query(7, ge=1, le=30),
):
    pool = _resolve_pool(pool)
    if not db.is_configured():
        return {"pool": pool, "events": []}
    since_ts = int(time.time()) - days * 86400
    events = db.get_pump_events(pool, since_ts)
    return {
        "pool": pool,
        "events": [
            {
                "id": e["id"],
                "pump": e["pump"],
                "state": e["state"],
                "time": e["time"],
                "receivedAt": e["received_at"],
            }
            for e in events
        ],
    }


@app.get("/api/status")
async def get_status():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {
        "status": "healthy",
        "mqttConnected": mqtt.is_connected(),
        "uptime": int(time.time() - _start_time),
        "version": APP_VERSION,
        "aiConfigured": ai.get_client().is_configured(),
        "imageAnalysisRequestsToday": _ai_counter.get(today, 0),
        "liveDataConfigured": db.is_configured(),
    }
