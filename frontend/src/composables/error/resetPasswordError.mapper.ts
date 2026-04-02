import type { ApiError } from "@/api/types"

export type ResetPasswordErrorResult =
    | { kind: "fail_mode"; message?: string }
    | { kind: "message"; message: string }

export function mapResetPasswordError(error?: ApiError | null): ResetPasswordErrorResult | null {
    if (!error) {
        return { kind: "message", message: "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요." }
    }

    // 토큰 문제(만료/위조/이미 사용됨 등) → 화면을 fail 모드로
    if (error.code === "unauthorized" && error.target === "token") {
        return { kind: "fail_mode" }
    }

    // 검증 실패(입력값 문제)
    if (error.code === "validation_error") {
        return { kind: "message", message: "입력값을 확인해주세요." }
    }

    // 기본
    return null
}