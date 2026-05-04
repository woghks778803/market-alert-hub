export function formatPrice(value: number | null, tickSize?: number) {
  if (value == null) return '-'

  if (tickSize) {
    const decimals = tickSize.toString().split('.')[1]?.length ?? 0
    return value.toFixed(decimals)
  }

  // fallback
  if (value >= 1000) return value.toLocaleString(undefined, { maximumFractionDigits: 0 })
  if (value >= 1) return value.toFixed(2)

  return value.toPrecision(4)
}

export function formatChange(value: number | null) {
  if (value == null) return '-'
  return value.toFixed(2)
}

export function formatVolume(value: number | null) {
  if (value == null) return '-'

  const abs = Math.abs(value)

  if (abs >= 1_000_000_000_000) return (value / 1_000_000_000_000).toFixed(1) + 'T'
  if (abs >= 1_000_000_000) return (value / 1_000_000_000).toFixed(1) + 'B'
  if (abs >= 1_000_000) return (value / 1_000_000).toFixed(1) + 'M'
  if (abs >= 1_000) return (value / 1_000).toFixed(1) + 'K'
  return value.toFixed(0)
}

export function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return ''

  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return ''

  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')

  return `${yyyy}.${mm}.${dd} ${hh}:${min}`
}

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return ''

  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return ''

  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')

  return `${yyyy}.${mm}.${dd}`
}

export function formatThrottleSeconds(isOnce: boolean, seconds: number | null | undefined): string {
  if (isOnce) return '최초 1회'
  if (seconds === null || seconds === undefined) return '-'

  if (seconds < 60) return `${seconds}초`

  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}분`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}시간`

  const days = Math.floor(hours / 24)
  return `${days}일`
}

export function formatTimeFrame(params: Record<string, unknown> | null | undefined): string {
  const timeframe = params?.timeframe
  const period = params?.period

  if (!timeframe) return '기준 없음'
  if (!period) return String(timeframe)

  return `${String(timeframe)} ${String(period)}`
}
