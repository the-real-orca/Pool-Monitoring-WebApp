import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StepperInput from '../src/components/StepperInput.vue'

describe('StepperInput', () => {
  function createWrapper(props) {
    return mount(StepperInput, {
      props: {
        modelValue: 10.0,
        min: 0.0,
        max: 20.0,
        step: 0.5,
        decimals: 1,
        unit: '°C',
        ...props,
      },
    })
  }

  it('click + emits modelValue + step', async () => {
    const wrapper = createWrapper({ modelValue: 10.0 })
    await wrapper.findAll('button')[1].trigger('click')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([10.5])
  })

  it('click - emits modelValue - step', async () => {
    const wrapper = createWrapper({ modelValue: 10.0 })
    await wrapper.findAll('button')[0].trigger('click')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([9.5])
  })

  it('does not emit when modelValue === max (button disabled)', async () => {
    const wrapper = createWrapper({ modelValue: 20.0 })
    const plusBtn = wrapper.findAll('button')[1]
    expect(plusBtn.attributes('disabled')).toBeDefined()
    await plusBtn.trigger('click')
    expect(wrapper.emitted('update:modelValue')).toBeFalsy()
  })

  it('does not emit when modelValue === min (button disabled)', async () => {
    const wrapper = createWrapper({ modelValue: 0.0 })
    const minusBtn = wrapper.findAll('button')[0]
    expect(minusBtn.attributes('disabled')).toBeDefined()
    await minusBtn.trigger('click')
    expect(wrapper.emitted('update:modelValue')).toBeFalsy()
  })

  it('toFixed(decimals) rounding is correct', async () => {
    const wrapper = createWrapper({ modelValue: 10.0, step: 0.333, decimals: 2 })
    await wrapper.findAll('button')[1].trigger('click')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([10.33])
  })

  it('displays value with correct decimals and unit', () => {
    const wrapper = createWrapper({ modelValue: 7.5, decimals: 1, unit: 'mg/l' })
    const input = wrapper.find('input')
    expect(input.element.value).toBe('7.5')
    expect(wrapper.text()).toContain('mg/l')
  })

  it('accepts comma as decimal separator', async () => {
    const wrapper = createWrapper({ modelValue: 20.0, min: 0, max: 45, decimals: 1, unit: '°C' })
    const input = wrapper.find('input')
    await input.setValue('21,4')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([21.4])
  })

  it('accepts dot as decimal separator', async () => {
    const wrapper = createWrapper({ modelValue: 20.0, min: 0, max: 45, decimals: 1, unit: '°C' })
    const input = wrapper.find('input')
    await input.setValue('21.4')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([21.4])
  })

  it('clamps value to min/max', async () => {
    const wrapper = createWrapper({ modelValue: 20.0, min: 0, max: 45, decimals: 1, unit: '°C' })
    const input = wrapper.find('input')
    await input.setValue('99,9')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([45.0])
  })
})
