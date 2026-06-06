import { describe, it, expect } from 'vitest'
import { stepFor, amountDecimals, amountEmptyValue, snapAmount } from '../src/utils/eventStep.js'

describe('stepFor — l/kg', () => {
  it('returns 0.1 below 1 in both directions', () => {
    expect(stepFor('l', 0, +1)).toBe(0.1)
    expect(stepFor('l', 0, -1)).toBe(0.1)
    expect(stepFor('l', 0.5, +1)).toBe(0.1)
    expect(stepFor('l', 0.5, -1)).toBe(0.1)
    expect(stepFor('l', 0.9, +1)).toBe(0.1)
    expect(stepFor('kg', 0.9, -1)).toBe(0.1)
  })

  it('uses 0.1 going down from 1, 1 going up from 1', () => {
    expect(stepFor('l', 1, +1)).toBe(1)
    expect(stepFor('l', 1, -1)).toBe(0.1)
    expect(stepFor('kg', 1, +1)).toBe(1)
    expect(stepFor('kg', 1, -1)).toBe(0.1)
  })

  it('returns 1 between 2 and 9 in both directions', () => {
    expect(stepFor('l', 2, +1)).toBe(1)
    expect(stepFor('l', 2, -1)).toBe(1)
    expect(stepFor('l', 9, +1)).toBe(1)
    expect(stepFor('l', 9, -1)).toBe(1)
  })

  it('uses 1 going down from 10, 10 going up from 10', () => {
    expect(stepFor('l', 10, +1)).toBe(10)
    expect(stepFor('l', 10, -1)).toBe(1)
    expect(stepFor('kg', 10, -1)).toBe(1)
  })

  it('returns 10 above 10 in both directions', () => {
    expect(stepFor('l', 20, +1)).toBe(10)
    expect(stepFor('l', 20, -1)).toBe(10)
    expect(stepFor('l', 50, +1)).toBe(10)
    expect(stepFor('l', 50, -1)).toBe(10)
    expect(stepFor('l', 100, +1)).toBe(10)
  })
})

describe('stepFor — non-fraction units (g, tabs, min)', () => {
  it('returns 1 below 10 in both directions', () => {
    expect(stepFor('g', 0, +1)).toBe(1)
    expect(stepFor('g', 0, -1)).toBe(1)
    expect(stepFor('g', 5, +1)).toBe(1)
    expect(stepFor('g', 5, -1)).toBe(1)
    expect(stepFor('tabs', 9, -1)).toBe(1)
    expect(stepFor('min', 1, +1)).toBe(1)
  })

  it('uses 1 going down from 10, 10 going up from 10', () => {
    expect(stepFor('g', 10, +1)).toBe(10)
    expect(stepFor('g', 10, -1)).toBe(1)
    expect(stepFor('min', 10, -1)).toBe(1)
  })

  it('returns 10 above 10 in both directions', () => {
    expect(stepFor('g', 20, +1)).toBe(10)
    expect(stepFor('g', 20, -1)).toBe(10)
    expect(stepFor('min', 50, +1)).toBe(10)
    expect(stepFor('min', 50, -1)).toBe(10)
  })
})

describe('amountDecimals', () => {
  it('returns 1 for l/kg, 0 otherwise', () => {
    expect(amountDecimals('l')).toBe(1)
    expect(amountDecimals('kg')).toBe(1)
    expect(amountDecimals('g')).toBe(0)
    expect(amountDecimals('tabs')).toBe(0)
    expect(amountDecimals('min')).toBe(0)
  })
})

describe('amountEmptyValue', () => {
  it('returns 0.1 for l/kg when current value is below 1', () => {
    expect(amountEmptyValue('l', null)).toBe(0.1)
    expect(amountEmptyValue('l', 0)).toBe(0.1)
    expect(amountEmptyValue('kg', 0.5)).toBe(0.1)
  })

  it('returns 1 for l/kg when current value is at or above 1', () => {
    expect(amountEmptyValue('l', 1)).toBe(1)
    expect(amountEmptyValue('kg', 10)).toBe(1)
  })

  it('returns 1 for all non-fraction units', () => {
    expect(amountEmptyValue('g', null)).toBe(1)
    expect(amountEmptyValue('tabs', 0)).toBe(1)
    expect(amountEmptyValue('min', 5)).toBe(1)
  })
})

describe('snapAmount — l/kg below 1', () => {
  it('rounds drag/manual entries to nearest 0.1', () => {
    expect(snapAmount('l', 0.35)).toBe(0.4)
    expect(snapAmount('l', 0.33)).toBe(0.3)
    expect(snapAmount('l', 0.05)).toBe(0.1)
  })

  it('passes through valid 0.1 values', () => {
    expect(snapAmount('l', 0.1)).toBe(0.1)
    expect(snapAmount('l', 0.5)).toBe(0.5)
    expect(snapAmount('kg', 0.9)).toBe(0.9)
  })
})

describe('snapAmount — l/kg in 1–9 range', () => {
  it('passes through valid integers', () => {
    expect(snapAmount('l', 1)).toBe(1)
    expect(snapAmount('l', 2)).toBe(2)
    expect(snapAmount('l', 9)).toBe(9)
  })

  it('rounds drag/manual between integers to nearest', () => {
    expect(snapAmount('l', 4.7)).toBe(5)
    expect(snapAmount('l', 3.2)).toBe(3)
  })
})

describe('snapAmount — l/kg above 10', () => {
  it('rounds drag/manual entries to nearest 10', () => {
    expect(snapAmount('l', 47)).toBe(50)
    expect(snapAmount('l', 53)).toBe(50)
    expect(snapAmount('l', 55)).toBe(60)
    expect(snapAmount('l', 56)).toBe(60)
  })

  it('passes through valid multiples of 10', () => {
    expect(snapAmount('l', 10)).toBe(10)
    expect(snapAmount('l', 20)).toBe(20)
    expect(snapAmount('l', 30)).toBe(30)
    expect(snapAmount('kg', 100)).toBe(100)
  })
})

describe('snapAmount — non-fraction units', () => {
  it('passes through valid integers below 10', () => {
    expect(snapAmount('g', 5)).toBe(5)
    expect(snapAmount('g', 9)).toBe(9)
  })

  it('rounds drag/manual between integers to nearest', () => {
    expect(snapAmount('g', 5.4)).toBe(5)
  })

  it('rounds drag/manual above 10 to nearest 10', () => {
    expect(snapAmount('tabs', 47)).toBe(50)
    expect(snapAmount('min', 56)).toBe(60)
  })
})

describe('snapAmount — null/zero passthrough', () => {
  it('returns null for null', () => {
    expect(snapAmount('l', null)).toBe(null)
  })

  it('returns 0 unchanged (watcher handles reset to null separately)', () => {
    expect(snapAmount('l', 0)).toBe(0)
  })
})
