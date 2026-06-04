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

const canvasRef = ref(null)
const containerRef = ref(null)
let chart = null
let resizeObserver = null

const empty = ref(true)
const loading = ref(false)
const error = ref(null)

const COLORS = {
  temp: '#0EA5E9',  // primary
  pH:   '#22C55E',  // success
  cl:   '#F59E0B',  // warning
}

function buildDatasets(histories) {
  // histories: { temp: {points}, pH: {points}, cl: {points} }
  const ds = []
  for (const metric of ['temp', 'pH', 'cl']) {
    const data = (histories[metric]?.points || []).map(p => ({ x: p.t * 1000, y: p.v }))
    ds.push({
      label: metric === 'temp' ? 'Temperatur (°C)' : metric === 'pH' ? 'pH' : 'Chlor (mg/l)',
      data,
      borderColor: COLORS[metric],
      backgroundColor: COLORS[metric] + '20',
      yAxisID: metric === 'temp' ? 'yTemp' : metric === 'pH' ? 'yPh' : 'yCl',
      tension: 0.25,
      pointRadius: 0,
      borderWidth: 2,
    })
  }
  return ds
}

function buildOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } },
      tooltip: { enabled: true },
      zoom: {
        pan: { enabled: true, mode: 'x' },
        zoom: {
          wheel: { enabled: false },
          pinch: { enabled: true },
          drag: { enabled: false },
          mode: 'x',
        },
      },
    },
    scales: {
      x: {
        type: 'time',
        time: { unit: 'day', displayFormats: { day: 'dd.MM' } },
        grid: { display: false },
      },
      yTemp: {
        type: 'linear', position: 'left',
        title: { display: true, text: '°C' },
        grid: { color: '#e2e8f0' },
      },
      yPh: {
        type: 'linear', position: 'right',
        title: { display: true, text: 'pH' },
        grid: { display: false },
        min: 6, max: 9,
      },
      yCl: {
        type: 'linear', position: 'right',
        title: { display: true, text: 'mg/l' },
        grid: { display: false },
        offset: true,
        min: 0, max: 5,
      },
    },
  }
}

async function reload() {
  if (!props.pool) return
  loading.value = true
  error.value = null
  const { fetchHistory } = useApi()
  const [temp, ph, cl] = await Promise.all([
    fetchHistory(props.pool, 'temp', props.days),
    fetchHistory(props.pool, 'pH', props.days),
    fetchHistory(props.pool, 'cl', props.days),
  ])
  loading.value = false
  const histories = { temp, pH: ph, cl }
  const hasAny = ['temp', 'pH', 'cl'].some(m => (histories[m]?.points || []).length > 0)
  empty.value = !hasAny
  if (chart) {
    chart.data.datasets = buildDatasets(histories)
    chart.update('none')
  }
}

function createChart() {
  if (!canvasRef.value) return
  if (chart) {
    chart.destroy()
    chart = null
  }
  chart = new Chart(canvasRef.value, {
    type: 'line',
    data: { datasets: buildDatasets({ temp: { points: [] }, pH: { points: [] }, cl: { points: [] } }) },
    options: buildOptions(),
  })
}

onMounted(() => {
  createChart()
  reload()
  if (containerRef.value && 'ResizeObserver' in window) {
    resizeObserver = new ResizeObserver(() => {
      if (chart) chart.resize()
    })
    resizeObserver.observe(containerRef.value)
  }
})

onBeforeUnmount(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (chart) {
    chart.destroy()
    chart = null
  }
})

watch(() => props.pool, () => {
  reload()
})
</script>

<template>
  <div ref="containerRef" class="relative h-64 w-full">
    <div v-if="loading && !chart" class="absolute inset-0 flex items-center justify-center text-slate-400">Lade…</div>
    <div v-if="empty" class="absolute inset-0 flex items-center justify-center text-slate-400">
      Noch keine Daten
    </div>
    <canvas ref="canvasRef" data-testid="trend-chart-canvas"></canvas>
  </div>
</template>
