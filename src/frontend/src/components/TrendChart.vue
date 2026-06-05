<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import uPlot from 'uplot'
import 'uplot/dist/uPlot.min.css'
import { useApi } from '../composables/useApi.js'

const props = defineProps({
  pool: { type: String, required: true },
  days: { type: Number, default: 7 },
})

const METRICS = [
  { key: 'temp', label: 'Temperatur', unit: '°C',   color: '#0EA5E9' },
  { key: 'pH',   label: 'pH',         unit: 'pH',   color: '#22C55E' },
  { key: 'cl',   label: 'Chlor',      unit: 'mg/l', color: '#F59E0B' },
]

const containerRefs = { temp: ref(null), pH: ref(null), cl: ref(null) }
const charts = { temp: null, pH: null, cl: null }
const resizeObservers = { temp: null, pH: null, cl: null }
// Oldest unix-seconds timestamp already loaded per metric (0 = none).
const earliestTs = { temp: 0, pH: 0, cl: 0 }
// Hard upper bound for the x-axis in unix-seconds. Latest data point or
// "now" — whichever is later. Prevents panning/zooming into the future.
let capSec = Math.floor(Date.now() / 1000)
let reloadTimer = null
let backfillInFlight = false
// Set while we are pushing a scale change to sibling charts (or
// triggering a data-driven scale change) so the setScale hook can skip
// the recursive broadcast and the backfill. Without this, every
// user-driven pan/zoom would also fire backfill on the *other* charts.
let isPropagating = false

const empty = ref(true)
const loading = ref(false)

// Returns the adaptive step (in seconds) that best fits the current
// visible span. Steps are always integer divisors of 24h so the 0h tick
// (midnight) is included as a `splits` boundary.
function stepForSpan(spanSec) {
  const hour = 3600, day = 86400
  if (spanSec <= 12 * hour)  return  2 * hour
  if (spanSec <= 24 * hour)  return  4 * hour
  if (spanSec <= 2 * day)    return  6 * hour
  if (spanSec <= 4 * day)    return 12 * hour
  if (spanSec <= 14 * day)   return      day
  return 2 * day
}

function makeSplitValues(spanSec) {
  return (self, axisIdx, scaleMin, scaleMax) => {
    const step = stepForSpan(spanSec)
    // Align to LOCAL-day (or sub-day) boundaries so the date label
    // appears at ticks where getHours() === 0 in the user's timezone.
    // uPlot passes scale min/max in seconds (ms: 1e-3 in opts, so unit
    // is seconds). We construct the first tick by stepping forward in
    // local time, then convert back to seconds.
    const stepMs = step * 1000
    const out = []
    // First tick: walk forward from scaleMin until we land on a local
    // boundary for the chosen step.
    const start = new Date(scaleMin * 1000)
    // Snap to next local "day" boundary (i.e. local midnight) when step
    // is a multiple of 24h. For sub-day steps, snap to the next local
    // hour boundary that is a multiple of `step / 3600`.
    const stepHours = step / 3600
    if (stepHours >= 24) {
      start.setHours(24, 0, 0, 0) // next local midnight
    } else {
      const nextHour = Math.ceil(start.getHours() / stepHours) * stepHours
      start.setHours(nextHour, 0, 0, 0)
    }
    let tMs = start.getTime()
    while (tMs / 1000 <= scaleMax) {
      out.push(Math.floor(tMs / 1000))
      tMs += stepMs
    }
    return out
  }
}

function makeTickLabels() {
  return (self, splits) => {
    const span = self.scales.x.max - self.scales.x.min
    const pad = n => String(n).padStart(2, '0')
    return splits.map((s, i) => {
      const d = new Date(s * 1000)
      const isMidnight = d.getHours() === 0 && d.getMinutes() === 0
      if (isMidnight) {
        return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}`
      }
      // Date anchor on the leftmost tick: when the user zooms in below
      // a 24h span, the regular step (2h, 4h, ...) never lands on local
      // midnight, so the user has no way to tell which day they are
      // looking at. We stack the date above the time using "\n", which
      // uPlot splits and renders as two lines (requires rotate: 0).
      if (span < 86400 && i === 0) {
        return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}\n${pad(d.getHours())}:${pad(d.getMinutes())}`
      }
      return `${pad(d.getHours())}:${pad(d.getMinutes())}`
    })
  }
}

