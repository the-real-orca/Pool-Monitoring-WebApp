export const FRACTION_UNITS = ['l', 'kg']

// Step width grows with the value. Asymmetric at thresholds: pressing "+"
// uses the step for the current range, pressing "-" uses the step for the
// range one tick below — so 1.0 l − → 0.9 (not 0) and 10 − → 9 (not 0).
//   l/kg: 0.1 below/at 1, 1 from >1 to <10, 10 from 10 up
//   other: 1 below 10, 10 from 10 up
//   Valid values: l/kg = 0.1…0.9, 1…9, 10, 20, … 100
//                 other = 1…9, 10, 20, … 100
export function stepFor(unit, value, dir) {
  const v = value ?? 0
  const isFraction = FRACTION_UNITS.includes(unit)
  if (isFraction) {
    if (v < 1) return 0.1
    if (v < 10) {
      if (v === 1 && dir === -1) return 0.1
      return 1
    }
    if (v === 10 && dir === -1) return 1
    return 10
  }
  if (v < 10) return 1
  if (v === 10 && dir === -1) return 1
  return 10
}

export function amountDecimals(unit) {
  return FRACTION_UNITS.includes(unit) ? 1 : 0
}

export function amountEmptyValue(unit, value) {
  return FRACTION_UNITS.includes(unit) && (value ?? 0) < 1 ? 0.1 : 1
}

// Snap a drag/manual entry to the nearest valid grid value. The stepper
// itself produces only valid values (1.0 l + → 2.0 directly, not 1.1).
export function snapAmount(unit, newAmount) {
  if (newAmount == null || newAmount <= 0) return newAmount
  const v = newAmount
  const isFraction = FRACTION_UNITS.includes(unit)
  if (isFraction && v < 1) return Math.round(v * 10) / 10
  if (v < 10) return Math.round(v)
  return Math.round(v / 10) * 10
}
