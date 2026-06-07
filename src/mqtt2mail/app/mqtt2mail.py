#!/usr/bin/env python3
"""
MQTT -> pool report gateway.

- Subscribes to pool sensor MQTT topics.
- Aggregates only values relevant for the next report window in RAM.
- Prints a summary email draft at fixed REPORT_TIMES (or every REPORT_INTERVAL_MINUTES as fallback).
- Designed for Docker Compose deployment.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import smtplib
import socket
import ssl
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from statistics import mean
from typing import Any, Optional

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()


def env_str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        logging.warning("Invalid integer for %s=%r, using %s", name, value, default)
        return default


def env_float(name: str, default: Optional[float] = None) -> Optional[float]:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        logging.warning("Invalid float for %s=%r, using %s", name, value, default)
        return default


def normalize_topic(topic: str) -> str:
    value = topic.strip()
    if not value:
        return ""
    if value != "/":
        value = value.rstrip("/")
    return value


def parse_topic_csv(value: str) -> list[str]:
    topics: list[str] = []
    for item in value.split(","):
        topic = normalize_topic(item)
        if topic:
            topics.append(topic)
    return topics


def parse_pool_topics() -> list[str]:
    raw = env_str("POOL_LIST")
    if not raw:
        return []

    try:
        pools = json.loads(raw)
    except json.JSONDecodeError:
        logging.warning("Invalid JSON in POOL_LIST, ignoring")
        return []

    if not isinstance(pools, list):
        logging.warning("POOL_LIST is not a JSON array, ignoring")
        return []

    topics: list[str] = []
    for pool in pools:
        if isinstance(pool, dict):
            topic = normalize_topic(str(pool.get("topic") or ""))
            if topic:
                topics.append(topic)
    return topics


def unique_topics(topics: list[str]) -> list[str]:
    unique: list[str] = []
    for topic in topics:
        if topic and topic not in unique:
            unique.append(topic)
    return unique


def resolve_topics() -> tuple[list[str], list[str], list[str]]:
    """Derive MQTT topic subscriptions purely from ``POOL_LIST``.

    The ``topic`` of every pool entry is the **base** topic — the prefix of
    every MQTT topic that pool uses. mqtt2mail subscribes once per pool
    using the wildcard ``<base>/+`` so it sees both measurement and pump
    messages; the ``on_message`` handler then inspects the JSON payload to
    classify them. Alert topics are ``<base>/+/alert`` so the same
    downstream consumer can subscribe to both. Availability topics are not
    used in this project.
    """
    data_topics: list[str] = []
    alert_topics: list[str] = []
    for base in parse_pool_topics():
        data_topics.append(f"{base}/+")
        alert_topics.append(f"{base}/+/alert")

    return (
        unique_topics(data_topics),
        unique_topics(alert_topics),
        [],
    )


def topic_matches(pattern: str, topic: str) -> bool:
    p_parts = pattern.split("/")
    t_parts = topic.split("/")
    p_len = len(p_parts)
    t_len = len(t_parts)
    i = 0
    while i < p_len:
        p = p_parts[i]
        if p == "#":
            return True
        if p == "+":
            if i >= t_len:
                return False
            i += 1
            continue
        if i >= t_len or p != t_parts[i]:
            return False
        i += 1
    return i == t_len


def parse_report_times(raw: str) -> list[int]:
    times: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            h, m = part.split(":", 1)
            try:
                times.append(int(h) * 60 + int(m))
            except ValueError:
                logging.warning("Invalid report time %r, ignoring", part)
    return sorted(times)


def next_report_delay(times: list[int]) -> float:
    now = now_local()
    current_sec = now.hour * 3600 + now.minute * 60 + now.second
    for t in times:
        t_sec = t * 60
        if t_sec > current_sec:
            return t_sec - current_sec
    return 24 * 3600 - current_sec + times[0] * 60


def to_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_number(value: Optional[float], decimals: int = 1) -> str:
    if value is None:
        return "n/a"
    text = f"{value:.{decimals}f}"
    return text.replace(".", ",")


def now_local() -> datetime:
    return datetime.now().astimezone()


def get_server_ip() -> str:
    """Return the primary outbound IPv4 of this host. Uses a UDP "connect"
    to a public address (no packets sent) which is the most reliable
    way to discover the interface IP from inside a container. Falls back
    to hostname resolution when no route is available."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "n/a"
    finally:
        sock.close()


def format_dt(dt: Optional[datetime]) -> str:
    if not dt:
        return "n/a"
    return dt.strftime("%d.%m.%Y %H:%M")


