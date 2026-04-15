import type { ApiError } from "@/api/types"

export function mapAlertCreateError(error: ApiError | null): string | null {
    if (!error) {
        return "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    }

    if (
        error.code === "conflict" &&
        error.target === "alert_status"
    ) {
        return "알림은 활성 상태로만 생성할 수 있습니다."
    }

    if (
        error.code === "conflict" &&
        error.target === "user_alert"
    ) {
        return "전체 알림은 최대 30개까지 만들 수 있습니다. 사용하지 않는 알림을 삭제한 뒤 다시 시도해주세요."
    }

    if (
        error.code === "conflict" &&
        error.target === "user_active_alert"
    ) {
        return "활성 알림은 최대 5개까지 사용할 수 있습니다. 사용하지 않는 알림을 비활성화한 뒤 다시 시도해주세요."
    }

    if (
        error.code === "not_found" &&
        error.target === "alert_type"
    ) {
        return "사용할 수 없는 알림 유형입니다. 새로고침 후 다시 시도해주세요.";
    }

    if (error.code === "validation_error") {
        return "알림 정보를 다시 확인해주세요."
    }

    if (error.code === "rate_limited") {
        return "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."
    }

    return null
}

export function mapAlertUpdateError(error: ApiError | null): string | null {
    if (!error) {
        return "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    }

    if (
        error.code === "not_found" &&
        error.target === "alert"
    ) {
        return "알림을 찾을 수 없습니다. 이미 삭제되었거나 접근할 수 없는 알림입니다."
    }

    if (
        error.code === "not_found" &&
        error.target === "alert_type"
    ) {
        return "사용할 수 없는 알림 유형입니다. 새로고침 후 다시 시도해주세요.";
    }

    if (
        error.code === "conflict" &&
        error.target === "alert_status"
    ) {
        return "보관된 알림은 수정할 수 없습니다. 보관 해제 후 다시 시도해주세요."
    }

    if (error.code === "validation_error") {
        return "알림 정보를 다시 확인해주세요."
    }

    if (error.code === "rate_limited") {
        return "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."
    }

    return null
}

export function mapAlertUpdateStatusError(error: ApiError | null): string | null {
    if (!error) {
        return "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    }

    if (
        error.code === "not_found" &&
        error.target === "alert"
    ) {
        return "알림을 찾을 수 없습니다. 이미 삭제되었거나 접근할 수 없는 알림입니다."
    }

    if (
        error.code === "not_found" &&
        error.target === "alert_type"
    ) {
        return "사용할 수 없는 알림 유형입니다. 새로고침 후 다시 시도해주세요.";
    }

    if (
        error.code === "conflict" &&
        error.target === "alert_status"
    ) {
        return "보관된 알림은 바로 활성화할 수 없습니다. 보관 해제 후 다시 시도해주세요."
    }

    if (
        error.code === "conflict" &&
        error.target === "user_archived_alert"
    ) {
        return "보관함에는 최대 200개까지 보관할 수 있습니다. 오래된 알림을 삭제한 뒤 다시 시도해주세요."
    }

    if (
        error.code === "conflict" &&
        error.target === "user_alert"
    ) {
        return "전체 알림은 최대 30개까지 사용할 수 있습니다. 사용하지 않는 알림을 삭제하거나 보관한 뒤 다시 시도해주세요."
    }

    if (
        error.code === "conflict" &&
        error.target === "user_active_alert"
    ) {
        return "활성 알림은 최대 5개까지 사용할 수 있습니다. 사용하지 않는 알림을 비활성화한 뒤 다시 시도해주세요."
    }

    if (error.code === "validation_error") {
        return "알림 상태 정보를 다시 확인해주세요."
    }

    if (error.code === "rate_limited") {
        return "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."
    }

    return null
}