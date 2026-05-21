<script setup>
import { reactive, ref, onMounted, watch } from 'vue'
import { FIELD_CONFIG } from '../validation.js'
import { useSettings } from '../composables/useSettings.js'
import { useApi } from '../composables/useApi.js'
import { useToast } from '../composables/useToast.js'
import StepperInput from './StepperInput.vue'

const emit = defineEmits(['open-settings'])

const { settings } = useSettings()
const { postMeasurement, fetchPools, loading, error } = useApi()
const { show: showToast } = useToast()

const pools = ref([])
const showStatus = ref(false)

const form = reactive({
  time: '',
  name: localStorage.getItem('lastPoolName') || '',
  temp: FIELD_CONFIG.temp.default,
  pH: FIELD_CONFIG.pH.default,
  cl: FIELD_CONFIG.cl.default,
  notes: '',
})

watch(() => form.name, (newName) => {
  if (newName) localStorage.setItem('lastPoolName', newName)
})

onMounted(async () => {
  pools.value = await fetchPools()
  if (pools.value.length && !form.name) {
    form.name = pools.value[0].name
  }
})

const errors = reactive({})

function resetForm() {
  form.status = ''
  Object.keys(errors).forEach(k => delete errors[k])
  initDateTime()
}

function validate() {
  Object.keys(errors).forEach(k => delete errors[k])
  let valid = true

  if (!form.name || form.name.length < 1 || form.name.length > 50) {
    errors.name = 'Please select a pool'
    valid = false
  }

  if (form.status && form.status.length > 500) {
    errors.status = 'Status must be max 500 characters'
    valid = false
  }

  if (!form.time) {
    errors.time = 'Date/Time is required'
    valid = false
  }

  return valid
}

async function submit() {
  if (!validate()) return

  const timestamp = Math.floor(new Date(form.time).getTime() / 1000)
  const ok = await postMeasurement({ ...form, time: timestamp })
  if (ok) {
    showToast('Measurement saved', 'success')
    resetForm()
  } else if (error.value === '401') {
    showToast('Unauthorized – check your token in settings', 'error')
  } else {
    showToast('Failed to send measurement', 'error')
  }
}

function initDateTime() {
  const now = new Date()
  const offset = now.getTimezoneOffset()
  const local = new Date(now.getTime() - offset * 60000)
  form.time = local.toISOString().slice(0, 16)
}

initDateTime()
</script>

<template>
  <form @submit.prevent="submit" class="space-y-5">

    <h1 class="text-center text-2xl font-bold text-slate-800">Measurements</h1>

    <div class="space-y-1">
      <label class="block text-sm font-medium text-slate-600">Date/Time</label>
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
        class="w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary bg-white"
      >
        <option value="" disabled>Please select</option>
        <option v-for="pool in pools" :key="pool.name" :value="pool.name">
          {{ pool.name }}
        </option>
      </select>
      <p v-if="errors.name" class="text-sm text-error">{{ errors.name }}</p>
    </div>

    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-slate-600">Temperature</label>
        <div class="flex justify-center mt-1">
          <StepperInput
            v-model="form.temp"
            v-bind="FIELD_CONFIG.temp"
          />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-600">pH Value</label>
        <div class="flex justify-center mt-1">
          <StepperInput
            v-model="form.pH"
            v-bind="FIELD_CONFIG.pH"
          />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-600">Chlorine</label>
        <div class="flex justify-center mt-1">
<StepperInput
            v-model="form.cl"
            v-bind="FIELD_CONFIG.cl"
          />
        </div>
      </div>
    </div>

    <div class="space-y-1">
      <button
        type="button"
        @click="showStatus = !showStatus"
        class="flex w-full items-center justify-between text-sm font-medium text-slate-600 hover:text-slate-800"
      >
        <span>Notes / Status</span>
        <svg
          class="h-4 w-4 transition-transform"
          :class="{ 'rotate-180': showNotes }"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <div v-if="showStatus" class="mt-1">
        <textarea
          v-model="form.status"
          rows="2"
          maxlength="500"
          placeholder="Enter status..."
          class="w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary resize-none"
        ></textarea>
        <p v-if="errors.status" class="text-sm text-error">{{ errors.status }}</p>
      </div>
    </div>

    <div class="space-y-1">
      <button
        type="submit"
        :disabled="loading"
        class="w-full rounded-lg bg-primary py-3 text-lg font-semibold text-white disabled:opacity-50 active:bg-primary/80"
      >
        {{ loading ? 'Sending...' : 'SEND' }}
      </button>
    </div>

  </form>

  <button
    type="button"
    @click="emit('open-settings')"
    class="absolute right-4 top-2 flex size-11 items-center justify-center rounded-lg text-white hover:bg-white/20"
  >
    <svg xmlns="http://www.w3.org/2000/svg" class="size-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.773c-.309.238-.48.617-.48 1.014v.292c0 .397.171.776.48 1.014l1.003.773a1.125 1.125 0 0 1 .26 1.431l-1.296 2.247a1.125 1.125 0 0 1-1.37.49l-1.217-.456a1.125 1.125 0 0 0-1.075.124c-.073.044-.146.087-.22.127-.332.184-.582.496-.645.87l-.213 1.281c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.063-.374-.313-.686-.645-.87a13.29 13.29 0 0 0-.22-.127 1.125 1.125 0 0 0-1.075-.124l-1.217.456a1.125 1.125 0 0 1-1.37-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.003-.773c.309-.238.48-.617.48-1.014v-.292c0-.397-.171-.776-.48-1.014l-1.003-.773a1.125 1.125 0 0 1-.26-1.431l1.297-2.247a1.125 1.125 0 0 1 1.37-.49l1.216.456a1.125 1.125 0 0 0 1.075-.124c.073-.044.146-.087.22-.127.332-.184.582-.496.645-.87l.213-1.28Z" />
      <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  </button>

</template>
