<script setup>
import { reactive, ref } from 'vue'
import { useSettings } from '../composables/useSettings.js'
import { useToast } from '../composables/useToast.js'

const emit = defineEmits(['close'])

const { settings } = useSettings()
const { show: showToast } = useToast()
const APP_VERSION = '2.0'

const original = reactive({ ...settings })
const tokenVisible = ref(false)

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
    <h1 class="text-center text-2xl font-bold text-slate-800">Einstellungen</h1>

    <div class="space-y-4">
      <div class="space-y-1">
        <label class="block text-sm font-medium text-slate-600">API Token</label>
        <div class="relative">
          <input
            v-model="settings.token"
            :type="tokenVisible ? 'text' : 'password'"
            placeholder="Bearer token"
            class="w-full rounded-lg border border-slate-300 px-3 py-2 pr-10 text-slate-800 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <button
            type="button"
            @click="tokenVisible = !tokenVisible"
            class="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
          >
            <svg v-if="tokenVisible" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
              <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l6.921 6.922c.05.062.105.118.168.167l6.91 6.911a1 1 0 001.414-1.414l-.303-.303a5.985 5.985 0 00-.653-.653l-.303-.303a1 1 0 00-1.414 1.414l.303.303A8.046 8.046 0 0010 16c-4.478 0-8.268-2.943-9.542-7a9.97 9.97 0 00.683-.683l.303-.303a1 1 0 00-.293-.707l-1.414 1.414a1 1 0 101.414 1.414l.303-.303c.17-.17.38-.323.627-.458A8.046 8.046 0 0010 14c4.478 0 8.268 2.943 9.542 7-.465 1.398-1.13 2.693-1.953 3.84a1 1 0 00-1.414-1.414c-.654-.908-1.19-1.874-1.635-2.87a8.046 8.046 0 01-8-8c.998-.002 1.996.12 2.948.358a1 1 0 00.949-1.664c-.548-.7-1.18-1.336-1.867-1.894a1 1 0 00-1.414 1.414c.495.402.902.862 1.213 1.373A8.046 8.046 0 0010 2c-4.478 0-8.268 2.943-9.542 7z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>
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
