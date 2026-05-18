import { reactive, watch } from 'vue'

const KEY = 'pool_monitor_settings'
const DEFAULTS = { token: '', poolName: 'Pool' }

function load() {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? '{}')
    return { ...DEFAULTS, ...raw, token: raw.token ? atob(raw.token) : '' }
  } catch { return { ...DEFAULTS } }
}

function save(s) {
  localStorage.setItem(KEY, JSON.stringify({ ...s, token: btoa(s.token) }))
}

const settings = reactive(load())
watch(settings, save, { deep: true })

export function useSettings() {
  return { settings }
}