def format_subject_date(dt: Optional[datetime]) -> str:
    """Short German date label for email subject, e.g. ``So. 7.6. @ 10:00``."""
    if not dt:
        return "n/a"
    weekday_short = ["Mo.", "Di.", "Mi.", "Do.", "Fr.", "Sa.", "So."][dt.weekday()]
    return f"{weekday_short} {dt.day}.{dt.month}. @ {dt.hour:02d}:{dt.minute:02d}"


def datetime_from_payload(payload: dict[str, Any]) -> datetime:
    raw = payload.get("time")
    if isinstance(raw, (int, float)):
        try:
            return datetime.fromtimestamp(raw).astimezone()
        except (OSError, ValueError):
            pass
    return now_local()


@dataclass
class MetricConfig:
    key: str
    label: str
    unit: str = ""
    decimals: int = 1
    divisor: float = 1.0


@dataclass
class MetricState:
    config: MetricConfig
    last_value: Optional[float] = None
    last_time: Optional[datetime] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    last_values: deque[float] = field(default_factory=lambda: deque(maxlen=5))

    def add(self, raw_value: Any, timestamp: datetime) -> None:
        value = to_float(raw_value)
        if value is None:
            return
        value = value / self.config.divisor
        self.last_value = value
        self.last_time = timestamp
        self.last_values.append(value)
        self.min_value = value if self.min_value is None else min(self.min_value, value)
        self.max_value = value if self.max_value is None else max(self.max_value, value)

    @property
    def avg_last_values(self) -> Optional[float]:
        if not self.last_values:
            return None
        return mean(self.last_values)

    def expected_range_text(self, low: Optional[float], high: Optional[float]) -> str:
        if low is None and high is None:
            return "n/a"
        low_txt = "-∞" if low is None else format_number(low, self.config.decimals)
        high_txt = "+∞" if high is None else format_number(high, self.config.decimals)
        return f"{low_txt} - {high_txt} {self.config.unit}".strip()

    def value_text(self, value: Optional[float]) -> str:
        text = format_number(value, self.config.decimals)
        return f"{text} {self.config.unit}".strip()


@dataclass
class AlertEvent:
    is_alert: bool
    kind: str
    value: Optional[float]
    min_value: Optional[float]
    max_value: Optional[float]
    text: str
    timestamp: datetime


class PoolAggregator:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.metric_configs = self._build_metric_configs()
        self.metrics = {key: MetricState(config) for key, config in self.metric_configs.items()}
        self.alerts: list[AlertEvent] = []
        self.availability: Optional[str] = None
        self.availability_time: Optional[datetime] = None
        self.message_count = 0
        self.invalid_message_count = 0
        self.window_start = now_local()
        self.last_sensor_name: Optional[str] = None

    def _build_metric_configs(self) -> dict[str, MetricConfig]:
        bat_divisor = 1000.0 if env_str("BAT_VALUE_UNIT", "mv").lower() == "mv" else 1.0
        bat_unit = env_str("BAT_DISPLAY_UNIT", "V")
        return {
            "temp": MetricConfig("temp", "Wassertemperatur", "°C", 1),
            "pH": MetricConfig("pH", "pH", "", 2),
            "cl": MetricConfig("cl", "Cl", "mg/l", 2),
            "bat": MetricConfig("bat", "Battery Spannung", bat_unit, 2, bat_divisor),
            "orp": MetricConfig("orp", "ORP", "mV", 0),
            "ec": MetricConfig("ec", "EC", "µS/cm", 0),
            "salt": MetricConfig("salt", "Salz", "g/l", 2),
            "tds": MetricConfig("tds", "TDS", "ppm", 0),
            "bleRSSI": MetricConfig("bleRSSI", "BLE RSSI", "dBm", 0),
            "wifiRSSI": MetricConfig("wifiRSSI", "WiFi RSSI", "dBm", 0),
        }

    def add_data(self, payload: dict[str, Any]) -> None:
        timestamp = datetime_from_payload(payload)
        with self.lock:
            self.message_count += 1
            name = payload.get("name")
            if isinstance(name, str) and name:
                self.last_sensor_name = name
            for key, state in self.metrics.items():
                if key in payload:
                    state.add(payload.get(key), timestamp)

    def add_alert(self, payload: dict[str, Any]) -> None:
        timestamp = datetime_from_payload(payload)
        kind = str(payload.get("type") or "unknown")
        raw_value = to_float(payload.get("value"))
        raw_min = to_float(payload.get("min"))
        raw_max = to_float(payload.get("max"))

        # Normalize battery values if alert payload uses mV.
        if kind == "bat" and env_str("BAT_VALUE_UNIT", "mv").lower() == "mv":
            raw_value = raw_value / 1000 if raw_value is not None else None
            raw_min = raw_min / 1000 if raw_min is not None else None
            raw_max = raw_max / 1000 if raw_max is not None else None

        with self.lock:
            self.message_count += 1
            self.alerts.append(
                AlertEvent(
                    is_alert=bool(payload.get("alert", False)),
                    kind=kind,
                    value=raw_value,
                    min_value=raw_min,
                    max_value=raw_max,
                    text=str(payload.get("text") or ""),
                    timestamp=timestamp,
                )
            )

    def add_availability(self, payload: str) -> None:
        with self.lock:
            self.message_count += 1
            self.availability = payload.strip()
            self.availability_time = now_local()

    def mark_invalid(self) -> None:
        with self.lock:
            self.invalid_message_count += 1

    def snapshot_and_reset(self) -> dict[str, Any]:
        with self.lock:
            snapshot = {
                "window_start": self.window_start,
                "window_end": now_local(),
                "sensor_name": self.last_sensor_name,
                "metrics": self.metrics,
                "alerts": list(self.alerts),
                "availability": self.availability,
                "availability_time": self.availability_time,
                "message_count": self.message_count,
                "invalid_message_count": self.invalid_message_count,
            }
            self.metrics = {key: MetricState(config) for key, config in self.metric_configs.items()}
            self.alerts.clear()
            self.message_count = 0
            self.invalid_message_count = 0
            self.window_start = now_local()
            # Availability is retained across windows as current state.
            return snapshot


