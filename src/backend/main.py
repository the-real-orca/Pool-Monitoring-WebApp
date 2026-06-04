import json
import logging
import os
import secrets as _secrets
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

API_TOKEN = os.getenv("API_TOKEN", "")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASS = os.getenv("MQTT_PASS", "")
POOL_LIST = json.loads(os.getenv("POOL_LIST", '[{"name": "Pool", "topic": "pool/manual"}]'))
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

# Live-Data configuration (Phase 20)
LIVE_TOPIC_BLE_TEMPLATE = os.getenv("LIVE_TOPIC_BLE_TEMPLATE", "home/{pool}/pool/ble-yc01")
LIVE_TOPIC_PUMP_TEMPLATE = os.getenv("LIVE_TOPIC_PUMP_TEMPLATE", "home/{pool}/pool/pump")
LIVE_AGGREGATION_WINDOW_MINUTES = int(os.getenv("LIVE_AGGREGATION_WINDOW_MINUTES", "60"))
LIVE_RETENTION_DAYS = int(os.getenv("LIVE_RETENTION_DAYS", "90"))
LIVE_DB_PATH = os.getenv("LIVE_DB_PATH", "/data/live/live.db")
LIVE_SAMPLE_RING_SIZE = int(os.getenv("LIVE_SAMPLE_RING_SIZE", "5"))
LIVE_STALE_AFTER_SECONDS = int(os.getenv("LIVE_STALE_AFTER_SECONDS", "600"))
LIVE_PUMP_FIELD_MAIN = os.getenv("LIVE_PUMP_FIELD_MAIN", "mainPump")
LIVE_PUMP_FIELD_SOLAR = os.getenv("LIVE_PUMP_FIELD_SOLAR", "solarPump")
LIVE_PUMP_FIELD_TIME = os.getenv("LIVE_PUMP_FIELD_TIME", "time")

VALID_METRICS = ("temp", "pH", "cl")
METRIC_UNITS = {"temp": "°C", "pH": "", "cl": "mg/l"}


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


APP_VERSION = "1.0.0"
_start_time = time.time()

# Module-level live state (initialised in lifespan)
_state: live_state.LiveState | None = None
_aggregator: aggregator.Aggregator | None = None


def _get_state() -> live_state.LiveState:
    assert _state is not None, "LiveState not initialised"
    return _state


def _topic_to_pool() -> dict[str, str]:
    return _topic_to_pool_map


_topic_to_pool_map: dict[str, str] = {}


def _handle_ble_message(topic: str, payload: dict) -> None:
    pool = _topic_to_pool_map.get(topic)
    if pool is None:
        return
    ts = int(payload.get("time") or time.time())
    state = _get_state()
    for metric in VALID_METRICS:
        if metric in payload and payload[metric] is not None:
            try:
                state.push_sample(pool, metric, float(payload[metric]), ts)
            except (TypeError, ValueError):
                pass


def _handle_pump_message(topic: str, payload: dict) -> None:
    pool = _topic_to_pool_map.get(topic)
    if pool is None:
        return
    ts = int(payload.get(LIVE_PUMP_FIELD_TIME) or time.time())
    state = _get_state()
    if LIVE_PUMP_FIELD_MAIN in payload:
        try:
            new_state = bool(payload[LIVE_PUMP_FIELD_MAIN])
        except (TypeError, ValueError):
            return
        if state.set_pump(pool, "main", new_state, ts) and db.is_configured():
            db.insert_pump_event(pool, "main", new_state, ts, int(time.time()))
    if LIVE_PUMP_FIELD_SOLAR in payload:
        try:
            new_state = bool(payload[LIVE_PUMP_FIELD_SOLAR])
        except (TypeError, ValueError):
            return
        if state.set_pump(pool, "solar", new_state, ts) and db.is_configured():
            db.insert_pump_event(pool, "solar", new_state, ts, int(time.time()))


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
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/"):
            client_ip = get_client_ip(request)
            now = datetime.now()
            cutoff = now - timedelta(seconds=self.seconds)

            self.requests[client_ip] = [
                t for t in self.requests[client_ip] if t > cutoff
            ]

            if len(self.requests[client_ip]) >= self.times:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"}
                )

            self.requests[client_ip].append(now)

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


