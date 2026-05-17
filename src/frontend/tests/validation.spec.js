import { describe, it, expect } from 'vitest'
import { FIELD_CONFIG, NAME_CONFIG } from '../src/validation.js'

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

describe('NAME_CONFIG', () => {
  it('matches valid names', () => {
    const { pattern } = NAME_CONFIG
    expect(pattern.test('Pool')).toBe(true)
    expect(pattern.test('Pool 1')).toBe(true)
    expect(pattern.test('ABC')).toBe(true)
    expect(pattern.test('a')).toBe(true)
  })

  it('rejects empty string', () => {
    expect(NAME_CONFIG.pattern.test('')).toBe(false)
  })

  it('rejects names with special characters', () => {
    expect(NAME_CONFIG.pattern.test('Pool!')).toBe(false)
    expect(NAME_CONFIG.pattern.test('P@ol')).toBe(false)
    expect(NAME_CONFIG.pattern.test('Pool-1')).toBe(false)
    expect(NAME_CONFIG.pattern.test('Pool_1')).toBe(false)
  })

  it('rejects names longer than 50 characters', () => {
    const long = 'A'.repeat(51)
    expect(long.length).toBeGreaterThan(NAME_CONFIG.maxLength)
    expect(NAME_CONFIG.pattern.test(long)).toBe(true)
    expect(long.length).toBe(51)
  })
})
