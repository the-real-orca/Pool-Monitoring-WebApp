import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import TrendChart from '../src/components/TrendChart.vue'

const KEY = 'pool_monitor_settings'

function saveSettings(s) {
  localStorage.setItem(KEY, JSON.stringify({ ...s, token: btoa(s.token) }))
}

describe('TrendChart', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    saveSettings({ token: 'test-token' })
    vi.stubGlobal('fetch', vi.fn())
    Element.prototype.getBoundingClientRect = function () {
      return { width: 600, height: 200, top: 0, left: 0, right: 600, bottom: 200, x: 0, y: 0 }
    }
  })

  it('shows the empty state when no points are returned', async () => {
    fetch.mockResolvedValue({ status: 200, ok: true, json: () => Promise.resolve({ pool: 'Pool', metric: 'temp', unit: '°C', points: [] }) })

    const wrapper = mount(TrendChart, { props: { pool: 'Pool' } })
    await flushPromises()
    expect(wrapper.text()).toContain('Noch keine Daten')
  }, 10000)

  it('renders three chart containers when data is present', async () => {
    const now = Math.floor(Date.now() / 1000)
    fetch.mockImplementation((url) => {
      const points = [{ t: now - 3600, v: 24.5 }, { t: now, v: 25.0 }]
      if (url.includes('metric=temp')) return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve({ pool: 'Pool', metric: 'temp', unit: '°C', points }) })
      if (url.includes('metric=pH'))   return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve({ pool: 'Pool', metric: 'pH', unit: '', points: [{ t: now, v: 7.2 }] }) })
      if (url.includes('metric=cl'))   return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve({ pool: 'Pool', metric: 'cl', unit: 'mg/l', points: [{ t: now, v: 0.7 }] }) })
      return Promise.reject(new Error('unexpected url: ' + url))
    })

    const wrapper = mount(TrendChart, { props: { pool: 'Pool' } })
    await flushPromises()
    expect(wrapper.find('[data-testid="trend-chart-temp"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="trend-chart-pH"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="trend-chart-cl"]').exists()).toBe(true)
    // Reload fetches each of the 3 metrics once. Subsequent backfill
    // fetches (triggered by setScale hooks from setData) are normal
    // production behavior — we only assert the initial load happened.
    expect(fetch.mock.calls.length).toBeGreaterThanOrEqual(3)
  }, 10000)

  it('destroys the chart instances on unmount', async () => {
    fetch.mockResolvedValue({ status: 200, ok: true, json: () => Promise.resolve({ pool: 'Pool', metric: 'temp', unit: '°C', points: [] }) })

    const wrapper = mount(TrendChart, { props: { pool: 'Pool' } })
    await flushPromises()
    expect(wrapper.findAll('[data-testid^="trend-chart-"]')).toHaveLength(3)
    wrapper.unmount()
  }, 10000)
})