// Touch gesture handler. Wire single-finger pan, two-finger pinch zoom
// and double-tap reset onto the uPlot overlay. Mirrors the desktop
// mouse handlers: pan delta maps to scale delta, pinch-distance ratio
// maps to range multiplier around the pinch midpoint. Right-edge
// clamp against capSec applies to both gestures so the user cannot
// pan/zoom into the future.
function touchGestureHandler(u) {
  const over = u.over
  const DOUBLE_TAP_MS = 300
  const TAP_SLOP_PX = 24

  let pan = null        // { startX, startMin, startMax, rect }
  let pinch = null      // { startDist, centerX, centerVal, leftPct, startMin, startMax, rect }
  let lastTap = null    // { time, x, y } for double-tap detection

  function endGesture() {
    pan = null
    pinch = null
  }

  over.addEventListener('touchstart', (e) => {
    if (e.touches.length === 0) return
    if (e.touches.length === 1) {
      const t = e.touches[0]
      const now = Date.now()
      // Double-tap detection runs on the second tap, before the pan
      // for that tap is recorded. The chart is reset and the pending
      // pan is dropped so the finger can stay down without dragging.
      if (lastTap &&
          now - lastTap.time < DOUBLE_TAP_MS &&
          Math.abs(t.clientX - lastTap.x) < TAP_SLOP_PX &&
          Math.abs(t.clientY - lastTap.y) < TAP_SLOP_PX) {
        e.preventDefault()
        lastTap = null
        endGesture()
        resetAllCharts()
        return
      }
      lastTap = { time: now, x: t.clientX, y: t.clientY }
      const r = over.getBoundingClientRect()
      pan = {
        startX: t.clientX,
        startMin: u.scales.x.min,
        startMax: u.scales.x.max,
        rect: r,
      }
      pinch = null
    } else if (e.touches.length >= 2) {
      e.preventDefault()
      lastTap = null
      pan = null
      const r = over.getBoundingClientRect()
      const a = e.touches[0]
      const b = e.touches[1]
      const dist = Math.hypot(b.clientX - a.clientX, b.clientY - a.clientY)
      if (dist <= 0) return
      const centerX = (a.clientX + b.clientX) / 2 - r.left
      pinch = {
        startDist: dist,
        centerX,
        centerVal: u.posToVal(centerX, 'x'),
        leftPct: centerX / r.width,
        startMin: u.scales.x.min,
        startMax: u.scales.x.max,
        rect: r,
      }
    }
  }, { passive: false })

  over.addEventListener('touchmove', (e) => {
    if (e.touches.length === 0) return
    e.preventDefault()
    if (e.touches.length === 1 && pan) {
      const t = e.touches[0]
      const dx = t.clientX - pan.startX
      const range = pan.startMax - pan.startMin
      const dVal = -(dx / pan.rect.width) * range
      let nMin = pan.startMin + dVal
      let nMax = pan.startMax + dVal
      if (nMax > capSec) {
        const shift = nMax - capSec
        nMin -= shift
        nMax -= shift
      }
      u.batch(() => {
        u.setScale('x', { min: nMin, max: nMax })
      })
    } else if (e.touches.length >= 2 && pinch) {
      const a = e.touches[0]
      const b = e.touches[1]
      const dist = Math.hypot(b.clientX - a.clientX, b.clientY - a.clientY)
      if (dist <= 0 || pinch.startDist <= 0) return
      const factor = dist / pinch.startDist
      if (!Number.isFinite(factor) || factor <= 0) return
      const oRange = pinch.startMax - pinch.startMin
      const nRange = oRange / factor
      const nMin = pinch.centerVal - pinch.leftPct * nRange
      const nMax = nMin + nRange
      u.batch(() => {
        u.setScale('x', { min: nMin, max: nMax })
      })
    }
  }, { passive: false })

  over.addEventListener('touchend', (e) => {
    if (e.touches.length === 0) endGesture()
  })
  over.addEventListener('touchcancel', endGesture)
}

