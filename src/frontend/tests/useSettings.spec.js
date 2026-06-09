import { describe, it, expect, beforeEach, vi } from 'vitest'
import { nextTick } from 'vue'

describe('useSettings', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetModules()
  })

  it('returns defaults when localStorage is empty', async () => {
    const { useSettings } = await import('../src/composables/useSettings.js')
    const { settings } = useSettings()
    expect(settings.token).toBe('')
  })

  it('persists token change to localStorage', async () => {
    const { useSettings } = await import('../src/composables/useSettings.js')
    const { settings } = useSettings()
    settings.token = 'secret'
    await nextTick()
    const raw = JSON.parse(localStorage.getItem('pool_monitor_settings'))
    expect(raw.token).toBe(btoa('secret'))
  })

  it('loads token from localStorage', async () => {
    localStorage.setItem('pool_monitor_settings', JSON.stringify({ token: btoa('encoded') }))
    const { useSettings } = await import('../src/composables/useSettings.js')
    const { settings } = useSettings()
    expect(settings.token).toBe('encoded')
  })

  it('handles missing token gracefully', async () => {
    localStorage.setItem('pool_monitor_settings', JSON.stringify({}))
    const { useSettings } = await import('../src/composables/useSettings.js')
    const { settings } = useSettings()
    expect(settings.token).toBe('')
  })

  it('handles corrupted localStorage data', async () => {
    localStorage.setItem('pool_monitor_settings', 'not-json')
    const { useSettings } = await import('../src/composables/useSettings.js')
    const { settings } = useSettings()
    expect(settings.token).toBe('')
  })
})
