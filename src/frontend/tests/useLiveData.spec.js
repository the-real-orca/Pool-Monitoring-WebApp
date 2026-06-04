import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const KEY = 'pool_monitor_settings'

function saveSettings(s) {
  localStorage.setItem(KEY, JSON.stringify({ ...s, token: btoa(s.token) }))
}

function mockSnapshot(extra = {}) {
  return {
    ts: Math.floor(Date.now() / 1000),
    temp: 24.6, pH: 7.2, cl: 0.7,
    pump: { main: { running: true, since: 1 }, solar: { running: false, since: 2 } },
    stale: false, staleSeconds: 5,
    ...extra,
  }
}

describe('useLiveData', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    saveSettings({ token: 'test-token' })
    vi.stubGlobal('fetch', vi.fn())
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('fetches immediately on start and exposes the snapshot', async () => {
    fetch.mockResolvedValue({ status: 200, ok: true, json: () => Promise.resolve(mockSnapshot()) })

    const { useLiveData } = await import('../src/composables/useLiveData.js')
    const { snapshot, start, stop } = useLiveData()
    await start('Pool')
    expect(fetch).toHaveBeenCalledTimes(1)
    expect(snapshot.value.temp).toBe(24.6)
    stop()
  })

  it('polls again after the configured interval', async () => {
    fetch.mockResolvedValue({ status: 200, ok: true, json: () => Promise.resolve(mockSnapshot()) })

    const { useLiveData } = await import('../src/composables/useLiveData.js')
    const { start, stop } = useLiveData()
    await start('Pool', { intervalMs: 1000 })
    expect(fetch).toHaveBeenCalledTimes(1)
    await vi.advanceTimersByTimeAsync(1000)
    expect(fetch).toHaveBeenCalledTimes(2)
    await vi.advanceTimersByTimeAsync(1000)
    expect(fetch).toHaveBeenCalledTimes(3)
    stop()
  })

  it('stop() clears the interval and stops further fetches', async () => {
    fetch.mockResolvedValue({ status: 200, ok: true, json: () => Promise.resolve(mockSnapshot()) })

    const { useLiveData } = await import('../src/composables/useLiveData.js')
    const { start, stop } = useLiveData()
    await start('Pool', { intervalMs: 1000 })
    expect(fetch).toHaveBeenCalledTimes(1)
    stop()
    await vi.advanceTimersByTimeAsync(5000)
    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it('on fetch error the error is exposed and polling continues', async () => {
    fetch.mockResolvedValueOnce({ status: 200, ok: true, json: () => Promise.resolve(mockSnapshot()) })
    fetch.mockResolvedValueOnce({ status: 500, ok: false, json: () => Promise.resolve({}) })
    fetch.mockResolvedValueOnce({ status: 200, ok: true, json: () => Promise.resolve(mockSnapshot({ temp: 25.0 })) })

    const { useLiveData } = await import('../src/composables/useLiveData.js')
    const { snapshot, usingCached, start, stop } = useLiveData()
    await start('Pool', { intervalMs: 1000 })
    expect(snapshot.value.temp).toBe(24.6)
    expect(usingCached.value).toBe(false)
    await vi.advanceTimersByTimeAsync(1000)
    // Polling continues, snapshot kept from last good fetch
    expect(snapshot.value.temp).toBe(24.6)
    expect(usingCached.value).toBe(true)
    await vi.advanceTimersByTimeAsync(1000)
    expect(snapshot.value.temp).toBe(25.0)
    expect(usingCached.value).toBe(false)
    stop()
  })

  it('stale is true when the backend reports stale', async () => {
    fetch.mockResolvedValue({ status: 200, ok: true, json: () => Promise.resolve(mockSnapshot({ stale: true, staleSeconds: 999 })) })

    const { useLiveData } = await import('../src/composables/useLiveData.js')
    const { stale, start, stop } = useLiveData()
    await start('Pool')
    expect(stale.value).toBe(true)
    stop()
  })

  it('stale is true when no snapshot is present', async () => {
    const { useLiveData } = await import('../src/composables/useLiveData.js')
    const { stale } = useLiveData()
    expect(stale.value).toBe(true)
  })

  it('stale is false when snapshot is fresh and not cached', async () => {
    fetch.mockResolvedValue({ status: 200, ok: true, json: () => Promise.resolve(mockSnapshot({ stale: false })) })

    const { useLiveData } = await import('../src/composables/useLiveData.js')
    const { stale, start, stop } = useLiveData()
    await start('Pool')
    expect(stale.value).toBe(false)
    stop()
  })

  it('switching pool resets the snapshot and restarts polling', async () => {
    fetch.mockResolvedValue({ status: 200, ok: true, json: () => Promise.resolve(mockSnapshot()) })

    const { useLiveData } = await import('../src/composables/useLiveData.js')
    const { snapshot, pool, start, stop } = useLiveData()
    await start('PoolA')
    expect(pool.value).toBe('PoolA')
    await start('PoolB')
    expect(pool.value).toBe('PoolB')
    expect(fetch).toHaveBeenCalledWith('/api/live?pool=PoolB', expect.any(Object))
    stop()
  })

  it('start() recovers and remains functional after a network-level rejection (M3)', async () => {
    // M3 regression: an exception escaping _tick used to leave _running=true
    // and no interval, wedging the polling loop. The fix wraps _tick in
    // try/catch so start() can be called again.
    fetch.mockRejectedValueOnce(new Error('network down'))
    fetch.mockResolvedValue({ status: 200, ok: true, json: () => Promise.resolve(mockSnapshot()) })

    const { useLiveData } = await import('../src/composables/useLiveData.js')
    const { start, stop } = useLiveData()
    await start('Pool')
    // After the rejected fetch, start() must be callable again to re-arm
    // polling instead of being stuck.
    await start('Pool')
    expect(fetch).toHaveBeenCalledTimes(2)
    stop()
  })
})
