<script setup>
import { ref } from 'vue'
import MeasurementForm from './components/MeasurementForm.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import { useToast } from './composables/useToast.js'

const view = ref('form')
const { toast } = useToast()
</script>

<template>
  <div class="flex min-h-svh items-center justify-center bg-slate-50 p-4">
    <div class="relative w-full max-w-sm overflow-hidden rounded-2xl bg-white shadow-lg">
      <div class="bg-primary px-6 py-4 text-center">
        <h1 class="text-2xl font-bold text-white">Pool Monitor</h1>
      </div>
      <div class="p-6">
        <MeasurementForm v-if="view === 'form'" @open-settings="view = 'settings'" />
        <SettingsPanel v-else @close="view = 'form'" />
      </div>
    </div>

    <Transition name="toast">
      <div
        v-if="toast.visible"
        class="fixed top-6 left-1/2 -translate-x-1/2 rounded-lg px-5 py-3 text-sm font-medium text-white shadow-lg"
        :class="{
          'bg-success': toast.type === 'success',
          'bg-error': toast.type === 'error',
          'bg-warning': toast.type === 'warning',
        }"
      >
        {{ toast.message }}
      </div>
    </Transition>
  </div>
</template>

<style>
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(1rem);
}
</style>
