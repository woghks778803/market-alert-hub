import type { ApiError } from "@/api/types"

export function mapTermsConsentError(error?: ApiError | null): string | null {
    if (!error) {
        return "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    }

    // 그 외
    return null
    // return { kind: "message", message: "요청 처리에 실패했습니다. 다시 시도해주세요." }
}