// Pan + wheel-zoom plugin. uPlot does not implement pan when
// cursor.drag.setScale is false (it only honours box-zoom on left
// drag), so we wire our own mousedown / mousemove / mouseup handlers.
// Wheel-zoom around the cursor stays the same as before.
// stopImmediatePropagation in the capture phase prevents uPlot's own
// mousedown from running for the left button — it would otherwise
// mark the chart as "dragging" and the bubble-phase mousemove would
// do its own cursor-position bookkeeping we don't need.
function panZoomPlugin() {
  return {
    hooks: {
      ready(u) {
        const over = u.over
        let panning = false
        let startX = 0
        let startMin = 0
        let startMax = 0
        let rect = null

        over.addEventListener('wheel', (e) => {
          e.preventDefault()
          const factor = 0.75
          const r = over.getBoundingClientRect()
          const leftPct = (e.clientX - r.left) / r.width
          const xVal = u.posToVal(e.clientX - r.left, 'x')
          const oRange = u.scales.x.max - u.scales.x.min
          const nRange = e.deltaY < 0 ? oRange * factor : oRange / factor
          const nMin = xVal - leftPct * nRange
          const nMax = nMin + nRange
          u.batch(() => {
            u.setScale('x', { min: nMin, max: nMax })
          })
        }, { passive: false })

        over.addEventListener('mousedown', (e) => {
          if (e.button !== 0) return
          panning = true
          startX = e.clientX
          startMin = u.scales.x.min
          startMax = u.scales.x.max
          rect = over.getBoundingClientRect()
          e.stopImmediatePropagation()
        }, true)

        // mousemove / mouseup on window so we don't lose the gesture
        // when the cursor leaves the chart while dragging.
        window.addEventListener('mousemove', (e) => {
          if (!panning) return
          const dx = e.clientX - startX
          const range = startMax - startMin
          const dVal = -(dx / rect.width) * range
          let nMin = startMin + dVal
          let nMax = startMax + dVal
          // Clamp right edge to capSec so the user cannot pan into the
          // future, and shift the whole window by the same amount so
          // the left edge follows.
          if (nMax > capSec) {
            const shift = nMax - capSec
            nMin -= shift
            nMax -= shift
          }
          u.batch(() => {
            u.setScale('x', { min: nMin, max: nMax })
          })
        })

        window.addEventListener('mouseup', () => {
          panning = false
        })

        // Touch gestures: single-finger pan, two-finger pinch zoom,
        // double-tap reset. Mirrors the mouse handlers above so the
        // chart is fully operable on phones/tablets.
        touchGestureHandler(u)
      },
    },
  }
}

// Push a scale change to all charts except the source. Sets
// isPropagating so the per-chart setScale hook skips recursive
// broadcast and backfill. Used by:
//   - the setScale hook (user pan / wheel / dblclick on one chart)
//   - the dblclick handler (resets all three at once)
function broadcastScale(sourceKey, min, max) {
  if (isPropagating) return
  isPropagating = true
  try {
    for (const meta of METRICS) {
      if (meta.key === sourceKey) continue
      const other = charts[meta.key]
      if (other) other.setScale('x', { min, max })
    }
  } finally {
    isPropagating = false
  }
}

