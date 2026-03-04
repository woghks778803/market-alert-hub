import type { ApiError } from "@/api/types"

export function mapLoginError(error?: ApiError | null): string | null {
    if (!error) {
        return "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    }

    if (error.code === "forbidden" && error.target === "role") {
        return "권한이 없습니다."
    }

    if (error.code === "forbidden" && error.target === "status") {
        return "계정이 정지되었습니다. 자세한 내용은 고객센터에 문의해주세요."
    }

    if (error.code === "unauthorized" && error.target === "email") {
        return "이메일 정보에 문제가 있습니다. 고객센터에 문의해주세요."
    }

    // 401 기본 로그인 실패
    if (error.code === "unauthorized") {
        return "로그인에 실패했습니다. 이메일과 비밀번호를 확인해주세요."
    }

    return null
}