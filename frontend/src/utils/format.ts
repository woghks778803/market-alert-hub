export function formatPrice(value: number | null) {
    if (value == null) return "-"

    if (value >= 1000) return value.toLocaleString(undefined, { maximumFractionDigits: 0 })
    if (value >= 1) return value.toFixed(2)

    return value.toPrecision(4)
}

export function formatChange(value: number | null) {
    if (value == null) return "-"
    return value.toFixed(2)
}

export function formatVolume(value: number | null) {
    if (value == null) return "-"

    if (value >= 1_000_000) return (value / 1_000_000).toFixed(1) + "M"
    if (value >= 1_000) return (value / 1_000).toFixed(1) + "K"
    return value.toFixed(0)
}