class ChemicalType(str, Enum):
    CHLORINE = "chlorine"
    PH = "ph"
    FLOCCULANT = "flocculant"


class ChemicalUnit(str, Enum):
    ML = "ml"
    G = "g"
    TABS = "tabs"
    L = "l"


class ChemicalUpdate(BaseModel):
    time: int
    name: str = Field(min_length=1, max_length=50)
    chemicalType: ChemicalType
    amount: float | None = Field(default=None)
    unit: ChemicalUnit | None = None

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
    def validate_amount_unit_pair(self) -> "ChemicalUpdate":
        if (self.amount is None) != (self.unit is None):
            raise ValueError("amount and unit must be set together")
        return self


def build_mqtt_payload(m: Measurement) -> tuple[str, dict]:
    topic = next((pool["topic"] for pool in POOL_LIST if pool["name"] == m.name), "pool/manual")
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


def build_chemical_payload(c: ChemicalUpdate) -> tuple[str, dict]:
    base_topic = next((pool["topic"] for pool in POOL_LIST if pool["name"] == c.name), "pool/manual")
    topic = f"{base_topic}/chem"
    payload = {
        "time": c.time,
        "name": c.name,
        "chemicalType": c.chemicalType.value,
    }
    if c.amount is not None:
        payload["amount"] = c.amount
        payload["unit"] = c.unit.value
    return topic, payload


async def verify_token(authorization: str = Header(alias="Authorization")):
    expected = f"Bearer {API_TOKEN}"
    if not API_TOKEN or not _secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _state, _aggregator, _topic_to_pool_map

    db.init_db(LIVE_DB_PATH)
    _state = live_state.LiveState(
        ring_size=LIVE_SAMPLE_RING_SIZE,
        stale_after_seconds=LIVE_STALE_AFTER_SECONDS,
    )
    _aggregator = aggregator.Aggregator(
        _state,
        tick_seconds=60,
        retention_days=LIVE_RETENTION_DAYS,
    )

    # Build the topic→pool map from POOL_LIST using the configured templates
    _topic_to_pool_map = {}
    for pool in POOL_LIST:
        name = pool["name"]
        try:
            ble_topic = LIVE_TOPIC_BLE_TEMPLATE.format(pool=name)
            pump_topic = LIVE_TOPIC_PUMP_TEMPLATE.format(pool=name)
        except KeyError as e:
            log.error("LIVE topic template missing placeholder %s for pool %s", e, name)
            continue
        _topic_to_pool_map[ble_topic] = name
        _topic_to_pool_map[pump_topic] = name
        mqtt.subscribe(ble_topic, _handle_ble_message)
        mqtt.subscribe(pump_topic, _handle_pump_message)
        log.info("Subscribed to live topics for %s: %s, %s", name, ble_topic, pump_topic)

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

app.add_middleware(RateLimitMiddleware, times=20, seconds=60)


@app.get("/api/pools", dependencies=[Depends(verify_token)])
async def get_pools():
    return [{"name": pool["name"]} for pool in POOL_LIST]


@app.post("/api/measurements", status_code=201, dependencies=[Depends(verify_token)])
async def post_measurement(m: Measurement):
    topic, payload = build_mqtt_payload(m)
    if not mqtt.publish(topic, payload):
        raise HTTPException(status_code=503, detail="MQTT unavailable")
    return {"status": "success", "message": "Measurement published to MQTT"}


@app.post("/api/chem", status_code=201, dependencies=[Depends(verify_token)])
async def post_chemical_update(c: ChemicalUpdate):
    topic, payload = build_chemical_payload(c)
    if not mqtt.publish(topic, payload):
        raise HTTPException(status_code=503, detail="MQTT unavailable")
    return {"status": "success", "message": "Chemical update published to MQTT"}


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
):
    pool = _resolve_pool(pool)
    if metric not in VALID_METRICS:
        raise HTTPException(status_code=422, detail=f"Unknown metric: {metric}")
    if not db.is_configured():
        return {"pool": pool, "metric": metric, "unit": METRIC_UNITS[metric], "points": []}
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
