import logging
import os
import re
import secrets as _secrets
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field, field_validator

import mqtt


log = logging.getLogger(__name__)

API_TOKEN = os.getenv("API_TOKEN", "")
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASS = os.getenv("MQTT_PASS", "")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "pool/manual")
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

_mqtt_tls_env = os.getenv("MQTT_TLS", "")
if _mqtt_tls_env:
    MQTT_TLS = _mqtt_tls_env.lower() == "true"
else:
    MQTT_TLS = MQTT_PORT == 8883
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

APP_VERSION = "1.0.0"
_start_time = time.time()

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
    name: str = Field(default="Pool", min_length=1, max_length=50)
    sensorType: str = "manual"
    pH: float = Field(ge=0.0, le=14.0)
    cl: float = Field(ge=0.0, le=10.0)
    temp: float = Field(ge=5.0, le=45.0)

    @field_validator("name")
    @classmethod
    def name_alphanumeric(cls, v: str) -> str:
        if not re.fullmatch(r"[a-zA-Z0-9 ]+", v):
            raise ValueError("name must be alphanumeric")
        return v

    @field_validator("pH", "cl", "temp")
    @classmethod
    def one_decimal(cls, v: float) -> float:
        return round(v, 1)


def build_mqtt_payload(m: Measurement) -> dict:
    return {
        "time": m.time,
        "name": m.name,
        "sensorType": m.sensorType,
        "temp": m.temp,
        "pH": m.pH,
        "cl": m.cl,
    }


async def verify_token(authorization: str = Header(alias="Authorization")):
    expected = f"Bearer {API_TOKEN}"
    if not API_TOKEN or not _secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    mqtt.connect(MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS, MQTT_TLS)
    yield
    mqtt.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL] if FRONTEND_URL else [],
    allow_methods=["POST", "GET"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(RateLimitMiddleware, times=20, seconds=60)


@app.post("/api/measurements", status_code=201, dependencies=[Depends(verify_token)])
async def post_measurement(m: Measurement):
    payload = build_mqtt_payload(m)
    if not mqtt.publish(MQTT_TOPIC, payload):
        raise HTTPException(status_code=503, detail="MQTT unavailable")
    return {"status": "success", "message": "Measurement published to MQTT"}


@app.get("/api/status")
async def get_status():
    return {
        "status": "healthy",
        "mqttConnected": mqtt.is_connected(),
        "uptime": int(time.time() - _start_time),
        "version": APP_VERSION,
    }