def alert_label(kind: str) -> tuple[str, str, int]:
    mapping = {
        "temp": ("Wassertemperatur", "°C", 1),
        "pH": ("pH Wert", "", 2),
        "cl": ("Cl Wert", "mg/l", 2),
        "bat": ("Battery Spannung", "V", 2),
        "orp": ("ORP", "mV", 0),
        "ec": ("EC", "µS/cm", 0),
    }
    return mapping.get(kind, (kind, "", 2))


def format_alert(alert: AlertEvent) -> str:
    label, unit, decimals = alert_label(alert.kind)
    value_text = format_number(alert.value, decimals)
    min_text = format_number(alert.min_value, decimals)
    max_text = format_number(alert.max_value, decimals)
    value_part = f"{alert.kind}: {value_text} {unit}".strip()
    range_part = f"Soll: {min_text} - {max_text} {unit}".strip()

    if alert.is_alert:
        title = alert.text or f"{label} außerhalb Sollbereich"
        title = humanize_alert_text(title, label, True)
        return f" - **{title}** ({value_part}  {range_part}) {format_dt(alert.timestamp)}"

    title = alert.text or f"{label} wieder OK"
    title = humanize_alert_text(title, label, False)
    return f" - {title} ({value_part}  {range_part}) {format_dt(alert.timestamp)}"


def humanize_alert_text(text: str, label: str, is_alert: bool) -> str:
    lower = text.lower()
    if "back in range" in lower or "recovery" in lower:
        return f"{label} wieder OK"
    if "too high" in lower:
        return f"{label} zu hoch"
    if "too low" in lower:
        return f"{label} zu niedrig"
    if text.startswith("Alert:"):
        return f"{label} Alarm"
    return text


