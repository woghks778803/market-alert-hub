import type { ApiError } from "@/api/types"

export function mapChangePasswordError(error: ApiError | null): string | null {
    if (!error) {
        return "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    }

    if (
        (error.code === "forbidden" || error.code === "unauthorized") &&
        error.target === "user"
    ) {
        return "현재 비밀번호가 올바르지 않습니다."
    }

    if (error.code === "rate_limited") {
        return "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."
    }

    return null
}