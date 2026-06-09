import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MeasurementForm from '../src/components/MeasurementForm.vue'

vi.mock('../src/composables/useApi.js', () => ({
  useApi: () => ({
    postMeasurement: vi.fn(),
    fetchPools: vi.fn().mockResolvedValue([{ name: 'Pool 1' }, { name: 'Pool 2' }]),
    loading: false,
    error: null,
  }),
}))

vi.mock('../src/composables/useToast.js', () => ({
  useToast: () => ({ show: vi.fn() }),
}))

vi.mock('../src/composables/useCamera.js', () => ({
  useCamera: () => ({ hasCamera: true }),
}))

describe('MeasurementForm', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('renders the form title', () => {
    const wrapper = mount(MeasurementForm)
    expect(wrapper.text()).toContain('Messung')
  })

  it('renders camera and file buttons when camera available', () => {
    const wrapper = mount(MeasurementForm)
    expect(wrapper.text()).toContain('Foto')
    expect(wrapper.text()).toContain('Datei')
  })

  it('renders submit button in idle state', () => {
    const wrapper = mount(MeasurementForm)
    expect(wrapper.text()).toContain('SENDEN')
  })
})
