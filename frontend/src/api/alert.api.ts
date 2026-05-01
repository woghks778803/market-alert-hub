import { http } from "./http"
import type { Envelope, SimpleOk } from "./types"

export type AlertSummaryInfo = {
    total_count: number
    active_count: number
    paused_count: number
}

export type AlertInfo = {
    id: number
    alert_type_id: number
    name: string
    status: string

    timezone: string
    timeframe: string | null
    period: number | null
    params: Record<string, unknown>

    throttle_seconds: number
    is_once: boolean
    valid_from: string | null
    valid_to: string | null
    updated_at: string

    exchange_instrument_id: number
    exchange_symbol: string
    exchange_code: string
    exchange_name: string
    ei_is_active: boolean
    e_is_active: boolean
}

export type AlertLogInfo = {
    alert_event_id: number
    alert_id: number
    title: string
    body: string
    exchange_code: string
    exchange_symbol: string
    status: string
    detected_at: string
}

export type AlertTypeInfo = {
    id: number
    code: string
    name: string
    indicator: string
    direction: string | null
    form_type: string
    param_schema: Record<string, unknown>
}

export type ArchivedAlertListRequest = {
    limit?: number
    cursor?: string
    sort?: string
}

export type AlertListRequest = {
    limit?: number
    cursor?: string
    status?: string
    sort?: string
}

export type AlertLogListRequest = {
    limit?: number
    cursor?: string
    status?: string
}

export type AlertTypeListRequest = {
    limit?: number
    offset?: number
    search?: string
}

export type AlertSaveRequest = {
    name: string
    exchange_instrument_id: number | null
    alert_type_id: number

    is_once: boolean
    status: string

    throttle_timeframe: string
    timezone: string

    use_validity: boolean
    valid_from: string | null
    valid_to: string | null

    params: Record<string, unknown>
}

export const alertApi = {
    // GET /alerts/{alert_id}
    async getAlert(alertId: number) {
        const { data } = await http.get<Envelope<AlertInfo>>(`/alerts/${alertId}`)
        return data
    },

    // GET /alerts
    async getAlerts(params: AlertListRequest) {
        const { data } = await http.get<Envelope<AlertInfo[]>>("/alerts", { params })
        return data
    },

    // GET /alerts/archives
    async getArchivedAlerts(params: ArchivedAlertListRequest) {
        const { data } = await http.get<Envelope<AlertInfo[]>>("/alerts/archives", { params })
        return data
    },

    // GET /alerts/logs
    async getAlertLogs(params: AlertLogListRequest) {
        const { data } = await http.get<Envelope<AlertLogInfo[]>>("/alerts/logs", { params })
        return data
    },

    // GET /alerts/types
    async getAlertTypes(params: AlertTypeListRequest) {
        const { data } = await http.get<Envelope<AlertTypeInfo[]>>("/alerts/types", { params })
        return data
    },

    // GET /alerts/summary
    async getAlertSummary() {
        const { data } = await http.get<Envelope<AlertSummaryInfo>>("/alerts/summary")
        return data
    },

    // POST /alerts
    async create(payload: AlertSaveRequest) {
        const { data } = await http.post<Envelope<SimpleOk>>(
            "/alerts", payload
        );
        return data;
    },

    // PATCH /alerts/{alert_id}
    async changeAlert(alertId: number, payload: AlertSaveRequest) {
        const { data } = await http.patch<Envelope<SimpleOk>>(`/alerts/${alertId}`, payload)
        return data
    },

    // PATCH /alerts/{alert_id}/status
    async changeAlertStatus(alertId: number, payload: { status: string }) {
        const { data } = await http.patch<Envelope<SimpleOk>>(`/alerts/${alertId}/status`, { status: payload.status })
        return data
    },

    // DELETE /alerts/{alert_id}
    async remove(alertId: number) {
        const { data } = await http.delete(
            `/alerts/${alertId}`
        );
        return data;
    },

}