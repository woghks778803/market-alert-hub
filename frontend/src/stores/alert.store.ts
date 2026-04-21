import { defineStore } from "pinia";
import { ref } from "vue";
import type { AlertSummaryDto, AlertDto, AlertTypeDto, AlertTypeListQuery, ArchivedAlertListQuery, AlertListQuery, AlertSaveQuery } from "@/services/alert.types"
import { AlertStatusFilter, AlertSort, AlertStatus, AlertListMode } from "@/services/alert.types"
import * as alertService from "@/services/alert.service";

export const useAlertStore = defineStore("alert", () => {
    const alertTypes = ref<AlertTypeDto[]>([])
    const alert = ref<AlertDto | null>(null)
    const alerts = ref<AlertDto[]>([])
    const alertSummary = ref<AlertSummaryDto | null>(null)

    const currentAlertStatus = ref<AlertStatusFilter>(AlertStatusFilter.ALL)
    const currentAlertSort = ref<AlertSort>(AlertSort.RECENT_UPDATED)

    const alertTypeListQuery = ref<AlertTypeListQuery>({
        search: "",
    })

    const alertListQuery = ref<AlertListQuery>({
        limit: 50,
        offset: 0,
    })
    const archivedAlertListQuery = ref<ArchivedAlertListQuery>({
        limit: 50,
        offset: 0,
    })
    const alertHasMore = ref(true)
    const alertLoadingMore = ref(false)

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

    async function fetchAlerts(options?: { append?: boolean }) {
        const append = options?.append ?? false
        if (alertLoadingMore.value) return
        if (append && !alertHasMore.value) return

        alertLoadingMore.value = true

        const limit = alertListQuery.value.limit ?? 50
        const prevOffset = alertListQuery.value.offset ?? 0

        try {
            if (!append) {
                alertListQuery.value.offset = 0
                alertHasMore.value = true
            } else {
                alertListQuery.value.offset = prevOffset + limit
            }

            const rows = await alertService.getAlerts(alertListQuery.value)

            alerts.value = [
                ...alerts.value,
                ...rows,
            ]

            console.log("fetchAlerts", alerts)

            if (rows.length < limit) {
                alertHasMore.value = false
            }
        } catch (err) {
            alertListQuery.value.offset = prevOffset
            throw err
        } finally {
            alertLoadingMore.value = false
        }
    }

    async function fetchArchivedAlerts(options?: { append?: boolean }) {
        const append = options?.append ?? false
        if (alertLoadingMore.value) return
        if (append && !alertHasMore.value) return

        alertLoadingMore.value = true

        const limit = archivedAlertListQuery.value.limit ?? 50
        const prevOffset = archivedAlertListQuery.value.offset ?? 0

        try {
            if (!append) {
                archivedAlertListQuery.value.offset = 0
                alertHasMore.value = true
            } else {
                archivedAlertListQuery.value.offset = prevOffset + limit
            }

            const rows = await alertService.getArchivedAlerts(archivedAlertListQuery.value)

            alerts.value = [
                ...alerts.value,
                ...rows,
            ]

            console.log("fetchArchivedAlerts", alerts)

            if (rows.length < limit) {
                alertHasMore.value = false
            }
        } catch (err) {
            archivedAlertListQuery.value.offset = prevOffset
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
        if (status === AlertStatusFilter.ALL) return undefined
        if (status === AlertStatusFilter.ACTIVE) return AlertStatus.ACTIVE
        if (status === AlertStatusFilter.PAUSED) return AlertStatus.PAUSED

        return undefined
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
        alertSummary.value = null

        alertHasMore.value = true
        alertLoadingMore.value = false
    }

    return {
        alertTypes,
        alert,
        alerts,
        alertSummary,

        currentAlertStatus,
        currentAlertSort,
        alertHasMore,
        alertLoadingMore,

        setStatus,
        setSort,
        resetAlert,

        fetchAlert,
        fetchAlertSummary,
        fetchAlertTypes,
        fetchAlerts,
        fetchArchivedAlerts,
        createAlert,
        changeAlert,
        changeAlertStatus,
        removeAlert,
    };
});