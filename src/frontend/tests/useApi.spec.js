import { describe, it, expect, vi, beforeEach } from 'vitest'

const KEY = 'pool_monitor_settings'

function saveSettings(s) {
  localStorage.setItem(KEY, JSON.stringify({ ...s, token: btoa(s.token) }))
}

describe('analyzeImage', () => {
  beforeEach(() => {
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
