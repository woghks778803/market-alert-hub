import type { CursorListResult, CursorPagination } from "@/api/types"
import {
    alertApi
} from "@/api/alert.api"
import {
    toAlertSummaryDto,
    toAlertSaveRequest,
    toArchivedAlertListRequest,
    toAlertListRequest,
    toAlertLogListRequest,
    toAlertTypeListRequest,
    toAlertDto,
    toAlertLogDto,
    toAlertTypeDto
} from "@/services/alert.mapper"
import type {
    ArchivedAlertListQuery,
    AlertListQuery,
    AlertLogListQuery,
    AlertTypeListQuery,
    AlertSaveQuery,
    AlertSummaryDto,
    AlertDto,
    AlertLogDto,
    AlertTypeDto,
    AlertStatus
} from "@/services/alert.types"


export async function getAlert(id: number): Promise<AlertDto> {
    const env = await alertApi.getAlert(id)

    if (!env.success || !env.data) {
        throw env.error ?? new Error("invalid_alert_list_response")
    }

    return toAlertDto(env.data)
}

export async function getAlerts(payload: AlertListQuery): Promise<CursorListResult<AlertDto>> {
    const env = await alertApi.getAlerts(toAlertListRequest(payload))

    if (!env.success || !env.data) {
        throw env.error ?? new Error("invalid_alert_list_response")
    }

    return {
        items: env.data.map(toAlertDto),
        page: env.meta.pagination as CursorPagination
    }
}

export async function getAlertLogs(payload: AlertLogListQuery): Promise<CursorListResult<AlertLogDto>> {
    const env = await alertApi.getAlertLogs(toAlertLogListRequest(payload))

    if (!env.success || !env.data) {
        throw env.error ?? new Error("invalid_alert_log_list_response")
    }

    return {
        items: env.data.map(toAlertLogDto),
        page: env.meta.pagination as CursorPagination
    }
}

export async function getAlertTypes(payload: AlertTypeListQuery): Promise<AlertTypeDto[]> {
    const env = await alertApi.getAlertTypes(toAlertTypeListRequest(payload))

    if (!env.success || !env.data) {
        throw env.error ?? new Error("invalid_alert_type_list_response")
    }

    return env.data.map(toAlertTypeDto)
}

export async function getArchivedAlerts(payload: ArchivedAlertListQuery): Promise<CursorListResult<AlertDto>> {
    const env = await alertApi.getArchivedAlerts(toArchivedAlertListRequest(payload))

    if (!env.success || !env.data) {
        throw env.error ?? new Error("invalid_archived_alert_list_response")
    }

    return {
        items: env.data.map(toAlertDto),
        page: env.meta.pagination as CursorPagination
    }
}

export async function getAlertSummary(): Promise<AlertSummaryDto> {
    const env = await alertApi.getAlertSummary()

    if (!env.success || !env.data) {
        throw env.error ?? new Error("invalid_alert_summary_response")
    }

    return toAlertSummaryDto(env.data)
}

export async function changeAlert(alertId: number, payload: AlertSaveQuery): Promise<void> {
    const env = await alertApi.changeAlert(alertId, toAlertSaveRequest(payload))

    if (!env.success) {
        throw env.error ?? new Error("change_status_failed")
    }
}

export async function changeAlertStatus(alertId: number, payload: { status: AlertStatus }): Promise<void> {
    const env = await alertApi.changeAlertStatus(alertId, payload)
    if (!env.success) {
        throw env.error ?? new Error("change_status_failed")
    }
}

export async function createAlert(payload: AlertSaveQuery) {
    const env = await alertApi.create(toAlertSaveRequest(payload))

    if (!env.success || !env.data) {
        throw new Error("create_alert_failed")
    }

    return env.data
}

export async function removeAlert(id: number) {
    await alertApi.remove(id)
}