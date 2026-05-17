<script setup>
import { useSettings } from '../composables/useSettings.js'

const emit = defineEmits(['close'])

const { settings } = useSettings()
const APP_VERSION = '1.0.0'
</script>

<template>
  <div class="relative space-y-5">
    <button
      type="button"
      @click="emit('close')"
      class="absolute -right-1 -top-1 flex size-11 items-center justify-center rounded-lg text-primary hover:bg-primary/10 text-xl font-bold">✕</button>


    <h1 class="text-center text-2xl font-bold text-slate-800">Settings</h1>

    <div class="space-y-4">
      <div class="space-y-1">
        <label class="block text-sm font-medium text-slate-600">Backend URL</label>
        <input
          v-model="settings.backendUrl"
          type="text"
          placeholder="/api"
          class="w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        />
      </div>

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

    <p class="text-center text-xs text-slate-400">Version {{ APP_VERSION }}</p>
  </div>
</template>
