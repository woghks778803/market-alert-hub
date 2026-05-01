<template>
    <AppLoading :show="logAction.loading.value" overlay />

    <div class="alert-container">
        <div class="alert-summary">
            <div>
                <div class="alert-summary-title">최근 알림 기록</div>
                <div class="alert-summary-desc">
                    최근 7일간의 알림 기록만 표시됩니다. (최근 500건)
                </div>
            </div>

            <div class="alert-summary-count">
                {{ alertLogs.length }}건
            </div>
        </div>
        
        <LogFilter 
            :status="currentAlertEventStatus" 
            @change-status="handleFilterStatus"
        />

        <v-infinite-scroll
            :key="currentAlertListKey"
            class="alert-rule-list"
            :disabled="!alertHasMore || alertLoadingMore"
            @load="handleLoadMore"
        >
            <LogCard
                v-for="log in alertLogs"
                :key="log.alertEventId"
                :log="log"
            />

            <template #loading>
                <div class="alert-list-loading">
                    불러오는 중...
                </div>
            </template>

            <template #empty>
                <div class="alert-list-empty">
                    더 이상 보관된 알림이 없습니다.
                </div>
            </template>
        </v-infinite-scroll>

    </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { storeToRefs } from "pinia"

import AppLoading from "@/components/common/AppLoading.vue"
import LogCard from "@/components/alert/LogCard.vue"
import LogFilter from "@/components/alert/LogFilter.vue"

import { useAsyncAction } from "@/composables/common/useAsyncAction"

import {
  AlertEventStatusFilter,
} from "@/services/alert.types"
import { useAlertStore } from "@/stores/alert.store"

const logAction = useAsyncAction()
const alertStore = useAlertStore()
const { 
    alertLogs, 
    currentAlertListKey, 
    currentAlertEventStatus, 
    alertHasMore, 
    alertLoadingMore
} = storeToRefs(alertStore)

const initialLoaded = ref(false)

onMounted(async () => {
  alertStore.resetAlert()

  await logAction.run(async () => {
    await alertStore.fetchAlertLogs()
  })

  initialLoaded.value = true
})

const handleFilterStatus = async (status: AlertEventStatusFilter) => {
  await logAction.run(() => {
    alertStore.setEventStatus(status)
  })
}

const handleLoadMore = async ({ done }: { done: (status: "ok" | "empty" | "error") => void }) => {
  if (!initialLoaded.value) {
    done("ok")
    return
  }

  if (!alertHasMore.value) {
    done("empty")
    return
  }

  try {
    await alertStore.fetchAlertLogs({ append: true })

    done(alertHasMore.value ? "ok" : "empty")
  } catch {
    done("error")
  }
}
</script>