def build_email_body(snapshot: dict[str, Any]) -> str:
    lines: list[str] = []
    sensor_name = snapshot.get("sensor_name") or "PoolSensor"
    lines.append(f"Pool Status - {sensor_name} ({format_subject_date(snapshot['window_end'])})")
    lines.append("")

    alerts: list[AlertEvent] = snapshot["alerts"]
    if alerts:
        lines.append("<b>Warnung:</b>")
        lines.append("")
        for alert in alerts:
            lines.append(format_alert(alert))
            lines.append("")
        lines.append("")

    lines.append("<b>Übersicht:</b>")
    lines.append("")

    metrics: dict[str, MetricState] = snapshot["metrics"]
    latest_alert_by_kind: dict[str, AlertEvent] = {}
    for alert in alerts:
        latest_alert_by_kind[alert.kind] = alert

    preferred_order = ["temp", "pH", "cl", "bat", "orp", "ec", "salt", "tds", "bleRSSI", "wifiRSSI"]
    any_metric = False
    for key in preferred_order:
        state = metrics.get(key)
        if not state or state.last_value is None:
            continue
        any_metric = True
        value = state.value_text(state.avg_last_values)
        latest_alert = latest_alert_by_kind.get(key)
        if latest_alert and latest_alert.is_alert:
            value = f"**{value}**"

        lines.append(f"{state.config.label}: {value} \t (min: {state.value_text(state.min_value)} - max: {state.value_text(state.max_value)})")
        if latest_alert and (latest_alert.min_value is not None or latest_alert.max_value is not None):
            lines.append(f"\tSoll: {state.expected_range_text(latest_alert.min_value, latest_alert.max_value)}")
        lines.append("")

    if not any_metric:
        lines.append("Keine Messwerte im Zeitraum empfangen.")
        lines.append("")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"Sensor: {sensor_name}")
    if snapshot.get("availability"):
        lines.append(f"Availability: {snapshot['availability']} ({format_dt(snapshot.get('availability_time'))})")
    lines.append(f"Zeitraum: {format_dt(snapshot['window_start'])} - {format_dt(snapshot['window_end'])}")
    lines.append(f"Empfangene Messungen: {snapshot.get('message_count', 0)}")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def print_report_to_stdout(subject: str, body: str) -> None:
    separator = "=" * 72
    print(separator, flush=True)
    print(f"Subject: {subject}", flush=True)
    print("", flush=True)
    print(body, end="" if body.endswith("\n") else "\n", flush=True)
    print(separator, flush=True)


def build_email_body_html(snapshot: dict[str, Any]) -> str:
    sensor_name = snapshot.get("sensor_name") or "PoolSensor"
    alerts: list[AlertEvent] = snapshot["alerts"]
    metrics: dict[str, MetricState] = snapshot["metrics"]

    primary_keys = ["temp", "pH", "cl"]
    secondary_keys = ["bat", "orp", "ec", "salt", "tds", "bleRSSI", "wifiRSSI"]

    def table_rows(keys: list[str], bold_current: bool = True) -> str:
        rows = ""
        for key in keys:
            state = metrics.get(key)
            if not state or state.last_value is None:
                continue
            current = state.value_text(state.avg_last_values)
            if bold_current:
                current = f"<b>{current}</b>"
            mn = state.value_text(state.min_value)
            mx = state.value_text(state.max_value)
            rows += f"<tr><td>{state.config.label}</td><td>{current}</td><td>{mn}</td><td>{mx}</td></tr>\n"
        return rows

    def build_table(keys: list[str], font_size: int = 14, bold_current: bool = True, header_style: str = "background:#eee") -> str:
        rows = table_rows(keys, bold_current)
        if not rows:
            return ""
        return (
            f"<table border=\"1\" cellpadding=\"6\" cellspacing=\"0\" style=\"border-collapse:collapse;font-size:{font_size}px\">\n"
            f"<tr style=\"{header_style}\"><th>Messwert</th><th>Aktuell</th><th>Min</th><th>Max</th></tr>\n"
            f"{rows}</table>\n"
        )

    primary_html = build_table(primary_keys, font_size=16)
    secondary_html = build_table(secondary_keys, font_size=12, bold_current=False, header_style="background:#f5f5f5;color:#666")

    alerts_html = ""
    if alerts:
        items = "".join(
            f"<li{' style=\"color:#c00;font-weight:bold\"' if a.is_alert else ''}>{format_alert_html(a)}</li>\n"
            for a in alerts
        )
        alerts_html = f"<h2 style=\"color:#c00\">Warnung</h2><ul>\n{items}</ul>\n"

    metrics_html = primary_html
    if secondary_html:
        metrics_html += "<br>\n" + secondary_html
    if not primary_html and not secondary_html:
        metrics_html = "<p>Keine Messwerte im Zeitraum empfangen.</p>\n"

    availability_html = ""
    if snapshot.get("availability"):
        availability_html = f"<p>Availability: {snapshot['availability']} ({format_dt(snapshot.get('availability_time'))})</p>\n"

    return (
        "<!DOCTYPE html>\n<html>\n<head><meta charset=\"utf-8\"></head>\n<body>\n"
        f"<h1>Pool Status - {sensor_name} ({format_subject_date(snapshot['window_end'])})</h1>\n"
        f"{alerts_html}"
        f"<h2>Übersicht</h2>\n"
        f"{metrics_html}"
        f"<br><hr>\n"
        f"{availability_html}"
        f"<p>Zeitraum: {format_dt(snapshot['window_start'])} - {format_dt(snapshot['window_end'])}</p>\n"
        f"<p>Empfangene Messungen: {snapshot.get('message_count', 0)}</p>\n"
        "</body>\n</html>\n"
    )


