<script setup>
import { ref, onMounted } from 'vue'
import { compress } from '../composables/useImage.js'
import { useApi } from '../composables/useApi.js'
import { useToast } from '../composables/useToast.js'

const props = defineProps({
  mode: { type: String, default: 'camera' }
})

const emit = defineEmits(['applied', 'close'])

const { loading, error, analyzeImage } = useApi()
const { show: showToast } = useToast()
const localError = ref(null)
const cameraInput = ref(null)
const fileInput = ref(null)

onMounted(() => {
  if (props.mode === 'camera') {
    cameraInput.value?.click()
  } else {
    fileInput.value?.click()
  }
})

async function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  localError.value = null
  try {
    const compressed = await compress(file, { maxEdge: 1920, quality: 0.8 })
    const result = await analyzeImage(compressed)
    if (result) {
      if (result.ph === -1 || result.cl === -1) {
        const parts = []
        if (result.ph === -1) parts.push('pH')
        if (result.cl === -1) parts.push('Cl')
        localError.value = `AI could not reliably read: ${parts.join(', ')}`
        return
      }
      if (result.warnings?.length) {
        showToast(result.warnings.join('; '), 'warning', 5000)
      }
      emit('applied', { pH: result.ph, cl: result.cl, image: result.image })
    } else if (error.value === '401') {
      localError.value = 'Unauthorized – check your token'
    } else if (error.value === '422') {
      localError.value = 'AI could not analyze the image'
    } else if (error.value === '429') {
      localError.value = 'Daily image-analysis limit reached'
    } else if (error.value) {
      localError.value = `Error ${error.value}`
    } else {
      localError.value = 'Network error'
    }
  } catch {
    localError.value = 'Could not read image file'
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
    <div class="relative w-full max-w-sm rounded-2xl bg-white p-6">
      <input
        ref="cameraInput"
        type="file"
        accept="image/*"
        capture="environment"
        class="hidden"
        @change="onFileChange"
      />
      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        class="hidden"
        @change="onFileChange"
      />

      <div v-if="loading" class="flex items-center justify-center gap-2 rounded-lg bg-slate-100 py-4 text-slate-600">
        <svg class="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
        Analyzing image…
      </div>

      <div v-if="localError" class="rounded-lg bg-error/10 px-4 py-3 text-sm text-error">
        {{ localError }}
      </div>

      <button
        type="button"
        @click="emit('close')"
        class="mt-4 w-full rounded-lg border border-slate-300 py-2.5 text-slate-600 hover:bg-slate-100"
      >Abbrechen</button>
    </div>
  </div>
</template>
