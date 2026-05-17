import { describe, it, expect, beforeEach, vi } from 'vitest'

const KEY = 'pool_monitor_settings'
const DEFAULTS = { backendUrl: '/api', token: '', poolName: 'Pool' }

function load() {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? '{}')
    return { ...DEFAULTS, ...raw, token: raw.token ? atob(raw.token) : '' }
  } catch { return { ...DEFAULTS } }
}

function save(s) {
  localStorage.setItem(KEY, JSON.stringify({ ...s, token: btoa(s.token) }))
}

describe('useSettings', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('returns defaults when localStorage is empty', () => {
    const settings = load()
    expect(settings).toEqual(DEFAULTS)
  })

  it('saves and loads roundtrip', () => {
    const data = { backendUrl: 'http://test/api', token: 'secret', poolName: 'MyPool' }
    save(data)
    const loaded = load()
    expect(loaded.backendUrl).toBe('http://test/api')
    expect(loaded.token).toBe('secret')
    expect(loaded.poolName).toBe('MyPool')
  })

  it('encodes token with Base64 on save', () => {
    const data = { ...DEFAULTS, token: 'my-secret-token' }
    save(data)
    const raw = JSON.parse(localStorage.getItem(KEY))
    expect(raw.token).toBe(btoa('my-secret-token'))
  })

  it('decodes token with Base64 on load', () => {
    const raw = { ...DEFAULTS, token: btoa('encoded-token') }
    localStorage.setItem(KEY, JSON.stringify(raw))
    const loaded = load()
    expect(loaded.token).toBe('encoded-token')
  })

  it('handles missing token gracefully', () => {
    localStorage.setItem(KEY, JSON.stringify({ poolName: 'Test' }))
    const loaded = load()
    expect(loaded.token).toBe('')
    expect(loaded.poolName).toBe('Test')
  })

  it('handles corrupted localStorage data', () => {
    localStorage.setItem(KEY, 'not-json')
    const loaded = load()
    expect(loaded).toEqual(DEFAULTS)
  })
})