def format_alert_html(alert: AlertEvent) -> str:
    label, unit, decimals = alert_label(alert.kind)
    value_text = format_number(alert.value, decimals)
    min_text = format_number(alert.min_value, decimals)
    max_text = format_number(alert.max_value, decimals)
    value_part = f"{alert.kind}: {value_text} {unit}".strip()
    range_part = f"Soll: {min_text} - {max_text} {unit}".strip()

    if alert.is_alert:
        title = alert.text or f"{label} außerhalb Sollbereich"
        title = humanize_alert_text(title, label, True)
        return f"<b>{title}</b> ({value_part} &nbsp; {range_part}) {format_dt(alert.timestamp)}"

    title = alert.text or f"{label} wieder OK"
    title = humanize_alert_text(title, label, False)
    return f"{title} ({value_part} &nbsp; {range_part}) {format_dt(alert.timestamp)}"


def send_email(subject: str, body: str, html_body: str = "") -> None:
    host = env_str("SMTP_HOST")
    port = env_int("SMTP_PORT", 587)
    username = env_str("SMTP_USERNAME")
    password = env_str("SMTP_PASSWORD")
    sender = env_str("MAIL_FROM", username)
    recipients = [addr.strip() for addr in env_str("MAIL_TO").split(",") if addr.strip()]

    if not username or not password or not sender or not recipients:
        raise RuntimeError("SMTP_USERNAME, SMTP_PASSWORD, MAIL_FROM and MAIL_TO must be configured")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(body, "plain", "utf-8"))
    if html_body:
        msg.attach(MIMEText(html_body, "html", "utf-8"))

    if env_bool("SMTP_STARTTLS", True):
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
            smtp.login(username, password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=30) as smtp:
            smtp.login(username, password)
            smtp.send_message(msg)


def send_test_email() -> None:
    subject = "Pool-Monitoring: Programm gestartet"
    server_ip = get_server_ip()
    body = (
        "Der mqtt2mail-Dienst wurde erfolgreich gestartet.\n"
        "\n"
        "SMTP-Verbindung wurde erfolgreich getestet.\n"
        f"Startzeit: {format_dt(now_local())}\n"
        f"Server-IP: {server_ip}\n"
        "\n"
        "Diese Mail dient nur zur Bestätigung der SMTP-Konfiguration."
    )
    html_body = (
        "<!DOCTYPE html>\n<html>\n<head><meta charset=\"utf-8\"></head>\n<body>\n"
        "<h1>Pool-Monitoring: Programm gestartet</h1>\n"
        "<p>Der mqtt2mail-Dienst wurde erfolgreich gestartet.</p>\n"
        "<p>SMTP-Verbindung wurde erfolgreich getestet.</p>\n"
        f"<p>Startzeit: {format_dt(now_local())}</p>\n"
        f"<p>Server-IP: {server_ip}</p>\n"
        "<hr>\n"
        "<p>Diese Mail dient nur zur Bestätigung der SMTP-Konfiguration.</p>\n"
        "</body>\n</html>\n"
    )
    try:
        send_email(subject, body, html_body)
        logging.info("Startup test email sent successfully (server IP: %s)", server_ip)
    except Exception as exc:
        logging.error("Failed to send startup test email: %s", exc)


def reporter_loop(aggregator: PoolAggregator, stop_event: threading.Event) -> None:
    interval = env_int("REPORT_INTERVAL_MINUTES", 15) * 60
    send_empty = env_bool("SEND_EMPTY_REPORT", False)
    report_times = parse_report_times(env_str("REPORT_TIMES", ""))

    if report_times:
        log_times = ", ".join(f"{t // 60:02d}:{t % 60:02d}" for t in report_times)
        logging.info("Report times configured: %s", log_times)

    while True:
        if report_times:
            delay = next_report_delay(report_times)
            if stop_event.wait(delay):
                return
        else:
            if stop_event.wait(interval):
                return

        snapshot = aggregator.snapshot_and_reset()
        if snapshot["message_count"] == 0 and not send_empty:
            logging.info("Skipping empty report window")
            continue
        sensor_name = snapshot.get("sensor_name") or "PoolSensor"
        subject = f"Pool Status - {sensor_name} ({format_subject_date(snapshot['window_end'])})"
        body = build_email_body(snapshot)
        html_body = build_email_body_html(snapshot)
        try:
            send_email(subject, body, html_body)
            logging.info("Report sent via email with %s MQTT messages", snapshot["message_count"])
        except Exception as exc:
            logging.error("Failed to send report email: %s", exc)
            print_report_to_stdout(subject, body)


