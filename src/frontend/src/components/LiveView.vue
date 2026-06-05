<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useApi } from '../composables/useApi.js'
import { useLiveData } from '../composables/useLiveData.js'
import PumpStatusCard from './PumpStatusCard.vue'
import TrendChart from './TrendChart.vue'

const pools = ref([])
const selectedPool = ref('')
const loadError = ref(null)

const { fetchPoolsLive, error: apiError } = useApi()
const { snapshot, usingCached, stale, loading, start, stop } = useLiveData()

const tempText = computed(() => {
  if (!snapshot.value || snapshot.value.temp == null) return '--'
  return Number(snapshot.value.temp).toFixed(1)
})
const phText = computed(() => {
  if (!snapshot.value || snapshot.value.pH == null) return '--'
  return Number(snapshot.value.pH).toFixed(1)
})
const clText = computed(() => {
  if (!snapshot.value || snapshot.value.cl == null) return '--'
  return Number(snapshot.value.cl).toFixed(1)
})
const lastUpdateText = computed(() => {
  if (!snapshot.value || !snapshot.value.ts) return '—'
  return new Date(snapshot.value.ts * 1000).toLocaleString('de-AT')
})
const mainPump = computed(() => snapshot.value?.pump?.main || { running: null, since: null })
const solarPump = computed(() => snapshot.value?.pump?.solar || { running: null, since: null })

const hasSnapshot = computed(() => snapshot.value !== null && snapshot.value.ts > 0)
const hasAnyPool = computed(() => pools.value.length > 0)
const persistentError = computed(() => usingCached.value && hasSnapshot.value)

async function loadPools() {
  const list = await fetchPoolsLive()
  if (list) {
    pools.value = list
    const remembered = localStorage.getItem('lastPoolName')
    if (remembered && list.find(p => p.name === remembered)) {
      selectedPool.value = remembered
    } else if (!selectedPool.value && list.length > 0) {
      selectedPool.value = list[0].name
    }
  } else {
    loadError.value = 'pools'
  }
}

async function retry() {
  loadError.value = null
  await loadPools()
  if (selectedPool.value) {
    await start(selectedPool.value)
  }
}

watch(selectedPool, (newName) => {
  if (newName) {
    localStorage.setItem('lastPoolName', newName)
    start(newName)
  }
})

onMounted(async () => {
  await loadPools()
  if (selectedPool.value) {
    await start(selectedPool.value)
  }
})

onBeforeUnmount(() => {
  stop()
})
</script>

<template>
  <div data-testid="live-view" class="space-y-4">
    <div class="flex justify-center">
      <select
        v-if="hasAnyPool"
        v-model="selectedPool"
        data-testid="pool-selector"
        class="w-full max-w-xs rounded-lg border border-slate-300 bg-white px-3 py-2 text-center text-xl font-bold text-slate-800 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
      >
        <option v-for="p in pools" :key="p.name" :value="p.name">{{ p.name }}</option>
      </select>
    </div>

    <div v-if="!hasAnyPool && loadError" class="rounded-lg bg-error/10 p-4 text-sm text-error">
      <p>Verbindung fehlgeschlagen.</p>
      <button @click="retry" class="mt-2 rounded bg-primary px-3 py-1 text-sm font-medium text-white">Erneut versuchen</button>
    </div>

    <template v-if="hasSnapshot">
      <div data-testid="temperature-card" class="rounded-2xl bg-primary/5 p-6 text-center">
        <div class="text-sm font-semibold uppercase tracking-wider text-primary">Temperatur</div>
        <div class="my-2 text-5xl font-bold text-slate-800">
          {{ tempText }}<span class="ml-1 text-2xl font-normal text-slate-500">°C</span>
        </div>
        <div v-if="stale" data-testid="stale-badge" class="inline-block rounded-full bg-slate-200 px-3 py-1 text-xs font-semibold text-slate-600">Stale</div>
        <div class="mt-1 text-xs text-slate-500">Letztes Update: {{ lastUpdateText }}</div>
        <div v-if="usingCached" class="text-xs text-warning">Cache (offline)</div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div data-testid="ph-card" class="rounded-xl border border-slate-200 bg-white p-4 text-center">
          <div class="text-xs font-semibold uppercase text-slate-500">pH</div>
          <div class="mt-1 text-3xl font-bold text-slate-800">{{ phText }}</div>
          <div class="mt-1 text-xs text-slate-400">&nbsp;</div>
        </div>
        <div data-testid="cl-card" class="rounded-xl border border-slate-200 bg-white p-4 text-center">
          <div class="text-xs font-semibold uppercase text-slate-500">Chlor</div>
          <div class="mt-1 text-3xl font-bold text-slate-800">
            {{ clText }}<span class="ml-0.5 text-sm font-normal text-slate-400">mg/l</span>
          </div>
          <div class="mt-1 text-xs text-slate-400">&nbsp;</div>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <PumpStatusCard pump="main" :state="mainPump.running" :running-since="mainPump.since" />
        <PumpStatusCard pump="solar" :state="solarPump.running" :running-since="solarPump.since" />
      </div>
    </template>

    <div v-if="!hasSnapshot && !loadError" class="rounded-lg bg-slate-100 p-4 text-center text-sm text-slate-500">
      Warte auf Daten…
    </div>

    <div v-if="selectedPool" class="rounded-xl border border-slate-200 bg-white p-4">
      <h2 class="mb-2 text-sm font-semibold text-slate-700">Trend</h2>
      <TrendChart :pool="selectedPool" :days="7" />
    </div>
  </div>
</template>
