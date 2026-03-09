// import type { ApiError } from "@/api/types"

// export type OauthErrorResult =
//     | { kind: "message"; message: string }

type GetQuery = {
    code: string,
    target: string
}

export function mapOauthError(error?: GetQuery | null): string | null {
    if (!error) {
        return "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    }

    const { code, target } = error

    if (code === "validation_error" && target === "state") {
        return "로그인 요청이 만료되었습니다. 다시 로그인해주세요."
    }

    if (code === "internal_error" && target === "state") {
        return "로그인 처리 중 문제가 발생했습니다. 다시 시도해주세요."
    }

    if (code === "internal_error" && target === "user") {
        return "로그인 처리 중 오류가 발생했습니다."
    }

    if (code === "forbidden" && target === "status.suspended") {
        return "이용이 제한된 계정입니다."
    } else if (code === "forbidden" && target === "status.deleted") {
        return "탈퇴 처리중인 계정입니다."
    }

    if (code === "not_found" && target === "oauth") {
        return "지원하지 않는 로그인 제공자입니다."
    }

    // oauth callback error (카카오)
    if (code === "access_denied" && target === "oauth") {
        return "로그인이 취소되었습니다."
    }

    if (code === "invalid_request" && target === "oauth") {
        return "잘못된 로그인 요청입니다."
    }

    if (code === "server_error" && target === "oauth") {
        return "카카오 로그인 처리 중 오류가 발생했습니다."
    }

    // 그 외
    return "로그인 처리에 실패했습니다. 다시 시도해주세요."
}