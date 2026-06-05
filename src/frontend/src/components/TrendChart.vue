<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Chart, LineController, LineElement, PointElement, LinearScale, TimeScale, Tooltip, Legend, Filler } from 'chart.js'
import 'chartjs-adapter-date-fns'
import { useApi } from '../composables/useApi.js'

Chart.register(LineController, LineElement, PointElement, LinearScale, TimeScale, Tooltip, Legend, Filler)

const props = defineProps({
  pool: { type: String, required: true },
  days: { type: Number, default: 7 },
})

const METRICS = [
  { key: 'temp', label: 'Temperatur', unit: '°C', color: '#0EA5E9' },
  { key: 'pH',   label: 'pH',         unit: 'pH', color: '#22C55E' },
  { key: 'cl',   label: 'Chlor',      unit: 'mg/l', color: '#F59E0B' },
]

const canvasRefs = { temp: ref(null), pH: ref(null), cl: ref(null) }
const containerRefs = { temp: ref(null), pH: ref(null), cl: ref(null) }
const charts = { temp: null, pH: null, cl: null }
const resizeObservers = { temp: null, pH: null, cl: null }
// Oldest timestamp already loaded per metric (unix seconds, 0 = none).
const earliestTs = { temp: 0, pH: 0, cl: 0 }
// Hard upper bound for the x-axis: latest data point or "now", whichever
// is later. Prevents panning/zooming into the future.
let capMs = Date.now()
let reloadTimer = null
// Guard against recursive backfill triggered by syncXScale → onPanComplete.
let backfillInFlight = false

const empty = ref(true)
const loading = ref(false)

function makeOptions(metric, key) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: { enabled: true },
      zoom: {
        zoom: {
          wheel: { enabled: true },
          pinch: { enabled: true },
          drag: {
            enabled: true,
            modifierKey: 'ctrl',
            backgroundColor: 'rgba(14,165,233,0.15)',
          },
          mode: 'x',
          onZoomComplete: ({ chart }) => {
            syncXScale(chart, key)
            backfillIfNeeded(chart, key)
          },
        },
        pan: {
          enabled: true,
          mode: 'x',
          onPanComplete: ({ chart }) => {
            syncXScale(chart, key)
            backfillIfNeeded(chart, key)
          },
        },
        limits: { x: { minRange: 60 * 60 * 1000, max: capMs } },
      },
    },
    scales: {
      x: {
        type: 'time',
        time: { unit: 'day', displayFormats: { day: 'dd.MM' } },
        grid: { display: false },
      },
      y: {
        type: 'linear', position: 'left',
        title: { display: true, text: metric.unit },
        grid: { color: '#e2e8f0' },
      },
    },
  }
}

function syncXScale(sourceChart, sourceKey) {
  const { min, max } = sourceChart.scales.x
  for (const meta of METRICS) {
    if (meta.key === sourceKey) continue
    const other = charts[meta.key]
    if (!other) continue
    other.options.scales.x.min = min
    other.options.scales.x.max = max
    other.update('none')
  }
}

function buildDataset(metric, points) {
  return {
    label: metric.label,
    data: (points || []).map(p => ({ x: p.t * 1000, y: p.v })),
    borderColor: metric.color,
    backgroundColor: metric.color + '20',
    tension: 0.25,
    pointRadius: 0,
    borderWidth: 2,
    fill: true,
  }
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
  // Update the global cap to "now" (or latest data, whichever is later)
  // so panning/zooming can never reach into the future.
  capMs = Math.max(Date.now(), capMs)
  for (const meta of METRICS) {
    const pts = (histories[meta.key]?.points) || []
    earliestTs[meta.key] = pts.length ? pts[0].t : 0
    if (pts.length) capMs = Math.max(capMs, pts[pts.length - 1].t * 1000)
    if (charts[meta.key]) {
      charts[meta.key].data.datasets = [buildDataset(meta, pts)]
      charts[meta.key].options.plugins.zoom.limits.x.max = capMs
      if (resetWindow) {
        const firstVisible = capMs - props.days * 86400 * 1000
        charts[meta.key].options.scales.x.min = firstVisible
        charts[meta.key].options.scales.x.max = capMs
      } else {
        // Clamp the current right edge in case "now" advanced since last reload.
        if (charts[meta.key].options.scales.x.max > capMs) {
          const width = charts[meta.key].options.scales.x.max - charts[meta.key].options.scales.x.min
          charts[meta.key].options.scales.x.max = capMs
          charts[meta.key].options.scales.x.min = capMs - width
        }
      }
      charts[meta.key].update('none')
    }
  }
  if (resetWindow && charts[METRICS[0].key]) {
    syncXScale(charts[METRICS[0].key], METRICS[0].key)
  }
}

