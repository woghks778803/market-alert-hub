import type { ApiError } from "@/api/types"

export type EmailVerifyErrorResult =
    | { kind: "cooldown"; cooldownSec: number; message: string }
    | { kind: "message"; message: string }

function pickCooldownSec(details: unknown): number | null {
    const d = details as any
    const sec = d?.cooldown_remaining_sec
    return typeof sec === "number" && Number.isFinite(sec) && sec >= 0 ? sec : null
}

export function mapEmailVerifyError(error?: ApiError | null): EmailVerifyErrorResult | null {
    if (!error) {
        return { kind: "message", message: "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요." }
    }

    // 이미 사용중인 이메일
    if (error.code === "conflict" && error.target === "new_email") {
        return { kind: "message", message: "이미 사용 중인 이메일입니다." }
    }

    // 입력값 검증 실패
    if (error.code === "validation_error") {
        return { kind: "message", message: "입력 정보를 다시 확인해주세요." }
    }

    // 쿨다운
    if (error.code === "rate_limited" && error.target === "resend_password_reset") {
        const sec = pickCooldownSec(error.details)
        if (sec !== null) {
            return { kind: "cooldown", cooldownSec: sec, message: "잠시 후 다시 시도해주세요." }
        }
        return { kind: "message", message: "요청이 너무 많습니다. 잠시 후 다시 시도해주세요." }
    }

    // 그 외
    return null
    // return { kind: "message", message: "요청 처리에 실패했습니다. 다시 시도해주세요." }
}