export function isEmail(value: string): boolean {
    const v = value.trim()
    if (!v) return false
    // 너무 빡센 정규식 말고 실무에서 흔히 쓰는 최소 체크
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)
}

export function minLength(value: string, n: number): boolean {
    return value.trim().length >= n
}
