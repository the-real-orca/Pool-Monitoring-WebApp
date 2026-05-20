import { describe, it, expect } from 'vitest'
import { FIELD_CONFIG } from '../src/validation.js'

describe('FIELD_CONFIG', () => {
  it('has correct temp config', () => {
    const c = FIELD_CONFIG.temp
    expect(c.min).toBe(5.0)
    expect(c.max).toBe(45.0)
    expect(c.step).toBe(0.2)
    expect(c.default).toBe(20.0)
    expect(c.decimals).toBe(1)
    expect(c.unit).toBe('°C')
  })

  it('has correct pH config', () => {
    const c = FIELD_CONFIG.pH
    expect(c.min).toBe(0.0)
    expect(c.max).toBe(14.0)
    expect(c.step).toBe(0.1)
    expect(c.default).toBe(7.0)
    expect(c.decimals).toBe(1)
    expect(c.unit).toBe('')
  })

  it('has correct chlorine config', () => {
    const c = FIELD_CONFIG.cl
    expect(c.min).toBe(0.0)
    expect(c.max).toBe(10.0)
    expect(c.step).toBe(0.1)
    expect(c.default).toBe(1.0)
    expect(c.decimals).toBe(1)
    expect(c.unit).toBe('mg/l')
  })
})
