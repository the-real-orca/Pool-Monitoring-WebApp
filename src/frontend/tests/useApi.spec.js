import { describe, it, expect, vi, beforeEach } from 'vitest'

const KEY = 'pool_monitor_settings'

function saveSettings(s) {
  localStorage.setItem(KEY, JSON.stringify({ ...s, token: btoa(s.token) }))
}

describe('analyzeImage', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    saveSettings({ token: 'test-token' })
    vi.stubGlobal('fetch', vi.fn())
  })

  it('builds FormData and sets Authorization header', async () => {
    fetch.mockResolvedValue({
      status: 200,
      ok: true,
      json: () => Promise.resolve({ ph: 7.2, cl: 1.5, requestsRemainingToday: 9 }),
    })

    const { useApi } = await import('../src/composables/useApi.js')
    const { analyzeImage } = useApi()
    const file = new File(['data'], 'test.jpg', { type: 'image/jpeg' })
    const result = await analyzeImage(file)

    expect(fetch).toHaveBeenCalledWith('/api/analyze-image', expect.objectContaining({
      method: 'POST',
      headers: { 'Authorization': 'Bearer test-token' },
      body: expect.any(FormData),
    }))

    const body = fetch.mock.calls[0][1].body
    expect(body.get('image')).toBe(file)
    expect(result).toEqual({ ph: 7.2, cl: 1.5, requestsRemainingToday: 9 })
  })

  it('returns null and sets error for 401', async () => {
    fetch.mockResolvedValue({ status: 401, ok: false })

    const { useApi } = await import('../src/composables/useApi.js')
    const { analyzeImage, error } = useApi()
    const file = new File(['data'], 'test.jpg', { type: 'image/jpeg' })
    const result = await analyzeImage(file)

    expect(result).toBeNull()
    expect(error.value).toBe('401')
  })

  it('returns null and sets error for 422', async () => {
    fetch.mockResolvedValue({ status: 422, ok: false })

    const { useApi } = await import('../src/composables/useApi.js')
    const { analyzeImage, error } = useApi()
    const file = new File(['data'], 'test.jpg', { type: 'image/jpeg' })
    const result = await analyzeImage(file)

    expect(result).toBeNull()
    expect(error.value).toBe('422')
  })

  it('returns null and sets error for 429', async () => {
    fetch.mockResolvedValue({ status: 429, ok: false })

    const { useApi } = await import('../src/composables/useApi.js')
    const { analyzeImage, error } = useApi()
    const file = new File(['data'], 'test.jpg', { type: 'image/jpeg' })
    const result = await analyzeImage(file)

    expect(result).toBeNull()
    expect(error.value).toBe('429')
  })

  it('returns null and sets error for 5xx', async () => {
    fetch.mockResolvedValue({ status: 503, ok: false })

    const { useApi } = await import('../src/composables/useApi.js')
    const { analyzeImage, error } = useApi()
    const file = new File(['data'], 'test.jpg', { type: 'image/jpeg' })
    const result = await analyzeImage(file)

    expect(result).toBeNull()
    expect(error.value).toBe('503')
  })

  it('returns null and sets error for network failure', async () => {
    fetch.mockRejectedValue(new Error('Network error'))

    const { useApi } = await import('../src/composables/useApi.js')
    const { analyzeImage, error } = useApi()
    const file = new File(['data'], 'test.jpg', { type: 'image/jpeg' })
    const result = await analyzeImage(file)

    expect(result).toBeNull()
    expect(error.value).toBe('network')
  })

  it('does not set Content-Type header', async () => {
    fetch.mockResolvedValue({
      status: 200,
      ok: true,
      json: () => Promise.resolve({ ph: 7.2, cl: 1.5, requestsRemainingToday: 9 }),
    })

    const { useApi } = await import('../src/composables/useApi.js')
    const { analyzeImage } = useApi()
    const file = new File(['data'], 'test.jpg', { type: 'image/jpeg' })
    await analyzeImage(file)

    const headers = fetch.mock.calls[0][1].headers
    expect(headers).toEqual({ 'Authorization': 'Bearer test-token' })
    expect(headers['Content-Type']).toBeUndefined()
  })
})

