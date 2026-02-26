import type { ApiError } from "@/api/types"

export function mapRegisterError(error?: ApiError | null): string | null {
    if (!error) {
        return "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    }

    // 이미 사용중인 이메일
    if (error.code === "conflict" && error.target === "email") {
        return "이미 사용 중인 이메일입니다."
    }

    // 입력값 검증 실패
    if (error.code === "validation_error") {
        return "입력 정보를 다시 확인해주세요."
    }

    // 요청 과다
    if (error.code === "rate_limited") {
        return "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."
    }

    return null
    // return "회원가입에 실패했습니다. 입력 정보를 확인해주세요."
}