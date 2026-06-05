"""Background aggregator: accumulates in-memory samples from the ring
buffer and writes one row per configurable time window to the
``measurements`` table.

Design notes:
  * Samples are collected from the ring buffer on each tick (default 30 s).
    The ring buffer must be large enough to hold samples for at least one
    tick interval to avoid gaps (see ``LIVE_SAMPLE_RING_SIZE``).
  * At the end of each window (default 60 min) one row per (pool, metric)
    is written – the arithmetic mean of all samples within that window.
  * Failures are logged but never re-raised: a single bad insert must not
    stop the task.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable

import db
import live_state

log = logging.getLogger(__name__)

METRICS = ("temp", "pH", "cl")


class Aggregator:
    """Per-window aggregator with daily retention cleanup."""

    def __init__(
        self,
        state: live_state.LiveState,
        window_minutes: int = 60,
        tick_seconds: int = 30,
        retention_days: int = 90,
        cleanup_hour_utc: int = 3,
        clock: Callable[[], float] = time.time,
        min_cleanup_interval_seconds: int = 20 * 3600,
    ):
        self._state = state
        self._window_seconds = max(1, int(window_minutes)) * 60
        self._tick = max(1, int(tick_seconds))
        self._retention_days = max(1, int(retention_days))
        self._cleanup_hour_utc = cleanup_hour_utc % 24
        self._clock = clock
        self._min_cleanup_interval = max(1, int(min_cleanup_interval_seconds))
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._last_cleanup_ymd: str | None = None
        self._last_cleanup_ts: int | None = None

        # Accumulated samples from the ring buffer, keyed by pool → metric.
        self._pending: dict[str, dict[str, list[tuple[float, int]]]] = {}
        # Highest timestamp already read per pool/metric (dedup guard).
        self._last_read_ts: dict[str, dict[str, int]] = {}

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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _window_start(ts: float, window_seconds: int) -> int:
        """Return the unix timestamp at the start of the window containing *ts*."""
        return int(ts) - (int(ts) % window_seconds)

    def _collect(self) -> None:
        """Read new samples from the ring buffer into ``_pending``."""
        now_ts = int(self._clock())
        for pool in self._state.get_known_pools():
            for metric in METRICS:
                since = self._last_read_ts.get(pool, {}).get(metric, 0)
                samples = self._state.iter_samples(pool, metric, since + 1, now_ts + 1)
                if not samples:
                    continue
                log.debug(
                    "aggregator collect: pool=%s metric=%s n=%d since=%d until=%d",
                    pool, metric, len(samples), since, now_ts,
                )
                self._pending.setdefault(pool, {}).setdefault(metric, []).extend(samples)
                new_last = max(ts for _, ts in samples)
                self._last_read_ts.setdefault(pool, {}).setdefault(metric, 0)
                if new_last > self._last_read_ts[pool][metric]:
                    self._last_read_ts[pool][metric] = new_last

    def _flush_window(self, window_start: int) -> None:
        """Compute the arithmetic mean of accumulated samples for *window_start*
        and write exactly one row per (pool, metric)."""
        if not db.is_configured():
            return
        window_end = window_start + self._window_seconds
        for pool, metrics in list(self._pending.items()):
            for metric, samples in list(metrics.items()):
                in_window = [(v, ts) for v, ts in samples if window_start <= ts < window_end]
                if not in_window:
                    continue
                values = [v for v, _ in in_window]
                mean = sum(values) / len(values)
                try:
                    db.insert_aggregate(pool, metric, window_start, mean, len(values))
                    log.debug(
                        "aggregator flush: pool=%s metric=%s window=%d n=%d mean=%.4f",
                        pool, metric, window_start, len(values), mean,
                    )
                except Exception as e:
                    log.warning("insert_aggregate(%s, %s) failed: %s", pool, metric, e)
                # Remove consumed samples from pending list.
                self._pending[pool][metric] = [(v, ts) for v, ts in samples if ts >= window_end]

    def _maybe_daily_cleanup(self, now_ts: int) -> None:
        if self._last_cleanup_ts is not None and now_ts - self._last_cleanup_ts < self._min_cleanup_interval:
            return
        from datetime import datetime, timezone
        ymd = datetime.fromtimestamp(now_ts, tz=timezone.utc).strftime("%Y-%m-%d")
        hour = datetime.fromtimestamp(now_ts, tz=timezone.utc).hour
        if ymd == self._last_cleanup_ymd:
            return
        if hour != self._cleanup_hour_utc:
            return
        self._last_cleanup_ymd = ymd
        self._last_cleanup_ts = now_ts
        if not db.is_configured():
            return
        try:
            deleted = db.cleanup_old_rows(self._retention_days)
            if deleted:
                log.info("live-data retention cleanup: deleted %d rows", deleted)
        except Exception as e:
            log.warning("cleanup_old_rows failed: %s", e)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def _run(self) -> None:
        log.info(
            "live aggregator started (window=%ds, tick=%ds, retention=%dd)",
            self._window_seconds,
            self._tick,
            self._retention_days,
        )
        last_window: int | None = None
        while not self._stop.is_set():
            try:
                now = self._clock()
                current_window = self._window_start(now, self._window_seconds)

                self._collect()

                if last_window is None:
                    last_window = current_window
                elif current_window > last_window:
                    self._flush_window(last_window)
                    last_window = current_window

                self._maybe_daily_cleanup(int(now))
            except Exception as e:
                log.exception("aggregator tick failed: %s", e)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self._tick)
            except asyncio.TimeoutError:
                pass
