import type { ApiError } from "@/api/types"

export type VerifyEmailSentErrorResult =
    | { kind: "cooldown"; cooldownSec: number; message: string }
    | { kind: "logout"; message?: string }
    | { kind: "message"; message: string }

function pickCooldownSec(details: unknown): number | null {
    const m = details as any
    const sec = m?.cooldown_remaining_sec
    return typeof sec === "number" && Number.isFinite(sec) && sec >= 0 ? sec : null
}

export function mapVerifyEmailSentError(error?: ApiError | null): VerifyEmailSentErrorResult | null {
    if (!error) {
        return { kind: "message", message: "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요." }
    }

    // 재발송 쿨다운
    if (error.code === "rate_limited" && error.target === "resend_email_verification") {
        console.log("error: ", error)
        const sec = pickCooldownSec(error.details)
        if (sec !== null) {
            return { kind: "cooldown", cooldownSec: sec, message: "잠시 후 다시 시도해주세요." }
        }
        return { kind: "message", message: "요청이 너무 많습니다. 잠시 후 다시 시도해주세요." }
    }

    // 이미 인증됨(또는 중복 요청)
    if (error.code === "conflict" && error.target === "email") {
        return { kind: "message", message: "이미 인증된 이메일입니다." }
    }

    // 이메일 정보 문제
    if (error.code === "unauthorized" && error.target === "email") {
        return { kind: "message", message: "이메일 정보에 문제가 있습니다. 고객센터에 문의해주세요." }
    }

    // 로그인 상태/토큰 문제 → 로그아웃 처리 필요
    if (error.code === "unauthorized" && (error.target === "user" || error.target === "token")) {
        return { kind: "logout" }
    }

    return null
}