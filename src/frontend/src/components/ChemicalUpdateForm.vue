<script setup>
import { computed, reactive, ref, onMounted, watch } from 'vue'
import { useApi } from '../composables/useApi.js'
import { useToast } from '../composables/useToast.js'
import ValueSliderInput from './ValueSliderInput.vue'

const { postChemicalUpdate, fetchPools, loading, error } = useApi()
const { show: showToast } = useToast()

const chemicalOptions = [
  { label: 'Chlor', value: 'chlorine' },
  { label: 'pH-Plus', value: 'ph_plus' },
  { label: 'pH-Minus', value: 'ph_minus' },
  { label: 'Flockungsmittel', value: 'flocculant' },
]

const amountStep = computed(() => form.amount != null && Math.abs(form.amount) < 1 ? 0.1 : 1.0)
const AMOUNT_CONFIG = computed(() => ({
  min: 0.0,
  max: 100.0,
  step: amountStep.value,
  decimals: 1,
  unit: '',
  emptyValue: Math.abs(form.amount ?? 0) < 1 ? 0.1 : 1.0,
}))

const pools = ref([])

const form = reactive({
  time: '',
  name: localStorage.getItem('lastPoolName') || '',
  chemicalType: 'chlorine',
  amount: null,
  unit: '',
})

const errors = reactive({})

watch(() => form.name, (newName) => {
  if (newName) localStorage.setItem('lastPoolName', newName)
})

watch(() => form.amount, (newAmount) => {
  if (newAmount === 0) {
    form.amount = null
    form.unit = ''
    delete errors.amount
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
  form.chemicalType = 'chlorine'
  form.amount = null
  form.unit = ''
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

  const hasAmount = form.amount != null
  const hasUnit = form.unit !== ''

  if (hasAmount !== hasUnit) {
    errors.amount = 'Menge und Einheit muessen zusammen gesetzt werden'
    valid = false
  }

  if (hasAmount) {
    if (Number.isNaN(form.amount) || form.amount <= 0) {
      errors.amount = 'Menge muss groesser als 0 sein'
      valid = false
    }
  }

  return valid
}

async function submit() {
  if (!validate()) return

  let apiChemicalType = form.chemicalType
  if (apiChemicalType === 'ph_plus' || apiChemicalType === 'ph_minus') {
    apiChemicalType = 'ph'
  }

  const payload = {
    time: Math.floor(new Date(form.time).getTime() / 1000),
    name: form.name,
    chemicalType: apiChemicalType,
  }

  if (form.amount != null && form.unit !== '') {
    let amount = form.amount
    if (form.chemicalType === 'ph_minus') {
      amount = -amount
    }
    payload.amount = amount
    payload.unit = form.unit
  }

  const ok = await postChemicalUpdate(payload)
  if (ok) {
    showToast('Chemieeintrag gespeichert', 'success')
    resetForm()
  } else if (error.value === '401') {
    showToast('Unauthorized – check your token in settings', 'error')
  } else {
    showToast('Chemieeintrag konnte nicht gesendet werden', 'error')
  }
}

initDateTime()
</script>

<template>
  <form @submit.prevent="submit" class="space-y-5">
    <h1 class="text-center text-2xl font-bold text-slate-800">Chemieupdate</h1>

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

    <div class="space-y-1">
      <label class="block text-sm font-medium text-slate-600">Chemikalie</label>
      <select
        v-model="form.chemicalType"
        class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
      >
        <option v-for="opt in chemicalOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </div>

    <div class="space-y-1">
      <div class="flex items-center justify-between">
        <label class="block text-sm font-medium text-slate-600">Menge</label>
        <span class="text-xs text-slate-400">optional</span>
      </div>
      <div class="grid grid-cols-[1fr_6.5rem] items-center gap-3">
        <ValueSliderInput
          v-model="form.amount"
          v-bind="AMOUNT_CONFIG"
        />
        <select
          v-model="form.unit"
          class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-800 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">Einheit</option>
          <option value="ml">ml</option>
          <option value="g">g</option>
          <option value="tabs">Tabs</option>
          <option value="l">l</option>
        </select>
      </div>
      <p v-if="errors.amount" class="text-sm text-error">{{ errors.amount }}</p>
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
