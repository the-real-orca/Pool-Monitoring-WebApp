<script setup>
import { computed } from 'vue'

const props = defineProps({
  pump: { type: String, required: true, validator: v => v === 'main' || v === 'solar' },
  state: { type: [Boolean, null], default: null },
  runningSince: { type: [Number, null], default: null },
})

const isRunning = computed(() => props.state === true)
const isUnknown = computed(() => props.state === null || props.state === undefined)
const label = computed(() => props.pump === 'main' ? 'HAUPTPUMPE' : 'SOLARPUMPE')
const statusText = computed(() => {
  if (isUnknown.value) return 'Unbekannt'
  return isRunning.value ? 'LÄUFT' : 'AUS'
})

const sinceMinutes = computed(() => {
  if (!isRunning.value || !props.runningSince) return null
  const diff = Math.max(0, Math.floor(((Date.now() / 1000) - props.runningSince) / 60))
  return diff
})

const sinceText = computed(() => {
  if (!isRunning.value) return null
  if (sinceMinutes.value === null) return null
  if (sinceMinutes.value < 60) return `läuft seit ${sinceMinutes.value} min`
  const h = Math.floor(sinceMinutes.value / 60)
  const m = sinceMinutes.value % 60
  return `läuft seit ${h} h ${m} min`
})

const cardClass = computed(() => {
  if (isUnknown.value) return 'border-slate-200 bg-slate-50 text-slate-500'
  if (isRunning.value) return 'border-success/30 bg-success/10 text-success'
  return 'border-slate-200 bg-slate-100 text-slate-500'
})
</script>

<template>
  <div
    data-testid="pump-status-card"
    :data-pump="pump"
    :data-state="state === null ? 'unknown' : (isRunning ? 'running' : 'idle')"
    :class="['flex items-center gap-3 rounded-xl border-2 p-3', cardClass]"
  >
    <div class="flex size-11 items-center justify-center rounded-lg bg-white/70">
      <svg v-if="pump === 'main'" xmlns="http://www.w3.org/2000/svg" class="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      <svg v-else xmlns="http://www.w3.org/2000/svg" class="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
      </svg>
    </div>
    <div class="min-w-0 flex-1">
      <div class="text-xs font-semibold tracking-wide">{{ label }}</div>
      <div class="text-sm font-bold">{{ statusText }}</div>
      <div v-if="sinceText" class="text-xs opacity-75">{{ sinceText }}</div>
    </div>
  </div>
</template>
