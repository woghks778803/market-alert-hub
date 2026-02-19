type JwtPayload = {
    sub?: string
    exp?: number
    ev?: boolean // email verified
}

// base64url decode (no external lib)
function base64UrlDecode(input: string): string {
    const pad = "=".repeat((4 - (input.length % 4)) % 4)
    const b64 = (input + pad).replace(/-/g, "+").replace(/_/g, "/")
    const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0))
    return new TextDecoder().decode(bytes)
}

function decodeJwtPayload(token: string): JwtPayload | null {
    const parts = token.split(".")
    if (parts.length !== 3) return null
    try {
        return JSON.parse(base64UrlDecode(parts[1])) as JwtPayload
    } catch {
        return null
    }
}

export function isTokenExpired(token: string): boolean {
    const p = decodeJwtPayload(token)
    if (!p?.exp) return true
    const nowSec = Math.floor(Date.now() / 1000)
    return nowSec >= p.exp
}

export function isEmailVerifiedFromToken(token: string): boolean {
    const p = decodeJwtPayload(token)
    return !!p?.ev
}
