import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ValueSliderInput from '../src/components/ValueSliderInput.vue'

describe('ValueSliderInput', () => {
  function createWrapper(props) {
    return mount(ValueSliderInput, {
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

  // buttons[0] = −, buttons[1] = value display (opens slider), buttons[2] = +
  // The step buttons use @mousedown (not @click) to enable hold-to-repeat.

  it('uses regular step for +', async () => {
    const wrapper = createWrapper({ modelValue: 10.0, step: 0.5, decimals: 1 })
    await wrapper.findAll('button')[2].trigger('mousedown')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([10.5])
  })

  it('uses regular step for - when stepDown is not provided', async () => {
    const wrapper = createWrapper({ modelValue: 10.0, step: 0.5, decimals: 1 })
    await wrapper.findAll('button')[0].trigger('mousedown')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([9.5])
  })

  it('uses stepDown for - when provided', async () => {
    const wrapper = createWrapper({
      modelValue: 10.0,
      min: 0.0,
      max: 20.0,
      step: 10.0,
      stepDown: 1.0,
      decimals: 1,
    })
    await wrapper.findAll('button')[0].trigger('mousedown')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([9.0])
  })

  it('ignores stepDown for +', async () => {
    const wrapper = createWrapper({
      modelValue: 10.0,
      min: 0.0,
      max: 20.0,
      step: 10.0,
      stepDown: 1.0,
      decimals: 1,
    })
    await wrapper.findAll('button')[2].trigger('mousedown')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([20.0])
  })

  it('+ on empty uses emptyValue', async () => {
    const wrapper = createWrapper({
      modelValue: null,
      min: 0.0,
      max: 20.0,
      step: 0.1,
      decimals: 1,
      emptyValue: 0.1,
    })
    await wrapper.findAll('button')[2].trigger('mousedown')
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([0.1])
  })
})
