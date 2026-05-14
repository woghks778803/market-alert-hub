<template>
  <AppLoading
    :show="ruleAction.loading.value"
    overlay
  />

  <div>
    <RuleSummary />

    <RuleFilter
      :sort="currentAlertSort"
      :status="currentAlertStatus"
      @change-sort="handleChangeSort"
      @change-status="handleFilterStatus"
    />

    <v-infinite-scroll
      :key="currentAlertListKey"
      class="alert-rule-list"
      :disabled="!alertHasMore || alertLoadingMore"
      @load="handleLoadMore"
    >
      <RuleCard
        v-for="alert in alerts"
        :key="alert.id"
        :alert="alert"
        @detail="goDetail"
        @archive="handleArchive"
        @change-status="handleAlertStatus"
        @delete="handleDelete"
      />

      <template #loading>
        <div class="alert-list-loading">불러오는 중...</div>
      </template>

      <template #empty>
        <div class="alert-list-empty">더 이상 보관된 알림이 없습니다.</div>
      </template>
    </v-infinite-scroll>
  </div>

  <RuleAddFab />
  <ScrollTopButton
    :bottom-offset="170"
    :show-after="300"
  />

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
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import { storeToRefs } from 'pinia'

import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import AppLoading from '@/components/common/AppLoading.vue'
import ScrollTopButton from '@/components/common/ScrollTopButton.vue'
import RuleSummary from '@/components/alert/RuleSummary.vue'
import RuleFilter from '@/components/alert/RuleFilter.vue'
import RuleCard from '@/components/alert/RuleCard.vue'
import RuleAddFab from '@/components/alert/RuleAddFab.vue'

import { useAsyncAction } from '@/composables/common/useAsyncAction'
import { getChangeAlertStatusError } from '@/composables/error/alertError.message'

import {
  type AlertDto,
  AlertListMode,
  AlertSort,
  AlertStatus,
  AlertStatusFilter,
} from '@/services/alert.types'
import { useAlertStore } from '@/stores/alert.store'
import { useUserStore } from '@/stores/user.store'

const route = useRoute()
const router = useRouter()
const mode = route.meta.mode as AlertListMode
const ruleAction = useAsyncAction()
const alertStore = useAlertStore()
const userStore = useUserStore()
const {
  alerts,
  currentAlertSort,
  currentAlertStatus,
  currentAlertListKey,
  alertHasMore,
  alertLoadingMore,
} = storeToRefs(alertStore)

const initialLoaded = ref(false)
const showConfirmDialog = ref(false)
const deleteTargetAlert = ref<AlertDto | null>(null)

onMounted(async () => {
  alertStore.resetAlert()

  await ruleAction.run(async () => {
    await alertStore.fetchAlertSummary()
    await alertStore.fetchAlerts()
    await userStore.fetchMe()
  })

  initialLoaded.value = true
})

const goDetail = (payload: { alertId: number }) => {
  router.push({
    name: 'RuleDetail',
    params: payload,
  })
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

const handleArchive = async (alert: AlertDto) => {
  try {
    await ruleAction.run(async () => {
      await alertStore.changeAlertStatus(alert, AlertStatus.ARCHIVED, mode)
    })
  } catch (err) {
    const result = getChangeAlertStatusError(err)
    if (result) {
      toast.error(result, {
        toastId: 'alert-status-update-failed',
      })
      return
    }
  }
}

const handleAlertStatus = async (alert: AlertDto) => {
  const nextStatus = alert.status === AlertStatus.ACTIVE ? AlertStatus.PAUSED : AlertStatus.ACTIVE

  try {
    await alertStore.changeAlertStatus(alert, nextStatus, mode)
  } catch (err) {
    const result = getChangeAlertStatusError(err)
    if (result) {
      toast.error(result, {
        toastId: 'alert-status-update-failed',
      })
      return
    }
  }
}

const handleFilterStatus = async (status: AlertStatusFilter) => {
  await ruleAction.run(() => {
    alertStore.setStatus(status)
  })
}

const handleChangeSort = async (sort: AlertSort) => {
  await ruleAction.run(() => {
    alertStore.setSort(sort)
  })
}

const handleLoadMore = async ({ done }: { done: (status: 'ok' | 'empty' | 'error') => void }) => {
  if (!initialLoaded.value) {
    done('ok')
    return
  }

  if (!alertHasMore.value) {
    done('empty')
    return
  }

  try {
    await alertStore.fetchAlerts({ append: true })

    done(alertHasMore.value ? 'ok' : 'empty')
  } catch {
    done('error')
  }
}
</script>
