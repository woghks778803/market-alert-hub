<template>
  <AppLoading :show="ruleAction.loading.value" overlay />

  <div class="alert-rules-container">

    <div v-if="!initialLoaded" class="alert-list-loading">
        불러오는 중...
    </div>

    <v-infinite-scroll
        class="alert-rule-list"
        :disabled="!alertHasMore || alertLoadingMore"
        @load="handleLoadMore"
    >
        <RuleCard
            v-for="alert in alerts"
            :key="alert.id"
            :alert="alert"
            @restore="handleRestore"
            @delete="handleDelete"
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

<ConfirmDialog
  v-model="showConfirmDialog"
  title="알림 삭제"
  :message="`
  정말로 이 알림을 삭제하시겠습니까?

  삭제한 알림은 목록에서 제거되며,
  다시 복구할 수 없습니다.
  `"
  confirm-text="삭제"
  cancel-text="취소"
  danger
  :loading="ruleAction.loading.value"
  :is-ready="ruleAction.isReady.value"
  @confirm="handleConfirmDelete"
/>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue"
import { useRoute } from 'vue-router'
import { toast } from 'vue3-toastify'
import { storeToRefs } from "pinia"

import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import AppLoading from "@/components/common/AppLoading.vue"
import RuleCard from "@/components/alert/RuleCard.vue"

import { useAsyncAction } from "@/composables/common/useAsyncAction"
import { mapCommonError } from "@/composables/error/error.mapper"
import { mapAlertUpdateStatusError } from "@/composables/error/alertError.mapper"

import {
  type AlertDto,
  AlertListMode,
  AlertStatus
} from "@/services/alert.types"
import { useAlertStore } from "@/stores/alert.store"

const route = useRoute()
const mode = route.meta.mode as AlertListMode
const ruleAction = useAsyncAction()
const alertStore = useAlertStore()
const { alerts, alertHasMore, alertLoadingMore } = storeToRefs(alertStore)

const initialLoaded = ref(false)
const showConfirmDialog = ref(false)
const deleteTargetAlert = ref<AlertDto | null>(null)

onMounted(async () => {
  alertStore.resetAlert()
  
  await ruleAction.run(async () => {
    await alertStore.fetchArchivedAlerts()
  })

  initialLoaded.value = true
})

const handleRestore = async (alert: AlertDto) => {
  try {
    await ruleAction.run(async () => {
      await alertStore.changeAlertStatus(alert, AlertStatus.PAUSED, mode)
    })
  } catch (err: any) {
    const apiError = err?.response?.data?.error

    const r = mapAlertUpdateStatusError(apiError)
    if (r) {
      toast.error(r, {
        toastId: "alert-status-update-failed",
      })
      return
    }

    const commonMessage = mapCommonError(apiError)
    if (commonMessage) {
      toast.error(commonMessage, {
        toastId: "alert-status-update-failed",
      })
      return
    }
  }
}

const handleDelete = async (alert: AlertDto) => {
  showConfirmDialog.value = true
  deleteTargetAlert.value = alert
}

const handleConfirmDelete = async () => {
  if (!deleteTargetAlert.value) return

  const alertId = deleteTargetAlert.value.id

  await ruleAction.run(async () => {
    await alertStore.removeAlert(alertId)
  })

  showConfirmDialog.value = false
  deleteTargetAlert.value = null
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
    await alertStore.fetchArchivedAlerts({ append: true })

    done(alertHasMore.value ? "ok" : "empty")
  } catch {
    done("error")
  }
}
</script>