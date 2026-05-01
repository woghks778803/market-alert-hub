import { defineStore } from "pinia";
import { ref } from "vue";
import type {
    AlertSummaryDto,
    AlertDto,
    AlertLogDto,
    AlertTypeDto,
    AlertLogListQuery,
    AlertTypeListQuery,
    ArchivedAlertListQuery,
    AlertListQuery,
    AlertSaveQuery
} from "@/services/alert.types"
import {
    AlertEventStatusFilter,
    AlertStatusFilter,
    AlertSort,
    AlertStatus,
    AlertEventStatus,
    AlertListMode,
    MAX_ALERT_LOGS_LIMIT,
    MAX_ARCHIVED_ALERTS_LIMIT,
    MAX_NON_ARCHIVED_ALERTS_LIMIT,
} from "@/services/alert.types"
import * as alertService from "@/services/alert.service";

export const useAlertStore = defineStore("alert", () => {
    const alertTypes = ref<AlertTypeDto[]>([])
    const alertLogs = ref<AlertLogDto[]>([])
    const alert = ref<AlertDto | null>(null)
    const alerts = ref<AlertDto[]>([])
    const alertSummary = ref<AlertSummaryDto | null>(null)

    const currentAlertListKey = ref<number>(0)
    const currentAlertStatus = ref<AlertStatusFilter>(AlertStatusFilter.ALL)
    const currentAlertSort = ref<AlertSort>(AlertSort.RECENT_UPDATED)
    const currentAlertEventStatus = ref<AlertEventStatusFilter>(AlertEventStatusFilter.ALL)

    const alertNextCursor = ref<string | null>(null)
    const alertHasMore = ref(true)
    const alertLoadingMore = ref(false)

    const alertTypeListQuery = ref<AlertTypeListQuery>({
        search: "",
    })

    const alertLogListQuery = ref<AlertLogListQuery>({
        limit: 50,
        cursor: undefined,
    })

    const alertListQuery = ref<AlertListQuery>({
        limit: 50,
        cursor: undefined,
    })

    const archivedAlertListQuery = ref<ArchivedAlertListQuery>({
        limit: 50,
        cursor: undefined,
    })

    const AlertSaveQuery = ref<AlertSaveQuery | null>(null)

    async function fetchAlert(id: number) {
        const result = await alertService.getAlert(id)
        alert.value = result
        console.log("fetchAlert", alert.value)
        return result
    }

    async function fetchAlertTypes() {
        alertTypes.value = await alertService.getAlertTypes(alertTypeListQuery.value)
        console.log("fetchAlertTypes", alertTypes)
    }

    async function fetchAlertLogs(options?: { append?: boolean }) {
        const append = options?.append ?? false
        if (alertLoadingMore.value) return
        if (append && !alertHasMore.value) return
        if (alertLogs.value.length >= MAX_ALERT_LOGS_LIMIT) {
            alertHasMore.value = false
            return
        }

        alertLoadingMore.value = true

        const prevCursor = alertLogListQuery.value.cursor ?? undefined

        try {
            if (!append) {
                alertLogs.value = []
                currentAlertListKey.value += 1
                alertHasMore.value = true
                alertLogListQuery.value.cursor = undefined
            } else {
                alertLogListQuery.value.cursor = alertNextCursor.value ?? undefined
            }

            const result = await alertService.getAlertLogs(alertLogListQuery.value)

            const rows = result.items

            alertLogs.value = append
                ? [
                    ...alertLogs.value, ...rows,
                ] : rows

            alertNextCursor.value = result.page?.next_cursor ?? null
            alertHasMore.value = result.page?.has_next ?? false
        } catch (err) {
            alertLogListQuery.value.cursor = prevCursor
            throw err
        } finally {
            alertLoadingMore.value = false
        }
    }

    async function fetchAlerts(options?: { append?: boolean }) {
        const append = options?.append ?? false
        if (alertLoadingMore.value) return
        if (append && !alertHasMore.value) return
        if (alerts.value.length >= MAX_NON_ARCHIVED_ALERTS_LIMIT) {
            alertHasMore.value = false
            return
        }

        alertLoadingMore.value = true

        const prevCursor = alertListQuery.value.cursor ?? undefined

        try {
            if (!append) {
                alerts.value = []
                currentAlertListKey.value += 1
                alertHasMore.value = true
                alertListQuery.value.cursor = undefined
            } else {
                alertListQuery.value.cursor = alertNextCursor.value ?? undefined
            }

            const result = await alertService.getAlerts(alertListQuery.value)

            const rows = result.items

            alerts.value = append
                ? [
                    ...alerts.value, ...rows,
                ] : rows

            alertNextCursor.value = result.page?.next_cursor ?? null
            alertHasMore.value = result.page?.has_next ?? false
        } catch (err) {
            alertListQuery.value.cursor = prevCursor
            throw err
        } finally {
            alertLoadingMore.value = false
        }
    }

    async function fetchArchivedAlerts(options?: { append?: boolean }) {
        const append = options?.append ?? false
        if (alertLoadingMore.value) return
        if (append && !alertHasMore.value) return
        if (alerts.value.length >= MAX_ARCHIVED_ALERTS_LIMIT) {
            alertHasMore.value = false
            return
        }

        alertLoadingMore.value = true

        const prevCursor = archivedAlertListQuery.value.cursor ?? undefined

        try {
            if (!append) {
                alerts.value = []
                currentAlertListKey.value += 1
                alertHasMore.value = true
                archivedAlertListQuery.value.cursor = undefined
            } else {
                archivedAlertListQuery.value.cursor = alertNextCursor.value ?? undefined
            }

            const result = await alertService.getArchivedAlerts(archivedAlertListQuery.value)

            const rows = result.items

            alerts.value = append
                ? [
                    ...alerts.value, ...rows,
                ] : rows

            alertNextCursor.value = result.page?.next_cursor ?? null
            alertHasMore.value = result.page?.has_next ?? false
        } catch (err) {
            archivedAlertListQuery.value.cursor = prevCursor
            throw err
        } finally {
            alertLoadingMore.value = false
        }
    }

    async function fetchAlertSummary() {
        alertSummary.value = await alertService.getAlertSummary()
    }

    async function createAlert(payload: AlertSaveQuery) {
        AlertSaveQuery.value = payload
        await alertService.createAlert(AlertSaveQuery.value)
    }

    async function changeAlert(id: number, payload: AlertSaveQuery) {
        AlertSaveQuery.value = payload
        await alertService.changeAlert(id, AlertSaveQuery.value)
    }

    async function changeAlertStatus(alert: AlertDto, status: AlertStatus, mode: AlertListMode = AlertListMode.ALERTS,) {
        await alertService.changeAlertStatus(alert.id, { status: status })

        if (!shouldKeepAlertInCurrentList(status, mode)) {
            alerts.value = alerts.value.filter((item) => item.id !== alert.id)
        } else {
            alert.status = status
        }

        await fetchAlertSummary()
    }

    async function removeAlert(id: number) {
        await alertService.removeAlert(id)
        alerts.value = alerts.value.filter((item) => item.id !== id)
        await fetchAlertSummary()
    }

    // 해당 목록 item의 필터 여부 검증
    function shouldKeepAlertInCurrentList(status: AlertStatus, mode: AlertListMode): boolean {
        if (mode === AlertListMode.ARCHIVES) {
            return status === AlertStatus.ARCHIVED
        }

        if (status === AlertStatus.ARCHIVED) {
            return false
        }

        if (currentAlertStatus.value === AlertStatusFilter.ALL) {
            return true
        }

        if (currentAlertStatus.value === AlertStatusFilter.ACTIVE) {
            return status === AlertStatus.ACTIVE
        }

        if (currentAlertStatus.value === AlertStatusFilter.PAUSED) {
            return status === AlertStatus.PAUSED
        }

        return true
    }

    function toAlertStatus(status: AlertStatusFilter): AlertStatus | undefined {
        if (status === AlertStatusFilter.ACTIVE) return AlertStatus.ACTIVE
        if (status === AlertStatusFilter.PAUSED) return AlertStatus.PAUSED

        return undefined
    }

    function toAlertEventStatus(status: AlertEventStatusFilter): AlertEventStatus | undefined {
        if (status === AlertEventStatusFilter.DISPATCHED) return AlertEventStatus.DISPATCHED
        if (status === AlertEventStatusFilter.SKIPPED) return AlertEventStatus.SKIPPED

        return undefined
    }

    function setEventStatus(status: AlertEventStatusFilter) {
        currentAlertEventStatus.value = status

        alertLogListQuery.value.status = toAlertEventStatus(status)
        fetchAlertLogs()
    }

    function setStatus(status: AlertStatusFilter) {
        currentAlertStatus.value = status

        alertListQuery.value.status = toAlertStatus(status)
        fetchAlerts()
    }

    function setSort(sort: AlertSort) {
        currentAlertSort.value = sort

        alertListQuery.value.sort = currentAlertSort.value
        fetchAlerts()
    }

    function resetAlert() {
        alerts.value = []
        alertLogs.value = []
        alertSummary.value = null

        currentAlertListKey.value = 0
        alertNextCursor.value = null
        alertHasMore.value = true
        alertLoadingMore.value = false
    }

    return {
        alertTypes,
        alertLogs,
        alert,
        alerts,
        alertSummary,

        currentAlertListKey,
        currentAlertStatus,
        currentAlertSort,
        currentAlertEventStatus,
        alertHasMore,
        alertLoadingMore,

        setEventStatus,
        setStatus,
        setSort,
        resetAlert,

        fetchAlertSummary,
        fetchAlert,
        fetchAlertLogs,
        fetchAlertTypes,
        fetchAlerts,
        fetchArchivedAlerts,
        createAlert,
        changeAlert,
        changeAlertStatus,
        removeAlert,
    };
});