function makeOptions(metric) {
  return {
    width: 600,
    height: CHART_HEIGHT,
    legend: { show: false },
    cursor: {
      // We do pan and zoom ourselves in panZoomPlugin, so disable
      // uPlot's built-in drag/box-zoom entirely. setScale:false stops
      // uPlot from acting on a left-drag selection.
      drag: { setScale: false },
      points: { size: 6 },
    },
    scales: {
      x: { time: true },
      y: {},
    },
    series: [
      {},
      {
        label: metric.label,
        stroke: metric.color,
        fill: metric.color + '20',
        width: 2,
        points: { show: false },
        spanGaps: true,
      },
    ],
    axes: [
      {
        // 45° axis labels. The two-line "dd.MM\nHH:mm" leftmost anchor
        // renders as a small staircase along the rotation axis — that
        // is the look the user wants for the date+time anchor.
        size: 60,
        rotate: 45,
        stroke: '#64748b',
        grid: { stroke: '#f1f5f9', width: 1 },
        ticks: { stroke: '#cbd5e1', size: 6 },
        font: '11px system-ui, sans-serif',
        values: makeTickLabels(),
        // splits is set per-resize via applySplits() so it can adapt to
        // the current visible span.
      },
      {
        stroke: '#64748b',
        grid: { stroke: '#e2e8f0', width: 1 },
        ticks: { stroke: '#cbd5e1', size: 6 },
        font: '11px system-ui, sans-serif',
        label: metric.unit,
        labelGap: -8,
        labelSize: 8,
      },
    ],
    plugins: [panZoomPlugin()],
    hooks: {
      setScale: [
        (u) => {
          applySplits(u)
          if (isPropagating) return
          // User-initiated scale change on this chart: mirror it to
          // the other two and then check whether older data is needed.
          broadcastScale(metric.key, u.scales.x.min, u.scales.x.max)
          backfillIfNeeded(u, metric.key)
        },
      ],
    },
  }
}

function applySplits(u) {
  const span = u.scales.x.max - u.scales.x.min
  if (!Number.isFinite(span) || span <= 0) return
  // Skip redraw if the visible span hasn't changed — prevents tight
  // setScale → redraw → setScale feedback loops.
  if (u.axes[0]._lastSplitsSpan === span) return
  u.axes[0].splits = makeSplitValues(span)
  u.axes[0]._lastSplitsSpan = span
  u.redraw(false, true)
}

// Total chart height: plot (200) + bottom axis (60) = 260.
const CHART_HEIGHT = 260

function buildData(points) {
  // uPlot wants aligned arrays: [xs, ys]. NaN for missing values so
  // spanGaps can draw a clean line through holes.
  const xs = []
  const ys = []
  for (const p of points || []) {
    xs.push(p.t)
    ys.push(p.v == null ? NaN : p.v)
  }
  return [xs, ys]
}

function safeCap() {
  capSec = Math.max(Math.floor(Date.now() / 1000), capSec)
  return capSec
}

async function reload(resetWindow = true) {
  if (!props.pool) return
  loading.value = true
  const { fetchHistory } = useApi()
  const [temp, ph, cl] = await Promise.all([
    fetchHistory(props.pool, 'temp', props.days),
    fetchHistory(props.pool, 'pH', props.days),
    fetchHistory(props.pool, 'cl', props.days),
  ])
  const histories = { temp, pH: ph, cl }
  loading.value = false
  const hasAny = ['temp', 'pH', 'cl'].some(m => (histories[m]?.points || []).length > 0)
  empty.value = !hasAny
  safeCap()
  // Data-driven scale changes: don't broadcast, don't backfill. The
  // setScale hook consults this flag.
  isPropagating = true
  try {
    for (const meta of METRICS) {
      const pts = (histories[meta.key]?.points) || []
      earliestTs[meta.key] = pts.length ? pts[0].t : 0
      if (pts.length) capSec = Math.max(capSec, pts[pts.length - 1].t)
      const u = charts[meta.key]
      if (!u) continue
      u.setData(buildData(pts), resetWindow)
      if (resetWindow) {
        const firstVisible = capSec - props.days * 86400
        u.setScale('x', { min: firstVisible, max: capSec })
      } else {
        // Clamp right edge to "now" if it has advanced.
        if (u.scales.x.max > capSec) {
          const width = u.scales.x.max - u.scales.x.min
          u.setScale('x', { min: capSec - width, max: capSec })
        }
      }
      applySplits(u)
    }
  } finally {
    isPropagating = false
  }
}

