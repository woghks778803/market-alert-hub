<template>
  <v-card
    class="alert-log-card"
    elevation="0"
  >
    <div class="alert-log-header">
      <div class="alert-log-title-group">
        <span class="alert-log-symbol">
          {{ log.exchangeSymbol }}
        </span>

        <span class="alert-log-exchange">
          {{ log.exchangeCode }}
        </span>

        <span
          class="alert-log-status"
          :class="log.status"
        >
          {{ AlertEventStatusLabel[log.status] }}
        </span>
      </div>
    </div>

    <div class="alert-log-title">
      {{ log.title }}
    </div>

    <div class="alert-log-body">
      {{ log.body }}
    </div>

    <div class="alert-log-meta">
      {{ formatDateTime(log.detectedAt) }}
    </div>
  </v-card>
</template>

<script setup lang="ts">
import type { AlertLogDto } from '@/services/alert.types'
import { AlertEventStatusLabel } from '@/services/alert.types'
import { formatDateTime } from '@/utils/format'

defineProps<{
  log: AlertLogDto
}>()
</script>
