import { ref } from 'vue'
import { useSettings } from './useSettings.js'

export function useApi() {
  const { settings } = useSettings()
  const loading = ref(false)
  const error = ref(null)

  async function fetchPools() {
    try {
      const res = await fetch(`/api/pools`, {
        headers: { 'Authorization': `Bearer ${settings.token}` }
      })
      if (!res.ok) return []
      return await res.json()
    } catch {
      return []
    }
  }

  async function postMeasurement(form) {
    loading.value = true
    error.value = null
    const payload = {
      time:       Math.floor(Date.now() / 1000),
      name:       form.name,
      sensorType: 'manual',
      pH:         form.pH,
      cl:         form.cl,
      temp:       form.temp,
    }
    if (form.status) {
      payload.status = form.status
    }
    try {
      const res = await fetch(`/api/measurements`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${settings.token}`,
        },
        body: JSON.stringify(payload),
      })
      if (res.status === 401) { error.value = '401'; return false }
      if (!res.ok) { error.value = String(res.status); return false }
      return true
    } catch {
      error.value = 'network'
      return false
    } finally {
      loading.value = false
    }
  }

  return { loading, error, postMeasurement, fetchPools }
}
