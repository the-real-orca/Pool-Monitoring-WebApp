"""Background aggregator: rolls the in-memory ring buffer into per-hour
SQLite aggregates and prunes old rows on a daily schedule.

Design notes:
  * The aggregation rule is intentionally simple: on each tick we take the
    complete samples for the previous hour bucket and write one row per
    (pool, metric). The ring buffer holds at most a few samples, so the
    per-hour mean is computed from that small window.
  * Failures are logged but never re-raised: a single bad insert must not
    stop the task. The task loop is also responsible for restarting its
    internal state should the underlying ``db`` become unavailable.
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Callable

import db
import live_state

log = logging.getLogger(__name__)

METRICS = ("temp", "pH", "cl")


def _hour_start(ts: int) -> int:
    """Return the unix timestamp at the start of the hour containing *ts*."""
    return ts - (ts % 3600)


def _collect_samples(state: live_state.LiveState, pool: str, metric: str, since_ts: int, until_ts: int) -> list[tuple[float, int]]:
    """Return samples for *pool*/*metric* in [since_ts, until_ts).

    The live state keeps the most-recent samples in a ring; we therefore
    return whatever lies in the requested window, in order. The ring is
    small (default 5), so the per-hour mean is computed from at most that
    many points.
    """
    out: list[tuple[float, int]] = []
    with state._lock:  # noqa: SLF001 - internal access for read-only iteration
        metrics = state._metrics.get(pool, {})
        ring = metrics.get(metric)
        if ring is None:
            return out
        for v, ts in ring.ring:
            if since_ts <= ts < until_ts:
                out.append((v, ts))
    out.sort(key=lambda x: x[1])
    return out


class Aggregator:
    """Per-hour aggregator with daily retention cleanup."""

    def __init__(
        self,
        state: live_state.LiveState,
        tick_seconds: int = 60,
        retention_days: int = 90,
        cleanup_hour_utc: int = 3,
        clock: Callable[[], float] = time.time,
    ):
        self._state = state
        self._tick = max(1, int(tick_seconds))
        self._retention_days = max(1, int(retention_days))
        self._cleanup_hour_utc = cleanup_hour_utc % 24
        self._clock = clock
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._last_cleanup_ymd: str | None = None

    def start(self) -> asyncio.Task:
        if self._task is not None:
            return self._task
        self._stop.clear()
        self._task = asyncio.create_task(self._run(), name="live-aggregator")
        return self._task

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            try:
                await asyncio.wait_for(self._task, timeout=5)
            except asyncio.TimeoutError:
                self._task.cancel()
            self._task = None

    async def _run(self) -> None:
        log.info("live aggregator started (tick=%ds, retention=%dd)", self._tick, self._retention_days)
        last_rollup_hour: int | None = None
        while not self._stop.is_set():
            try:
                now_ts = int(self._clock())
                current_hour = _hour_start(now_ts)
                # Roll up the previous hour once we cross into the next one.
                if last_rollup_hour is None:
                    last_rollup_hour = current_hour
                elif current_hour > last_rollup_hour:
                    self._rollup_window(last_rollup_hour, current_hour)
                    last_rollup_hour = current_hour
                self._maybe_daily_cleanup(now_ts)
            except Exception as e:
                log.exception("aggregator tick failed: %s", e)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self._tick)
            except asyncio.TimeoutError:
                pass

    def _rollup_window(self, since_ts: int, until_ts: int) -> None:
        if not db.is_configured():
            return
        for pool in self._state.get_known_pools():
            for metric in METRICS:
                samples = _collect_samples(self._state, pool, metric, since_ts, until_ts)
                if not samples:
                    continue
                values = [v for v, _ in samples]
                mean = sum(values) / len(values)
                try:
                    db.insert_aggregate(pool, metric, since_ts, mean, len(values))
                except Exception as e:
                    log.warning("insert_aggregate(%s, %s) failed: %s", pool, metric, e)

    def _maybe_daily_cleanup(self, now_ts: int) -> None:
        ymd = datetime.fromtimestamp(now_ts, tz=timezone.utc).strftime("%Y-%m-%d")
        hour = datetime.fromtimestamp(now_ts, tz=timezone.utc).hour
        if ymd == self._last_cleanup_ymd:
            return
        if hour != self._cleanup_hour_utc:
            return
        self._last_cleanup_ymd = ymd
        if not db.is_configured():
            return
        try:
            deleted = db.cleanup_old_rows(self._retention_days)
            if deleted:
                log.info("live-data retention cleanup: deleted %d rows", deleted)
        except Exception as e:
            log.warning("cleanup_old_rows failed: %s", e)
