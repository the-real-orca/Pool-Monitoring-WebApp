<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import LiveView from './components/LiveView.vue'
import MeasurementForm from './components/MeasurementForm.vue'
import EventForm from './components/EventForm.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import { useToast } from './composables/useToast.js'

const view = ref('live')
const previousView = ref('live')
const menuOpen = ref(false)
const menuRef = ref(null)
const { toast } = useToast()

const navigationEntries = [
  { label: 'Dashboard', view: 'live' },
  { label: 'Messungen', view: 'form' },
  { label: 'Ereignisse', view: 'event' },
]

function showView(nextView) {
  view.value = nextView
  menuOpen.value = false
}

function openSettings() {
  previousView.value = view.value === 'settings' ? previousView.value : view.value
  view.value = 'settings'
  menuOpen.value = false
}

function closeSettings() {
  view.value = previousView.value
}

function toggleMenu() {
  menuOpen.value = !menuOpen.value
}

function onDocumentClick(event) {
  if (menuOpen.value && menuRef.value && !menuRef.value.contains(event.target)) {
    menuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('mousedown', onDocumentClick)
  document.addEventListener('touchstart', onDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onDocumentClick)
  document.removeEventListener('touchstart', onDocumentClick)
})
</script>

<template>
  <div class="flex min-h-svh items-center justify-center bg-slate-50 p-4">
    <div class="relative w-full max-w-sm overflow-hidden rounded-2xl bg-white shadow-lg md:max-w-2xl">
      <div class="relative bg-primary px-6 py-4 text-center">
        <div v-if="view !== 'settings'" ref="menuRef" class="absolute left-4 top-4">
          <button
            type="button"
            @click="toggleMenu"
            class="flex size-11 items-center justify-center rounded-lg text-white hover:bg-white/20"
            aria-label="Navigation öffnen"
            :aria-expanded="menuOpen"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <Transition name="menu">
            <div
              v-if="menuOpen"
              class="absolute left-0 top-12 z-30 w-56 overflow-hidden rounded-xl bg-white py-2 text-left shadow-2xl ring-1 ring-slate-200"
            >
              <button
                v-for="entry in navigationEntries"
                :key="entry.view"
                type="button"
                @click="showView(entry.view)"
                class="flex w-full items-center justify-between px-4 py-3 text-sm font-medium transition-colors"
                :class="view === entry.view ? 'bg-slate-100 text-primary' : 'text-slate-700 hover:bg-slate-50'"
              >
                <span>{{ entry.label }}</span>
                <span v-if="view === entry.view" class="text-xs font-semibold">aktiv</span>
              </button>
              <div class="my-1 border-t border-slate-200"></div>
              <button
                type="button"
                @click="openSettings"
                class="flex w-full items-center px-4 py-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
              >
                Einstellungen
              </button>
            </div>
          </Transition>
        </div>

        <h1 class="text-2xl font-bold text-white">Pool Monitor</h1>
        <button
          v-if="view !== 'settings'"
          type="button"
          @click="openSettings"
          class="absolute right-4 top-4 flex size-11 items-center justify-center rounded-lg text-white hover:bg-white/20"
          aria-label="Einstellungen öffnen"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="size-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.773c-.309.238-.48.617-.48 1.014v.292c0 .397.171.776.48 1.014l1.003.773a1.125 1.125 0 0 1 .26 1.431l-1.296 2.247a1.125 1.125 0 0 1-1.37.49l-1.217-.456a1.125 1.125 0 0 0-1.075.124c-.073.044-.146.087-.22.127-.332.184-.582.496-.645.87l-.213 1.281c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.063-.374-.313-.686-.645-.87a13.29 13.29 0 0 0-.22-.127 1.125 1.125 0 0 0-1.075-.124l-1.217.456a1.125 1.125 0 0 1-1.37-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.003-.773c.309-.238.48-.617.48-1.014v-.292c0-.397-.171-.776-.48-1.014l-1.003-.773a1.125 1.125 0 0 1-.26-1.431l1.297-2.247a1.125 1.125 0 0 1 1.37-.49l1.216.456a1.125 1.125 0 0 0 1.075-.124c.073-.044.146-.087.22-.127.332-.184.582-.496.645-.87l.213-1.28Z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
          </svg>
        </button>
      </div>
      <div class="p-6">
        <div v-show="view !== 'settings'">
          <div v-show="view === 'live'">
            <LiveView />
          </div>
          <div v-show="view === 'form'">
            <MeasurementForm />
          </div>
          <div v-show="view === 'event'">
            <EventForm />
          </div>
        </div>
        <SettingsPanel v-if="view === 'settings'" @close="closeSettings" />
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

.menu-enter-active,
.menu-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}

.menu-enter-from,
.menu-leave-to {
  opacity: 0;
  transform: translateY(-0.25rem);
}
</style>
