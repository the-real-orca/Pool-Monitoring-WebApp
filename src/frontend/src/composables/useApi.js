import { ref } from 'vue'
import { useSettings } from './useSettings.js'

export function useApi() {
  const { settings } = useSettings()
  const loading = ref(false)
  const error = ref(null)

  function authHeaders(extra = {}) {
    return { 'Authorization': `Bearer ${settings.token}`, ...extra }
  }

  async function getJson(path) {
    const res = await fetch(path, { headers: authHeaders() })
    if (!res.ok) {
      const code = String(res.status)
      if (res.status === 401) error.value = '401'
      else if (res.status === 422) error.value = '422'
      else error.value = code
      return { __status: res.status, __data: null }
    }
    return { __status: res.status, __data: await res.json() }
  }

  async function fetchPools() {
    try {
      const res = await fetch(`/api/pools`, { headers: authHeaders() })
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
      time:       form.time,
      name:       form.name,
      sensorType: 'manual',
      pH:         form.pH,
      cl:         form.cl,
      temp:       form.temp,
    }
    if (form.status) payload.status = form.status
    if (form.aiPH != null) payload.aiPH = form.aiPH
    if (form.aiCL != null) payload.aiCL = form.aiCL
    if (form.aiImage) payload.aiImage = form.aiImage
    if (form.aiCorrected != null) payload.aiCorrected = form.aiCorrected
    try {
      const res = await fetch(`/api/measurements`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
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

  async function postChemicalUpdate(form) {
    loading.value = true
    error.value = null
    const payload = {
      time: form.time,
      name: form.name,
      chemicalType: form.chemicalType,
    }
    if (form.amount != null) payload.amount = form.amount
    if (form.unit) payload.unit = form.unit
    try {
      const res = await fetch(`/api/chem`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
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

  async function analyzeImage(file) {
    loading.value = true
    error.value = null
    const fd = new FormData()
    fd.append('image', file)
    try {
      const res = await fetch(`/api/analyze-image`, {
        method: 'POST',
        headers: authHeaders(),
        body: fd,
      })
      if (res.status === 401) { error.value = '401'; return null }
      if (res.status === 422) { error.value = '422'; return null }
      if (res.status === 429) { error.value = '429'; return null }
      if (!res.ok) { error.value = String(res.status); return null }
      return await res.json()
    } catch {
      error.value = 'network'
      return null
    } finally {
      loading.value = false
    }
  }

  // --- Live Data (Phase 20) -----------------------------------------------

  async function fetchPoolsLive() {
    error.value = null
    try {
      const { __status, __data } = await getJson('/api/pools/live')
      if (__status === 401) error.value = '401'
      if (__status === 422) error.value = '422'
      return __status === 200 ? __data : null
    } catch {
      error.value = 'network'
      return null
    }
  }

  async function fetchLive(pool) {
    error.value = null
    try {
      const { __status, __data } = await getJson(`/api/live?pool=${encodeURIComponent(pool)}`)
      if (__status === 401) error.value = '401'
      if (__status === 422) error.value = '422'
      return __status === 200 ? __data : null
    } catch {
      error.value = 'network'
      return null
    }
  }

  async function fetchHistory(pool, metric, days = 7) {
    error.value = null
    try {
      const { __status, __data } = await getJson(
        `/api/history?pool=${encodeURIComponent(pool)}&metric=${encodeURIComponent(metric)}&days=${days}`
      )
      if (__status === 401) error.value = '401'
      if (__status === 422) error.value = '422'
      return __status === 200 ? __data : null
    } catch {
      error.value = 'network'
      return null
    }
  }

  async function fetchPumpEvents(pool, days = 7) {
    error.value = null
    try {
      const { __status, __data } = await getJson(
        `/api/pump-events?pool=${encodeURIComponent(pool)}&days=${days}`
      )
      if (__status === 401) error.value = '401'
      if (__status === 422) error.value = '422'
      return __status === 200 ? __data : null
    } catch {
      error.value = 'network'
      return null
    }
  }

  return {
    loading, error,
    postMeasurement, postChemicalUpdate, fetchPools, analyzeImage,
    fetchPoolsLive, fetchLive, fetchHistory, fetchPumpEvents,
  }
}
