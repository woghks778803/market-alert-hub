import type { ApiError } from "@/api/types"

export function mapRegisterError(error?: ApiError | null): string | null {
    if (!error) {
        return "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    }

    // 이미 사용중인 이메일
    if (error.code === "conflict" && error.target === "email") {
        return "이미 사용 중인 이메일입니다."
    }

    // 값 검증 실패
    if (error.code === "forbidden" && error.target === "status.suspended") {
        return "이용이 제한된 계정입니다."
    } else if (error.code === "forbidden" && error.target === "status.deleted") {
        return "탈퇴 처리중인 계정입니다."
    }

    // 요청 과다
    if (error.code === "rate_limited") {
        return "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."
    }

    return null
    // return "회원가입에 실패했습니다. 입력 정보를 확인해주세요."
}