<script setup>
import { computed, reactive, ref, onMounted, watch } from 'vue'
import { useApi } from '../composables/useApi.js'
import { useToast } from '../composables/useToast.js'
import ValueSliderInput from './ValueSliderInput.vue'
import { FRACTION_UNITS, stepFor, amountDecimals, amountEmptyValue, snapAmount } from '../utils/eventStep.js'

const { postEvent, fetchPools, loading, error } = useApi()
const { show: showToast } = useToast()

const eventOptions = [
  { label: 'Chlor', value: 'chlorine' },
  { label: 'pH-Plus', value: 'ph_plus' },
  { label: 'pH-Minus', value: 'ph_minus' },
  { label: 'Flockungsmittel', value: 'flocculant' },
  { label: 'Nachfüllen', value: 'refill' },
  { label: 'Rückspülen', value: 'backwash' },
  { label: 'Wintermittel', value: 'winter' },
]

// Map UI eventType -> default unit. ph_plus / ph_minus both map to grams.
const DEFAULT_UNIT = {
  chlorine: 'tabs',
  ph_plus: 'g',
  ph_minus: 'g',
  flocculant: 'l',
  winter: 'l',
  refill: 'min',
  backwash: 'min',
}

// Step width grows with the value (see utils/eventStep.js). Asymmetric at
// thresholds: pressing "-" uses the step one tick below, so 1.0 l − → 0.9
// (not 0) and 10 − → 9 (not 0). Valid grid: l/kg = 0.1…0.9, 1…9, 10, 20…
// other = 1…9, 10, 20… up to 100.
const AMOUNT_CONFIG = computed(() => ({
  min: 0.0,
  max: 100.0,
  step: stepFor(form.unit, form.amount, +1),
  stepDown: stepFor(form.unit, form.amount, -1),
  decimals: amountDecimals(form.unit),
  unit: '',
  emptyValue: amountEmptyValue(form.unit, form.amount),
}))

const pools = ref([])
const showNote = ref(false)

const form = reactive({
  time: '',
  name: localStorage.getItem('lastPoolName') || '',
  eventType: 'chlorine',
  amount: null,
  unit: DEFAULT_UNIT.chlorine,
  note: '',
})

const errors = reactive({})

watch(() => form.name, (newName) => {
  if (newName) localStorage.setItem('lastPoolName', newName)
})

watch(() => form.eventType, (newType) => {
  // Switch the default unit to match the new event type, but keep any
  // amount the user has already entered (per Senior-Engineer decision).
  const def = DEFAULT_UNIT[newType]
  if (def) form.unit = def
})

// Snap any value into the closest valid step (drag/manual entry). The
// stepper itself only produces valid values; rules live in utils/eventStep.js.
watch(() => form.amount, (newAmount) => {
  if (newAmount === 0) {
    // Reset to the sentinel "empty" state used by the slider, but keep the
    // currently selected unit — when amount is missing, the unit is simply
    // ignored at submit time (validator + payload builder both check amount).
    form.amount = null
    delete errors.amount
    return
  }
  if (newAmount == null) return
  const snapped = snapAmount(form.unit, newAmount)
  if (snapped !== newAmount) {
    form.amount = snapped
  }
})

onMounted(async () => {
  pools.value = await fetchPools()
  if (pools.value.length && !form.name) {
    form.name = pools.value[0].name
  }
})

function initDateTime() {
  const now = new Date()
  const offset = now.getTimezoneOffset()
  const local = new Date(now.getTime() - offset * 60000)
  form.time = local.toISOString().slice(0, 16)
}

function resetForm() {
  form.eventType = 'chlorine'
  form.amount = null
  form.unit = DEFAULT_UNIT.chlorine
  form.note = ''
  showNote.value = false
  Object.keys(errors).forEach(k => delete errors[k])
  initDateTime()
}