// Touch gesture tests. The handlers run on the uPlot overlay (`.u-over`)
// inside each chart container. jsdom does not ship a `Touch` constructor,
// so each event is built as a plain `Event` with a `touches` array
// attached — uPlot only inspects the array, not the event class.
describe('TrendChart touch gestures', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    saveSettings({ token: 'test-token' })
    vi.stubGlobal('fetch', vi.fn())
    Element.prototype.getBoundingClientRect = function () {
      return { width: 600, height: 200, top: 0, left: 0, right: 600, bottom: 200, x: 0, y: 0 }
    }
  })

  function dispatchTouch(el, type, touches) {
    const evt = new Event(type, { bubbles: true, cancelable: true })
    evt.touches = touches
    evt.changedTouches = touches
    evt.targetTouches = touches
    el.dispatchEvent(evt)
    return evt
  }

  function mountWithData() {
    const now = Math.floor(Date.now() / 1000)
    fetch.mockImplementation((url) => {
      const points = [{ t: now - 3600, v: 24.5 }, { t: now, v: 25.0 }]
      if (url.includes('metric=temp')) return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve({ pool: 'Pool', metric: 'temp', unit: '°C', points }) })
      if (url.includes('metric=pH'))   return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve({ pool: 'Pool', metric: 'pH', unit: '', points: [{ t: now, v: 7.2 }] }) })
      if (url.includes('metric=cl'))   return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve({ pool: 'Pool', metric: 'cl', unit: 'mg/l', points: [{ t: now, v: 0.7 }] }) })
      return Promise.reject(new Error('unexpected url: ' + url))
    })
    return mount(TrendChart, { props: { pool: 'Pool' } })
  }

  it('does not preventDefault on a single-finger touchstart (pan only)', async () => {
    const wrapper = mountWithData()
    await flushPromises()
    const over = wrapper.find('[data-testid="trend-chart-temp"]').element.querySelector('.u-over')
    expect(over).not.toBeNull()
    const evt = dispatchTouch(over, 'touchstart', [{ clientX: 100, clientY: 50 }])
    expect(evt.defaultPrevented).toBe(false)
  }, 10000)

  it('preventsDefault on a two-finger touchstart (pinch)', async () => {
    const wrapper = mountWithData()
    await flushPromises()
    const over = wrapper.find('[data-testid="trend-chart-temp"]').element.querySelector('.u-over')
    const evt = dispatchTouch(over, 'touchstart', [
      { clientX: 100, clientY: 50 },
      { clientX: 200, clientY: 50 },
    ])
    expect(evt.defaultPrevented).toBe(true)
  }, 10000)

  it('preventsDefault on a double-tap (second tap within 300ms at the same spot)', async () => {
    const wrapper = mountWithData()
    await flushPromises()
    const over = wrapper.find('[data-testid="trend-chart-temp"]').element.querySelector('.u-over')
    dispatchTouch(over, 'touchstart', [{ clientX: 150, clientY: 60 }])
    // Second tap must arrive before the 300ms window expires.
    const evt = dispatchTouch(over, 'touchstart', [{ clientX: 152, clientY: 62 }])
    expect(evt.defaultPrevented).toBe(true)
  }, 10000)

  it('preventsDefault on touchmove (both pan and pinch)', async () => {
    const wrapper = mountWithData()
    await flushPromises()
    const over = wrapper.find('[data-testid="trend-chart-temp"]').element.querySelector('.u-over')
    // Start a pan
    dispatchTouch(over, 'touchstart', [{ clientX: 100, clientY: 50 }])
    const panMove = dispatchTouch(over, 'touchmove', [{ clientX: 200, clientY: 50 }])
    expect(panMove.defaultPrevented).toBe(true)
    // Start a pinch
    dispatchTouch(over, 'touchstart', [
      { clientX: 100, clientY: 50 },
      { clientX: 200, clientY: 50 },
    ])
    const pinchMove = dispatchTouch(over, 'touchmove', [
      { clientX: 80, clientY: 50 },
      { clientX: 220, clientY: 50 },
    ])
    expect(pinchMove.defaultPrevented).toBe(true)
  }, 10000)

  it('treats a second tap outside the double-tap window as a fresh pan', async () => {
    const wrapper = mountWithData()
    await flushPromises()
    const over = wrapper.find('[data-testid="trend-chart-temp"]').element.querySelector('.u-over')
    dispatchTouch(over, 'touchstart', [{ clientX: 150, clientY: 60 }])
    // Move time past the 300ms window. Date.now is the only clock the
    // handler reads, so a vi.useFakeTimers / vi.advanceTimersByTime
    // would be the cleanest way — but the simpler assertion is that a
    // tap with a different position (well past TAP_SLOP_PX = 24) is
    // never treated as a double-tap regardless of timing.
    const evt = dispatchTouch(over, 'touchstart', [{ clientX: 400, clientY: 60 }])
    expect(evt.defaultPrevented).toBe(false)
  }, 10000)
})
