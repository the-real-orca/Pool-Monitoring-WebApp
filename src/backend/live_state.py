"""Thread-safe in-memory live state for Phase 20.

The MQTT callback thread and the FastAPI request handler both touch this
state, so all reads and writes are serialized through a single ``Lock``.

Per-pool state holds:
  * a per-metric ring buffer of the most recent samples (for short-window
    smoothing of pH/Cl in the UI),
  * the last value + timestamp for that metric (so the temperature can be
    displayed immediately without waiting for the next sample),
  * the current boolean state of each known pump and the timestamp of the
    last observed change.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Deque


class _MetricRing:
    __slots__ = ("ring", "last_value", "last_ts", "has_data")

    def __init__(self, ring_size: int):
        self.ring: Deque[tuple[float, int]] = deque(maxlen=ring_size)
        self.last_value: float | None = None
        self.last_ts: int = 0
        self.has_data: bool = False

    def push(self, value: float, ts: int) -> None:
        self.ring.append((float(value), int(ts)))
        self.last_value = float(value)
        self.last_ts = int(ts)
        self.has_data = True

    def mean(self) -> float | None:
        if not self.ring:
            return None
        return sum(v for v, _ in self.ring) / len(self.ring)


class LiveState:
    """Single source of truth for in-memory live values."""

    _KNOWN_METRICS = ("temp", "pH", "cl")
    _KNOWN_PUMPS = ("main", "solar")

    def __init__(self, ring_size: int = 5, stale_after_seconds: int = 600):
        self._ring_size = max(1, int(ring_size))
        self._stale_after = max(1, int(stale_after_seconds))
        self._lock = threading.Lock()
        self._metrics: dict[str, dict[str, _MetricRing]] = {}
        self._pumps: dict[str, dict[str, dict]] = {}

    # -- writers ------------------------------------------------------------

    def push_sample(self, pool: str, metric: str, value: float, ts: int) -> None:
        """Append a sensor sample. Silently ignores unknown metrics."""
        if metric not in self._KNOWN_METRICS:
            return
        with self._lock:
            pool_metrics = self._metrics.setdefault(pool, {})
            ring = pool_metrics.get(metric)
            if ring is None:
                ring = _MetricRing(self._ring_size)
                pool_metrics[metric] = ring
            ring.push(value, ts)

    def set_pump(self, pool: str, name: str, state: bool, ts: int) -> bool:
        """Set pump state. Returns True only on actual state change."""
        if name not in self._KNOWN_PUMPS:
            return False
        with self._lock:
            pool_pumps = self._pumps.setdefault(pool, {})
            current = pool_pumps.get(name)
            if current is not None and bool(current["state"]) == bool(state):
                return False
            pool_pumps[name] = {"state": bool(state), "since": int(ts)}
            return True

    # -- readers ------------------------------------------------------------

    def get_snapshot(self, pool: str) -> dict:
        """Return the current snapshot for one pool.

        All metrics are the mean of the ring buffer.
        ``stale`` is True when no sample has been received
        within ``stale_after_seconds``.
        """
        now = int(time.time())
        with self._lock:
            metrics = self._metrics.get(pool, {})
            pump_map = dict(self._pumps.get(pool, {}))

        temp = metrics.get("temp")
        ph = metrics.get("pH")
        cl = metrics.get("cl")

        ts_candidates = []
        if temp is not None and temp.has_data:
            ts_candidates.append(temp.last_ts)
        if ph is not None and ph.has_data:
            ts_candidates.append(ph.last_ts)
        if cl is not None and cl.has_data:
            ts_candidates.append(cl.last_ts)
        last_ts = max(ts_candidates) if ts_candidates else 0
        stale_seconds = (now - last_ts) if last_ts else None
        stale = stale_seconds is None or stale_seconds > self._stale_after

        return {
            "ts": last_ts,
            "temp": temp.mean() if temp is not None else None,
            "pH": ph.mean() if ph is not None else None,
            "cl": cl.mean() if cl is not None else None,
            "pump": {
                "main": {
                    "running": bool(pump_map["main"]["state"]) if "main" in pump_map else None,
                    "since": int(pump_map["main"]["since"]) if "main" in pump_map else None,
                },
                "solar": {
                    "running": bool(pump_map["solar"]["state"]) if "solar" in pump_map else None,
                    "since": int(pump_map["solar"]["since"]) if "solar" in pump_map else None,
                },
            },
            "stale": bool(stale),
            "staleSeconds": int(stale_seconds) if stale_seconds is not None else None,
        }

    def get_known_pools(self) -> list[str]:
        with self._lock:
            return list(self._metrics.keys() | self._pumps.keys())

    def has_data(self, pool: str) -> bool:
        with self._lock:
            metrics = self._metrics.get(pool, {})
            return any(r.has_data for r in metrics.values())

    def iter_samples(
        self, pool: str, metric: str, since_ts: int, until_ts: int
    ) -> list[tuple[float, int]]:
        """Return ``(value, timestamp)`` samples for *pool*/*metric* in
        ``[since_ts, until_ts)``, ordered by timestamp. Public alternative
        to reaching into the private ring buffer."""
        with self._lock:
            ring = self._metrics.get(pool, {}).get(metric)
            if ring is None:
                return []
            return [(v, ts) for v, ts in ring.ring if since_ts <= ts < until_ts]

    def stale_after(self) -> int:
        return self._stale_after

    def ring_size(self) -> int:
        return self._ring_size
