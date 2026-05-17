<template>
  <div class="alert-summary">
    <div class="alert-summary-left">
      <!-- <span class="alert-rule-title">야간 알림 허용</span>

      <v-switch
        v-if="me"
        :model-value="me.isQuietHours"
        density="compact"
        hide-details
        @update:model-value="userStore.setQuietHours"
      /> -->
    </div>

    <div class="alert-summary-right">
      전체 {{ alertSummary?.totalCount ?? 0 }} · 활성 {{ alertSummary?.activeCount ?? 0 }} ·
      일시정지 {{ alertSummary?.pausedCount ?? 0 }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useAlertStore } from '@/stores/alert.store'

const alertStore = useAlertStore()
const { alertSummary } = storeToRefs(alertStore)
</script>
