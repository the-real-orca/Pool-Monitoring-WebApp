<script setup>
import { ref } from 'vue'
import { compress } from '../composables/useImage.js'
import { useApi } from '../composables/useApi.js'

const emit = defineEmits(['applied', 'close'])

const { loading, error, analyzeImage } = useApi()
const previewUrl = ref(null)
const localError = ref(null)
const errorKey = ref(0)

async function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  localError.value = null
  previewUrl.value = URL.createObjectURL(file)
  try {
    const compressed = await compress(file, { maxEdge: 1920, quality: 0.8 })
    const result = await analyzeImage(compressed)
    if (result) {
      emit('applied', { pH: result.ph, cl: result.cl, time: result.time })
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
  } finally {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = null
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
    <div class="relative w-full max-w-sm rounded-2xl bg-white p-6">
      <h2 class="mb-4 text-lg font-bold text-slate-800">Analyze Photo</h2>

      <input
        :key="errorKey"
        type="file"
        accept="image/*"
        capture="environment"
        @change="onFileChange"
        class="block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-primary file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white hover:file:bg-primary/90"
      />

      <div v-if="loading" class="mt-4 flex items-center justify-center gap-2 rounded-lg bg-slate-100 py-4 text-slate-600">
        <svg class="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
        Analyzing image…
      </div>

      <div v-if="localError" class="mt-4 rounded-lg bg-error/10 px-4 py-3 text-sm text-error">
        {{ localError }}
      </div>

      <button
        type="button"
        @click="emit('close')"
        class="mt-4 w-full rounded-lg border border-slate-300 py-2.5 text-slate-600 hover:bg-slate-100"
      >Cancel</button>
    </div>
  </div>
</template>