describe('postMeasurement', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    saveSettings({ token: 'test-token' })
    vi.stubGlobal('fetch', vi.fn())
  })

  it('uses provided timestamp and manual sensor type', async () => {
    fetch.mockResolvedValue({ status: 201, ok: true })

    const { useApi } = await import('../src/composables/useApi.js')
    const { postMeasurement } = useApi()
    const ok = await postMeasurement({
      time: 1755724982,
      name: 'Pool',
      pH: 7.2,
      cl: 1.0,
      temp: 24.6,
      status: 'Cloudy',
      aiPH: 7.3,
      aiCL: 1.5,
      aiImage: '2026-05-29/123456_abc.jpg',
      aiCorrected: true,
    })

    expect(ok).toBe(true)
    expect(fetch).toHaveBeenCalledWith('/api/measurements', expect.objectContaining({
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token',
      },
    }))

    const payload = JSON.parse(fetch.mock.calls[0][1].body)
    expect(payload).toEqual({
      time: 1755724982,
      name: 'Pool',
      sensorType: 'manual',
      pH: 7.2,
      cl: 1.0,
      temp: 24.6,
      status: 'Cloudy',
      aiPH: 7.3,
      aiCL: 1.5,
      aiImage: '2026-05-29/123456_abc.jpg',
      aiCorrected: true,
    })
  })
})

describe('postChemicalUpdate', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    saveSettings({ token: 'test-token' })
    vi.stubGlobal('fetch', vi.fn())
  })

  it('posts chemical updates with amount and unit', async () => {
    fetch.mockResolvedValue({ status: 201, ok: true })

    const { useApi } = await import('../src/composables/useApi.js')
    const { postChemicalUpdate } = useApi()
    const ok = await postChemicalUpdate({
      time: 1755724982,
      name: 'Pool',
      chemicalType: 'chlorine',
      amount: 250.0,
      unit: 'ml',
    })

    expect(ok).toBe(true)
    expect(fetch).toHaveBeenCalledWith('/api/chem', expect.objectContaining({
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token',
      },
    }))

    const payload = JSON.parse(fetch.mock.calls[0][1].body)
    expect(payload).toEqual({
      time: 1755724982,
      name: 'Pool',
      chemicalType: 'chlorine',
      amount: 250,
      unit: 'ml',
    })
  })

  it('omits optional amount and unit when absent', async () => {
    fetch.mockResolvedValue({ status: 201, ok: true })

    const { useApi } = await import('../src/composables/useApi.js')
    const { postChemicalUpdate } = useApi()
    await postChemicalUpdate({
      time: 1755724982,
      name: 'Pool',
      chemicalType: 'ph',
    })

    const payload = JSON.parse(fetch.mock.calls[0][1].body)
    expect(payload).toEqual({
      time: 1755724982,
      name: 'Pool',
      chemicalType: 'ph',
    })
  })

  it('returns false and sets error for unauthorized requests', async () => {
    fetch.mockResolvedValue({ status: 401, ok: false })

    const { useApi } = await import('../src/composables/useApi.js')
    const { postChemicalUpdate, error } = useApi()
    const ok = await postChemicalUpdate({
      time: 1755724982,
      name: 'Pool',
      chemicalType: 'ph',
    })

    expect(ok).toBe(false)
    expect(error.value).toBe('401')
  })
})

// --- Live Data API (Phase 20) ----------------------------------------------

describe('fetchPoolsLive', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    saveSettings({ token: 'test-token' })
    vi.stubGlobal('fetch', vi.fn())
  })

  it('returns pool list on 200', async () => {
    fetch.mockResolvedValue({
      status: 200, ok: true, json: () => Promise.resolve([{ name: 'Pool', hasData: true }])
    })
    const { useApi } = await import('../src/composables/useApi.js')
    const { fetchPoolsLive } = useApi()
    const out = await fetchPoolsLive()
    expect(out).toEqual([{ name: 'Pool', hasData: true }])
    expect(fetch).toHaveBeenCalledWith('/api/pools/live', expect.objectContaining({
      headers: { 'Authorization': 'Bearer test-token' }
    }))
  })

  it('returns null and sets error on 401', async () => {
    fetch.mockResolvedValue({ status: 401, ok: false, json: () => Promise.resolve({}) })
    const { useApi } = await import('../src/composables/useApi.js')
    const { fetchPoolsLive, error } = useApi()
    const out = await fetchPoolsLive()
    expect(out).toBeNull()
    expect(error.value).toBe('401')
  })

  it('returns null on network error', async () => {
    fetch.mockRejectedValue(new Error('boom'))
    const { useApi } = await import('../src/composables/useApi.js')
    const { fetchPoolsLive, error } = useApi()
    const out = await fetchPoolsLive()
    expect(out).toBeNull()
    expect(error.value).toBe('network')
  })
})

