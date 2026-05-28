export function getDecimalPlaces(value: number | null): number {
  if (value == null || !Number.isFinite(value)) return 0

  const text = value.toString().toLowerCase()

  if (text.includes('e-')) {
    const [coefficient, exponentText] = text.split('e-')
    const coefficientDecimals =
      coefficient.split('.')[1]?.length ?? 0

    return Number(exponentText) + coefficientDecimals
  }

  return text.split('.')[1]?.length ?? 0
}

export function normalizeNumberString(value: string): string {
  return value.replace(/,/g, '').trim()
}

export function toNumberOrNull(value: unknown): number | null {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null
  }

  if (typeof value !== 'string') {
    return null
  }

  const normalized = normalizeNumberString(value)
  if (!normalized) {
    return null
  }

  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : null
}

export function isPositiveNumber(value: unknown): boolean {
  const parsed = toNumberOrNull(value)
  return parsed !== null && parsed > 0
}

export function isNonNegativeNumber(value: unknown): boolean {
  const parsed = toNumberOrNull(value)
  return parsed !== null && parsed >= 0
}