def parse_json_payload(raw: bytes) -> Optional[dict[str, Any]]:
    try:
        decoded = raw.decode("utf-8", errors="replace")
        data = json.loads(decoded)
        if isinstance(data, dict):
            return data
        return None
    except json.JSONDecodeError:
        return None


def main() -> None:
    log_level = env_str("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    if log_level == "DEBUG":
        logging.getLogger("paho.mqtt.client").setLevel(logging.DEBUG)

    aggregator = PoolAggregator()
    stop_event = threading.Event()

    def handle_signal(signum: int, _frame: Any) -> None:
        logging.info("Received signal %s, shutting down", signum)
        stop_event.set()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    data_topics, alert_topics, availability_topics = resolve_topics()
    mqtt_host = env_str("MQTT_HOST")
    mqtt_port = env_int("MQTT_PORT", 1883)
    mqtt_client_id = env_str("MQTT_CLIENT_ID", f"pool-mqtt-mailer-{os.urandom(4).hex()}")

    if not mqtt_host:
        raise RuntimeError("MQTT_HOST must be configured")
    if not data_topics and not alert_topics:
        raise RuntimeError(
            "No MQTT topics configured. Set POOL_LIST with at least one pool entry."
        )

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_client_id)

    username = env_str("MQTT_USERNAME") or env_str("MQTT_USER")
    password = env_str("MQTT_PASSWORD") or env_str("MQTT_PASS")
    if username:
        client.username_pw_set(username, password or None)

    if env_bool("MQTT_TLS", False):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        client.tls_set_context(ctx)

    def on_connect(client: mqtt.Client, _userdata: Any, _flags: mqtt.ConnectFlags, reason_code: mqtt.ReasonCode, _properties: Any) -> None:
        if reason_code == 0:
            logging.info("Connected to MQTT broker %s:%s", mqtt_host, mqtt_port)
            all_topics = unique_topics(data_topics + alert_topics + availability_topics)
            for topic in all_topics:
                client.subscribe(topic, qos=0)
            logging.info("Subscribed topics: %s", ", ".join(all_topics))
        else:
            logging.error("MQTT connect failed: %s", reason_code)

    def on_message(_client: mqtt.Client, _userdata: Any, message: mqtt.MQTTMessage) -> None:
        topic = message.topic
        raw = message.payload
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError:
            decoded = repr(raw)
        print(f"[mqtt-debug] topic={topic} payload={decoded}", flush=True)
        logging.debug("MQTT message on %s: %s", topic, message.payload)

        if any(topic_matches(p, topic) for p in availability_topics):
            aggregator.add_availability(message.payload.decode("utf-8", errors="replace"))
            return

        payload = parse_json_payload(message.payload)
        if payload is None:
            logging.warning("Ignoring invalid JSON payload on topic %s", topic)
            aggregator.mark_invalid()
            return

        if any(topic_matches(p, topic) for p in alert_topics):
            aggregator.add_alert(payload)
        elif any(topic_matches(p, topic) for p in data_topics):
            aggregator.add_data(payload)
        else:
            logging.debug("Ignoring unexpected topic %s", topic)

    def on_disconnect(_client: mqtt.Client, _userdata: Any, _disconnect_flags: mqtt.DisconnectFlags, reason_code: mqtt.ReasonCode, _properties: Any) -> None:
        logging.warning("Disconnected from MQTT broker: %s", reason_code)

    def on_subscribe(_client: mqtt.Client, _userdata: Any, _mid: int, reason_code_list: list[mqtt.ReasonCode], _properties: Any) -> None:
        for rc in reason_code_list:
            if rc is not None and rc not in (0, 1, 2):
                logging.error("Subscribe denied (reason code: %s)", rc)

    client.reconnect_delay_set(min_delay=30, max_delay=300)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe

    reporter = threading.Thread(target=reporter_loop, args=(aggregator, stop_event), daemon=True)
    reporter.start()

    client.connect(mqtt_host, mqtt_port, keepalive=env_int("MQTT_KEEPALIVE", 60))
    client.loop_start()

    send_test_email()

    try:
        while not stop_event.wait(1):
            pass
    finally:
        client.loop_stop()
        client.disconnect()
        logging.info("Stopped")


if __name__ == "__main__":
    main()