function validate() {
  Object.keys(errors).forEach(k => delete errors[k])
  let valid = true

  if (!form.name || form.name.length < 1 || form.name.length > 50) {
    errors.name = 'Bitte einen Pool auswaehlen'
    valid = false
  }

  if (!form.time) {
    errors.time = 'Datum und Uhrzeit sind erforderlich'
    valid = false
  }

  // Amount is optional: when it's missing the unit is ignored (no pair
  // check, no error). When it IS set, it must be > 0. The unit dropdown
  // always carries a value (default per event type), so no pair-check
  // is needed here.
  if (form.amount != null) {
    if (Number.isNaN(form.amount) || form.amount <= 0) {
      errors.amount = 'Menge muss groesser als 0 sein'
      valid = false
    }
  }

  if (form.note && form.note.length > 500) {
    errors.note = 'Notiz darf maximal 500 Zeichen lang sein'
    valid = false
  }

  return valid
}

async function submit() {
  if (!validate()) return

  let apiEventType = form.eventType
  if (apiEventType === 'ph_plus' || apiEventType === 'ph_minus') {
    apiEventType = 'ph'
  }

  const payload = {
    time: Math.floor(new Date(form.time).getTime() / 1000),
    name: form.name,
    eventType: apiEventType,
  }

  if (form.amount != null && form.unit !== '') {
    let amount = form.amount
    if (form.eventType === 'ph_minus') {
      amount = -amount
    }
    payload.amount = amount
    payload.unit = form.unit
  }

  if (form.note) {
    payload.note = form.note
  }

  const ok = await postEvent(payload)
  if (ok) {
    showToast('Ereignis gespeichert', 'success')
    resetForm()
  } else if (error.value === '401') {
    showToast('Unauthorized – check your token in settings', 'error')
  } else {
    showToast('Ereignis konnte nicht gesendet werden', 'error')
  }
}

initDateTime()
</script>

<template>
  <form @submit.prevent="submit" class="space-y-5">
    <h1 class="text-center text-2xl font-bold text-slate-800">Ereignis</h1>

    <div class="grid grid-cols-1 gap-x-4 md:grid-cols-2">
      <div class="space-y-1">
        <label class="block text-sm font-medium text-slate-600">Datum/Uhrzeit</label>
        <input
          v-model="form.time"
          type="datetime-local"
          class="w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        />
        <p v-if="errors.time" class="text-sm text-error">{{ errors.time }}</p>
      </div>

      <div class="space-y-1">
        <label class="block text-sm font-medium text-slate-600">Pool</label>
        <select
          v-model="form.name"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="" disabled>Bitte auswaehlen</option>
          <option v-for="pool in pools" :key="pool.name" :value="pool.name">
            {{ pool.name }}
          </option>
        </select>
        <p v-if="errors.name" class="text-sm text-error">{{ errors.name }}</p>
      </div>
    </div>

    <div class="space-y-1">
      <label class="block text-sm font-medium text-slate-600">Ereignis</label>
      <select
        v-model="form.eventType"
        class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
      >
        <option v-for="opt in eventOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </div>

    <div class="space-y-1">
      <label class="block text-sm font-medium text-slate-600">Menge (optional)</label>
      <div class="grid grid-cols-[1fr_6.5rem] items-center gap-3">
        <ValueSliderInput
          v-model="form.amount"
          v-bind="AMOUNT_CONFIG"
        />
        <select
          v-model="form.unit"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="tabs">Tabs</option>
          <option value="g">g</option>
          <option value="kg">kg</option>
          <option value="l">l</option>
          <option value="min">Min.</option>
        </select>
      </div>
      <p v-if="errors.amount" class="text-sm text-error">{{ errors.amount }}</p>
    </div>

    <div class="space-y-1">
      <button
        type="button"
        @click="showNote = !showNote"
        class="flex w-full items-center justify-between text-sm font-medium text-slate-600 hover:text-slate-800"
      >
        <span>Notiz</span>
        <svg
          class="h-4 w-4 transition-transform"
          :class="{ 'rotate-180': showNote }"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <div v-if="showNote" class="mt-1">
        <textarea
          v-model="form.note"
          rows="2"
          maxlength="500"
          placeholder="Notiz hinzufuegen..."
          class="w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary resize-none"
        ></textarea>
        <p v-if="errors.note" class="text-sm text-error">{{ errors.note }}</p>
      </div>
    </div>

    <button
      type="submit"
      :disabled="loading"
      class="w-full rounded-lg bg-primary py-3 text-lg font-semibold text-white disabled:opacity-50 active:bg-primary/80"
    >
      {{ loading ? 'Sende...' : 'SEND' }}
    </button>
  </form>
</template>
