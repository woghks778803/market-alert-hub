export function maskEmail(email: string): string {
    const v = email.trim()
    const at = v.indexOf("@")
    if (at <= 1) return v

    const name = v.slice(0, at)
    const domain = v.slice(at)

    const head = name.slice(0, 2)
    return `${head}${"*".repeat(Math.max(1, name.length - 2))}${domain}`
}