describe('fetchLive', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    saveSettings({ token: 'test-token' })
    vi.stubGlobal('fetch', vi.fn())
  })

  it('returns snapshot on 200', async () => {
    fetch.mockResolvedValue({
      status: 200, ok: true,
      json: () => Promise.resolve({ ts: 1, temp: 24.5, pH: 7.2, cl: 0.7, stale: false, staleSeconds: 5, pump: { main: { running: true, since: 1 }, solar: { running: null, since: null } } })
    })
    const { useApi } = await import('../src/composables/useApi.js')
    const { fetchLive } = useApi()
    const out = await fetchLive('Pool')
    expect(out.temp).toBe(24.5)
    expect(out.pump.main.running).toBe(true)
    expect(fetch.mock.calls[0][0]).toBe('/api/live?pool=Pool')
  })

  it('encodes special characters in pool name', async () => {
    fetch.mockResolvedValue({ status: 200, ok: true, json: () => Promise.resolve({}) })
    const { useApi } = await import('../src/composables/useApi.js')
    const { fetchLive } = useApi()
    await fetchLive('My Pool')
    expect(fetch.mock.calls[0][0]).toBe('/api/live?pool=My%20Pool')
  })

  it('returns null and sets error on 422', async () => {
    fetch.mockResolvedValue({ status: 422, ok: false, json: () => Promise.resolve({}) })
    const { useApi } = await import('../src/composables/useApi.js')
    const { fetchLive, error } = useApi()
    const out = await fetchLive('Unknown')
    expect(out).toBeNull()
    expect(error.value).toBe('422')
  })
})

describe('fetchHistory', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    saveSettings({ token: 'test-token' })
    vi.stubGlobal('fetch', vi.fn())
  })

  it('returns points on 200', async () => {
    fetch.mockResolvedValue({
      status: 200, ok: true,
      json: () => Promise.resolve({ pool: 'Pool', metric: 'temp', unit: '°C', points: [{ t: 1, v: 24.5 }] })
    })
    const { useApi } = await import('../src/composables/useApi.js')
    const { fetchHistory } = useApi()
    const out = await fetchHistory('Pool', 'temp', 7)
    expect(out.points).toEqual([{ t: 1, v: 24.5 }])
    expect(fetch.mock.calls[0][0]).toBe('/api/history?pool=Pool&metric=temp&days=7')
  })

  it('handles 422 on bad metric', async () => {
    fetch.mockResolvedValue({ status: 422, ok: false, json: () => Promise.resolve({}) })
    const { useApi } = await import('../src/composables/useApi.js')
    const { fetchHistory, error } = useApi()
    const out = await fetchHistory('Pool', 'humidity')
    expect(out).toBeNull()
    expect(error.value).toBe('422')
  })
})

describe('fetchPumpEvents', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    saveSettings({ token: 'test-token' })
    vi.stubGlobal('fetch', vi.fn())
  })

  it('returns events on 200', async () => {
    fetch.mockResolvedValue({
      status: 200, ok: true,
      json: () => Promise.resolve({ pool: 'Pool', events: [{ id: 1, pump: 'main', state: true, time: 1, receivedAt: 1 }] })
    })
    const { useApi } = await import('../src/composables/useApi.js')
    const { fetchPumpEvents } = useApi()
    const out = await fetchPumpEvents('Pool', 7)
    expect(out.events).toHaveLength(1)
    expect(fetch.mock.calls[0][0]).toBe('/api/pump-events?pool=Pool&days=7')
  })
})

