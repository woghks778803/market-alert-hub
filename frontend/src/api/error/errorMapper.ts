import type { ApiError } from "@/api/types"

export function mapCommonError(error?: ApiError | null): string | null {
    if (!error) {
        return "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    }

    switch (error.code) {
        case "validation_error":
            return "입력값을 확인해주세요."

        case "unauthorized":
            return "인증이 필요합니다."

        case "forbidden":
            return "접근 권한이 없습니다."

        case "not_found":
            return "요청한 정보를 찾을 수 없습니다."

        case "conflict":
            return "이미 처리된 요청입니다."

        case "rate_limited":
            return "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."

        case "external_service_error":
            return "메일 발송 중 오류가 발생했습니다."

        case "internal_error":
        case "template_render_error":
            return "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

        default:
            return "요청 처리 중 오류가 발생했습니다."
    }
}