<script setup>
import { reactive, watch } from 'vue'
import { useSettings } from '../composables/useSettings.js'
import { useToast } from '../composables/useToast.js'

const emit = defineEmits(['close'])

const { settings } = useSettings()
const { show: showToast } = useToast()
const APP_VERSION = '1.0.0'

const original = reactive({ ...settings })

const cancel = () => {
  Object.assign(settings, original)
  emit('close')
}

const save = () => {
  showToast('Einstellungen gespeichert', 'success')
  Object.assign(original, settings)
  emit('close')
}
</script>

<template>
  <div class="relative space-y-5">
    <h1 class="text-center text-2xl font-bold text-slate-800">Settings</h1>

    <div class="space-y-4">
      <div class="space-y-1">
        <label class="block text-sm font-medium text-slate-600">API Token</label>
        <input
          v-model="settings.token"
          type="password"
          placeholder="Bearer token"
          class="w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        />
      </div>

      <div class="space-y-1">
        <label class="block text-sm font-medium text-slate-600">Pool Name</label>
        <input
          v-model="settings.poolName"
          type="text"
          placeholder="Pool"
          class="w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        />
      </div>
    </div>

    <div class="flex gap-3 pt-2">
      <button
        type="button"
        @click="cancel"
        class="flex-1 rounded-lg border border-slate-300 py-2.5 text-slate-600 hover:bg-slate-100 font-medium"
      >Abbrechen</button>
      <button
        type="button"
        @click="save"
        class="flex-1 rounded-lg bg-primary py-2.5 text-white font-medium hover:bg-primary/90"
      >Speichern</button>
    </div>

    <p class="text-center text-xs text-slate-400">Version {{ APP_VERSION }}</p>
  </div>
</template>