async function backfillIfNeeded(sourceChart, key) {
  if (backfillInFlight) return
  const { fetchHistory } = useApi()
  backfillInFlight = true
  try {
    const visibleMin = sourceChart.scales.x.min
    let progress = true
    while (progress) {
      progress = false
      for (const meta of METRICS) {
        if (earliestTs[meta.key] <= 0) continue
        if (visibleMin - earliestTs[meta.key] > 2 * 3600) continue
        const data = await fetchHistory(props.pool, meta.key, props.days, earliestTs[meta.key])
        if (!data || !data.points || data.points.length === 0) {
          earliestTs[meta.key] = 0
          continue
        }
        const target = charts[meta.key]
        if (!target) continue
        // Only prepend points that are actually older than what we have.
        // If the server returns nothing older, stop refetching for this
        // metric.
        const existingMin = target.data[0][0]
        const newPoints = data.points.filter(p => p.t < existingMin)
        if (newPoints.length === 0) {
          earliestTs[meta.key] = 0
          continue
        }
        earliestTs[meta.key] = newPoints[0].t
        const existingXs = target.data[0]
        const existingSet = new Set(existingXs)
        const newXs = []
        const newYs = []
        for (const p of newPoints) {
          if (!existingSet.has(p.t)) {
            newXs.push(p.t)
            newYs.push(p.v == null ? NaN : p.v)
            existingSet.add(p.t)
          }
        }
        const mergedX = [...newXs, ...target.data[0]]
        const mergedY = [...newYs, ...target.data[1]]
        // isPropagating suppresses the recursive broadcast + backfill
        // triggered by setData → setScale.
        isPropagating = true
        try {
          target.setData([mergedX, mergedY], false)
        } finally {
          isPropagating = false
        }
        progress = true
      }
    }
  } catch {
    // Network/parse error: stay silent, retry on next pan.
  } finally {
    backfillInFlight = false
  }
}

function resetAllCharts() {
  isPropagating = true
  try {
    const firstVisible = capSec - props.days * 86400
    for (const m of METRICS) {
      const c = charts[m.key]
      if (c) c.setScale('x', { min: firstVisible, max: capSec })
    }
  } finally {
    isPropagating = false
  }
}

function createChart(meta) {
  const el = containerRefs[meta.key]?.value
  if (!el) return
  if (charts[meta.key]) {
    charts[meta.key].destroy()
    charts[meta.key] = null
  }
  const u = new uPlot(makeOptions(meta), [[], []], el)
  el.addEventListener('dblclick', resetAllCharts)
  return u
}

function destroyCharts() {
  for (const meta of METRICS) {
    if (charts[meta.key]) {
      charts[meta.key].destroy()
      charts[meta.key] = null
    }
  }
}

onMounted(() => {
  for (const meta of METRICS) {
    const u = createChart(meta)
    if (u) {
      charts[meta.key] = u
    }
  }
  reload(true)
  reloadTimer = setInterval(() => reload(false), 60_000)
  for (const meta of METRICS) {
    const el = containerRefs[meta.key]?.value
    if (el && 'ResizeObserver' in window) {
      resizeObservers[meta.key] = new ResizeObserver(() => {
        if (charts[meta.key]) {
          const rect = el.getBoundingClientRect()
          charts[meta.key].setSize({ width: rect.width, height: CHART_HEIGHT })
          applySplits(charts[meta.key])
        }
      })
      resizeObservers[meta.key].observe(el)
    }
  }
})

onBeforeUnmount(() => {
  if (reloadTimer !== null) {
    clearInterval(reloadTimer)
    reloadTimer = null
  }
  for (const meta of METRICS) {
    if (resizeObservers[meta.key]) {
      resizeObservers[meta.key].disconnect()
      resizeObservers[meta.key] = null
    }
  }
  destroyCharts()
})

watch(() => props.pool, () => { reload(true) })
watch(() => props.days, () => { reload(true) })
</script>

<template>
  <div class="">
    <div v-if="loading && !empty" class="text-center text-sm text-slate-400">Lade…</div>
    <div v-if="empty && !loading" class="text-center text-sm text-slate-400">Noch keine Daten</div>

    <div v-for="meta in METRICS" :key="meta.key" class="">
      <div class="text-xs font-semibold uppercase text-slate-500">{{ meta.label }}</div>
      <div :ref="el => { containerRefs[meta.key].value = el }" class="trend-chart-container" :data-testid="'trend-chart-' + meta.key"></div>
    </div>
  </div>
</template>

<style scoped>
.trend-chart-container {
  position: relative;
  height: 260px;
  width: 100%;
}
</style>
