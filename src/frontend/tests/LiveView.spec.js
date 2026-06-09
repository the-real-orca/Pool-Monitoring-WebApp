import { afterEach, describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import LiveView from '../src/components/LiveView.vue'

const KEY = 'pool_monitor_settings'

function saveSettings(s) {
  localStorage.setItem(KEY, JSON.stringify({ ...s, token: btoa(s.token) }))
}

function mockSnapshot(extra = {}) {
  return {
    ts: Math.floor(Date.now() / 1000),
    temp: 24.6, pH: 7.2, cl: 0.7,
    pump: { main: { running: true, since: 1 }, solar: { running: false, since: null } },
    stale: false, staleSeconds: 5,
    ...extra,
  }
}

describe('LiveView', () => {
  let wrapper

  afterEach(() => {
    wrapper?.unmount()
  })

  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    saveSettings({ token: 'test-token' })
    vi.stubGlobal('fetch', vi.fn())
    HTMLCanvasElement.prototype.getContext = function () {
      return {
        canvas: this, save: () => {}, restore: () => {}, beginPath: () => {},
        moveTo: () => {}, lineTo: () => {}, closePath: () => {}, clip: () => {},
        translate: () => {}, rotate: () => {}, scale: () => {},
        fillRect: () => {}, clearRect: () => {}, strokeRect: () => {},
        fillText: () => {}, strokeText: () => {}, measureText: () => ({ width: 0 }),
        drawImage: () => {}, putImageData: () => {}, getImageData: () => ({ data: [] }),
        createImageData: () => ({}), setTransform: () => {}, resetTransform: () => {},
        arc: () => {}, ellipse: () => {}, rect: () => {},
        fill: () => {}, stroke: () => {}, setLineDash: () => {}, getLineDash: () => [],
        createLinearGradient: () => ({ addColorStop: () => {} }),
        createRadialGradient: () => ({ addColorStop: () => {} }),
        createPattern: () => ({}),
        bezierCurveTo: () => {}, quadraticCurveTo: () => {},
        isPointInPath: () => false, isPointInStroke: () => false,
      }
    }
  })

  it('shows the waiting message until the first snapshot arrives', async () => {
    fetch.mockImplementation(() => new Promise(() => {})) // never resolves
    wrapper = mount(LiveView)
    await flushPromises()
    expect(wrapper.text()).toContain('Warte auf Daten')
  })

  it('renders temperature, pH, cl, and pump cards once a snapshot is present', async () => {
    fetch.mockImplementation((url) => {
      if (url.startsWith('/api/pools/live')) {
        return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve([{ name: 'Pool', hasData: true }]) })
      }
      if (url.startsWith('/api/live')) {
        return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve(mockSnapshot()) })
      }
      if (url.startsWith('/api/history')) {
        return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve({ pool: 'Pool', metric: 'temp', unit: '°C', points: [] }) })
      }
      return Promise.reject(new Error('unexpected url: ' + url))
    })

    wrapper = mount(LiveView)
    await flushPromises()
    expect(wrapper.find('[data-testid="temperature-card"]').text()).toContain('24.6')
    expect(wrapper.find('[data-testid="ph-card"]').text()).toContain('7.2')
    expect(wrapper.find('[data-testid="cl-card"]').text()).toContain('0.7')
    const cards = wrapper.findAll('[data-testid="pump-status-card"]')
    expect(cards).toHaveLength(2)
  })

  it('shows the pool selector even with only one pool', async () => {
    fetch.mockImplementation((url) => {
      if (url.startsWith('/api/pools/live')) {
        return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve([{ name: 'Pool', hasData: true }]) })
      }
      if (url.startsWith('/api/live')) {
        return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve(mockSnapshot()) })
      }
      if (url.startsWith('/api/history')) {
        return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve({ pool: 'Pool', metric: 'temp', unit: '°C', points: [] }) })
      }
      return Promise.reject(new Error('unexpected url: ' + url))
    })

    wrapper = mount(LiveView)
    await flushPromises()
    const sel = wrapper.find('[data-testid="pool-selector"]')
    expect(sel.exists()).toBe(true)
    expect(sel.findAll('option')).toHaveLength(1)
  })

  it('shows the pool selector when more than one pool exists', async () => {
    fetch.mockImplementation((url) => {
      if (url.startsWith('/api/pools/live')) {
        return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve([{ name: 'Pool A', hasData: true }, { name: 'Pool B', hasData: false }]) })
      }
      if (url.startsWith('/api/live')) {
        return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve(mockSnapshot()) })
      }
      if (url.startsWith('/api/history')) {
        return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve({ pool: 'Pool A', metric: 'temp', unit: '°C', points: [] }) })
      }
      return Promise.reject(new Error('unexpected url: ' + url))
    })

    wrapper = mount(LiveView)
    await flushPromises()
    const sel = wrapper.find('[data-testid="pool-selector"]')
    expect(sel.exists()).toBe(true)
    const options = sel.findAll('option')
    expect(options).toHaveLength(2)
  })

  it('shows the stale badge when the snapshot is stale', async () => {
    fetch.mockImplementation((url) => {
      if (url.startsWith('/api/pools/live')) {
        return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve([{ name: 'Pool', hasData: true }]) })
      }
      if (url.startsWith('/api/live')) {
        return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve(mockSnapshot({ stale: true, staleSeconds: 1200 })) })
      }
      if (url.startsWith('/api/history')) {
        return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve({ pool: 'Pool', metric: 'temp', unit: '°C', points: [] }) })
      }
      return Promise.reject(new Error('unexpected url: ' + url))
    })

    wrapper = mount(LiveView)
    await flushPromises()
    expect(wrapper.find('[data-testid="stale-badge"]').exists()).toBe(true)
  })
})