async function backfillIfNeeded(chart, key) {
  if (backfillInFlight) return
  // Backfill any metric whose oldest loaded point is within 2h of the
  // currently visible left edge. We loop so a single pan can pull in
  // several chunks per metric if the user jumped far into the past.
  const { fetchHistory } = useApi()
  backfillInFlight = true
  try {
    const visibleMin = chart.scales.x.min
    let progress = true
    while (progress) {
      progress = false
      for (const meta of METRICS) {
        if (earliestTs[meta.key] <= 0) continue
        const earliestMs = earliestTs[meta.key] * 1000
        if (visibleMin - earliestMs > 2 * 3600 * 1000) continue
        const data = await fetchHistory(props.pool, meta.key, props.days, earliestTs[meta.key])
        if (!data || !data.points || data.points.length === 0) {
          earliestTs[meta.key] = 0
          continue
        }
        const target = charts[meta.key]
        if (!target) continue
        earliestTs[meta.key] = data.points[0].t
        const curMin = target.scales.x.min
        const curMax = target.scales.x.max
        const currentPts = target.data.datasets[0].data || []
        const prepend = data.points.map(p => ({ x: p.t * 1000, y: p.v }))
        target.data.datasets[0].data = [...prepend, ...currentPts]
        target.options.scales.x.min = curMin
        target.options.scales.x.max = curMax
        target.update('none')
        progress = true
      }
    }
    syncXScale(chart, key)
  } catch (e) {
    // Network/parse error: stay silent, retry on next pan.
  } finally {
    backfillInFlight = false
  }
}

function createCharts() {
  for (const meta of METRICS) {
    const el = canvasRefs[meta.key]?.value
    if (!el) continue
    if (charts[meta.key]) {
      charts[meta.key].destroy()
      charts[meta.key] = null
    }
    charts[meta.key] = new Chart(el, {
      type: 'line',
      data: { datasets: [buildDataset(meta, [])] },
      options: makeOptions(meta, meta.key),
    })
    el.addEventListener('dblclick', () => {
      charts[meta.key]?.resetZoom()
      syncXScale(charts[meta.key], meta.key)
    })
  }
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
  createCharts()
  reload(true)
  reloadTimer = setInterval(() => reload(false), 60_000)
  for (const meta of METRICS) {
    const el = containerRefs[meta.key]?.value
    if (el && 'ResizeObserver' in window) {
      resizeObservers[meta.key] = new ResizeObserver(() => {
        if (charts[meta.key]) charts[meta.key].resize()
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
  <div class="space-y-4">
    <div v-if="loading && !empty" class="text-center text-sm text-slate-400">Lade…</div>
    <div v-if="empty && !loading" class="text-center text-sm text-slate-400">Noch keine Daten</div>

    <div v-for="meta in METRICS" :key="meta.key" class="space-y-1">
      <div class="text-xs font-semibold uppercase text-slate-500">{{ meta.label }}</div>
      <div :ref="el => { containerRefs[meta.key].value = el }" class="relative h-48 w-full">
        <canvas :ref="el => { canvasRefs[meta.key].value = el }" :data-testid="'trend-chart-' + meta.key"></canvas>
      </div>
    </div>
  </div>
</template>
