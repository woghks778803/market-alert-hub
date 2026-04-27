
export type AlertSummaryDto = {
    totalCount: number
    activeCount: number
    pausedCount: number
}

export type AlertDto = {
    id: number
    alertTypeId: number
    name: string
    status: AlertStatus

    timezone: string
    timeframe: string | null
    period: number | null
    params: Record<string, unknown>

    throttleSeconds: number
    isOnce: boolean
    validFrom: string | null
    validTo: string | null
    updatedAt: string

    exchangeInstrumentId: number,
    exchangeSymbol: string
    exchangeCode: string
    exchangeName: string
    exchangeInstrumentIsActive: boolean
    exchangeIsActive: boolean
}

export type AlertTypeDto = {
    id: number,
    code: string
    name: string

    indicator: string
    direction: string | null
    formType: FormType
    paramSchema: Record<string, unknown>
}

export type AlertListQuery = {
    limit?: number
    offset?: number
    status?: AlertStatus
    sort?: AlertSort
}

export type ArchivedAlertListQuery = {
    limit?: number
    offset?: number
    sort?: AlertSort
}

export type AlertTypeListQuery = {
    search: string
    limit?: number
    offset?: number
}

export type AlertSaveQuery = {
    name: string
    exchangeInstrumentId: number | null
    alertTypeId: number

    isOnce: boolean
    status: AlertStatus

    throttleTimeframe: ThrottleTimeframe
    timezone: string

    useValidity: boolean
    validFrom: string | null
    validTo: string | null

    params: Record<string, unknown>
}

export type CrossFormValue = {
    threshold: string
    confirmBars: number
}

export type PatternFormValue = {
    pattern: string
    period: string
}

export type PercentFormValue = {
    percent: string
}

export type RangeFormValue = {
    minValue: string
    maxValue: string
}

export type ThresholdFormValue = {
    threshold: string
}

export enum AlertSort {
    RECENT_UPDATED = "recent_updated",
    RECENT_CREATED = "recent_created",
    MARKET_ASC = "market_asc",
    STATUS = "status",
}

export enum AlertStatus {
    ACTIVE = "active",
    PAUSED = "paused",
    ARCHIVED = "archived",
}

export enum AlertStatusFilter {
    ALL = "all",
    ACTIVE = "active",
    PAUSED = "paused",
}

export enum ConditionType {
    SINGLE = "single",
    CROSS = "cross",
}

export enum FormType {
    THRESHOLD = "threshold",
    THRESHOLD_WITH_PERIOD = "threshold_with_period",
    RANGE = "range",
    PERCENT = "percent",
    PATTERN = "pattern",
    CROSS = "cross",
}

export enum ThrottleTimeframe {
    MIN_5 = "5m",
    MIN_10 = "10m",
    MIN_30 = "30m",
    HOUR_1 = "1h",
    HOUR_3 = "3h",
    HOUR_6 = "6h",
    HOUR_12 = "12h",
    DAY_1 = "1d",
}

export enum AlertListMode {
    ALERTS = "alerts",
    ARCHIVES = "archives",
}

export const AlertStatusLabel: Record<AlertStatus, string> = {
    [AlertStatus.ACTIVE]: "ON",
    [AlertStatus.PAUSED]: "OFF",
    [AlertStatus.ARCHIVED]: "보관",
}

export const AlertStatusFilterLabel: Record<AlertStatusFilter, string> = {
    [AlertStatusFilter.ALL]: "전체",
    [AlertStatusFilter.ACTIVE]: "활성",
    [AlertStatusFilter.PAUSED]: "일시정지",
}

export const ThrottleTimeframeLabel: Record<ThrottleTimeframe, string> = {
    [ThrottleTimeframe.MIN_5]: '5분',
    [ThrottleTimeframe.MIN_10]: '10분',
    [ThrottleTimeframe.MIN_30]: '30분',
    [ThrottleTimeframe.HOUR_1]: '1시간',
    [ThrottleTimeframe.HOUR_3]: '3시간',
    [ThrottleTimeframe.HOUR_6]: '6시간',
    [ThrottleTimeframe.HOUR_12]: '12시간',
    [ThrottleTimeframe.DAY_1]: '1일',
}

export const AlertSortLabel: Record<AlertSort, string> = {
    [AlertSort.RECENT_UPDATED]: "최근 수정",
    [AlertSort.RECENT_CREATED]: "최근 생성",
    [AlertSort.MARKET_ASC]: "마켓순",
    [AlertSort.STATUS]: "상태순",
}

export const THROTTLE_TIMEFRAME_ITEMS = Object.values(ThrottleTimeframe).map((value) => ({
    title: ThrottleTimeframeLabel[value],
    value,
}))
