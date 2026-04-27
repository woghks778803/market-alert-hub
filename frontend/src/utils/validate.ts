export function isEmail(value: string): boolean {
    const v = value.trim()
    if (!v) return false
    // 너무 빡센 정규식 말고 실무에서 흔히 쓰는 최소 체크
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)
}

export function minLength(value: string, n: number): boolean {
    return value.trim().length >= n
}

export function maxLength(value: string, n: number): boolean {
    return value.trim().length <= n
}

export function isStrongPassword(v: string): boolean {
    const s = v.trim();
    if (s.length < 8) return false;

    const hasDigit = /\d/.test(s);
    const hasLetter = /[A-Za-z]/.test(s);
    const hasSpecial = /[^A-Za-z0-9]/.test(s);

    return hasDigit && hasLetter && hasSpecial;
}

export function isValidNickname(v: string): boolean {
    const s = v.trim();
    if (!s) return false;
    if (s.length < 2) return false;
    if (s.length > 20) return false;
    return true;
}
