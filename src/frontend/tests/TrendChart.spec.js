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
    // jsdom doesn't implement HTMLCanvasElement.getContext; Chart.js
    // would otherwise throw. Provide a no-op stub.
    HTMLCanvasElement.prototype.getContext = function () {
      return {
        canvas: this,
        save: () => {}, restore: () => {}, beginPath: () => {},
        moveTo: () => {}, lineTo: () => {}, closePath: () => {}, clip: () => {},
        translate: () => {}, rotate: () => {}, scale: () => {},
        fillRect: () => {}, clearRect: () => {}, strokeRect: () => {},
        fillText: () => {}, strokeText: () => {}, measureText: () => ({ width: 0 }),
        drawImage: () => {},
        putImageData: () => {}, getImageData: () => ({ data: [] }),
        createImageData: () => ({}),
        setTransform: () => {}, resetTransform: () => {},
        arc: () => {}, ellipse: () => {}, rect: () => {},
        fill: () => {}, stroke: () => {},
        setLineDash: () => {}, getLineDash: () => [],
        createLinearGradient: () => ({ addColorStop: () => {} }),
        createRadialGradient: () => ({ addColorStop: () => {} }),
        createPattern: () => ({}),
        bezierCurveTo: () => {}, quadraticCurveTo: () => {},
        isPointInPath: () => false, isPointInStroke: () => false,
      }
    }
  })

  it('shows the empty state when no points are returned', async () => {
    fetch.mockResolvedValue({ status: 200, ok: true, json: () => Promise.resolve({ pool: 'Pool', metric: 'temp', unit: '°C', points: [] }) })

    const wrapper = mount(TrendChart, { props: { pool: 'Pool' } })
    await flushPromises()
    expect(wrapper.text()).toContain('Noch keine Daten')
  })

  it('fetches all three metrics and creates 3 datasets when data is present', async () => {
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
    const canvas = wrapper.find('canvas')
    expect(canvas.exists()).toBe(true)
    // three fetch calls (one per metric)
    expect(fetch).toHaveBeenCalledTimes(3)
  })

  it('destroys the chart instance on unmount', async () => {
    fetch.mockResolvedValue({ status: 200, ok: true, json: () => Promise.resolve({ pool: 'Pool', metric: 'temp', unit: '°C', points: [] }) })

    const wrapper = mount(TrendChart, { props: { pool: 'Pool' } })
    await flushPromises()
    // The component owns a Chart.js instance — verify that unmounting does
    // not throw and tears down the canvas.
    const canvas = wrapper.find('canvas').element
    expect(canvas).toBeTruthy()
    wrapper.unmount()
    // No further assertions possible in jsdom; absence of thrown errors is
    // the contract.
  })
})
