
import type { AlertSummaryInfo, AlertInfo, AlertTypeInfo, ArchivedAlertListRequest, AlertListRequest, AlertTypeListRequest, AlertSaveRequest } from "@/api/alert.api"
import type { AlertSummaryDto, AlertDto, AlertTypeDto, ArchivedAlertListQuery, AlertListQuery, AlertTypeListQuery, AlertSaveQuery, AlertStatus, AlertScope, FormType } from "@/services/alert.types"

export function toAlertSummaryDto(data: AlertSummaryInfo): AlertSummaryDto {
    return {
        totalCount: data.total_count,
        activeCount: data.active_count,
        pausedCount: data.paused_count,
    }
}

export function toAlertDto(data: AlertInfo): AlertDto {
    return {
        id: data.id,
        alertTypeId: data.alert_type_id,
        name: data.name,
        status: data.status as AlertStatus,
        scope: data.scope as AlertScope,

        timezone: data.timezone,
        timeframe: data.timeframe,
        period: data.period,
        params: data.params,

        throttleSeconds: data.throttle_seconds,
        isOnce: data.is_once,
        validFrom: data.valid_from,
        validTo: data.valid_to,
        updatedAt: data.updated_at,

        exchangeInstrumentId: data.exchange_instrument_id,
        exchangeSymbol: data.exchange_symbol,
        exchangeCode: data.exchange_code,
        exchangeName: data.exchange_name,
        exchangeInstrumentIsActive: data.ei_is_active,
        exchangeIsActive: data.e_is_active,
    }
}

export function toAlertTypeDto(data: AlertTypeInfo): AlertTypeDto {
    return {
        id: data.id,
        code: data.code,
        name: data.name,
        indicator: data.indicator,
        direction: data.direction,
        formType: data.form_type as FormType,
        paramSchema: data.param_schema,
    }
}

export function toAlertListRequest(q: AlertListQuery): AlertListRequest {
    return {
        limit: q.limit,
        offset: q.offset,
        status: q.status,
        // scope: q.scope,
        sort: q.sort,
    }
}

export function toArchivedAlertListRequest(
    q: ArchivedAlertListQuery,
): ArchivedAlertListRequest {
    return {
        limit: q.limit,
        offset: q.offset,
        sort: q.sort,
    }
}

export function toAlertTypeListRequest(q: AlertTypeListQuery): AlertTypeListRequest {
    return {
        limit: q.limit,
        offset: q.offset,
        search: q.search
    }
}

export function toAlertSaveRequest(q: AlertSaveQuery): AlertSaveRequest {
    return {
        name: q.name,
        exchange_instrument_id: q.exchangeInstrumentId,
        alert_type_id: q.alertTypeId,

        is_once: q.isOnce,
        status: q.status,
        scope: q.scope,

        throttle_timeframe: q.throttleTimeframe,
        timezone: q.timezone,

        use_validity: q.useValidity,
        valid_from: q.validFrom,
        valid_to: q.validTo,

        timeframe: q.timeframe,
        period: q.period,

        params: q.params,
    }
}



