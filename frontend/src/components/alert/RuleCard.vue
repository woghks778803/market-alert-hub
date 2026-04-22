<template>
  <v-card class="alert-rule-card">
    <div class="alert-rule-header">
      <div class="alert-rule-title-group">
        <div class="alert-rule-market">
          <span
            class="alert-rule-symbol"
            :class="{ inactive: !alert.exchangeInstrumentIsActive }"
          >
            {{ alert.exchangeSymbol }}
          </span>

          <span
            class="alert-rule-exchange"
            :class="{ inactive: !alert.exchangeIsActive }"
          >
            {{ alert.exchangeCode }}
          </span>

          <span
            class="alert-rule-status"
            :class="alert.status"
          >
            {{ AlertStatusLabel[alert.status] }}
          </span>
        </div>

      </div>

      <div class="alert-rule-actions">
        <v-switch
          v-if="!isArchived"
          :model-value="alert.status === AlertStatus.ACTIVE"
          @click.stop.prevent="onChangeStatus"
          density="compact"
          hide-details
          inset
        />

        <v-menu location="bottom end">
          <template #activator="{ props }">
            <v-btn
              v-bind="props"
              icon
              variant="text"
              size="small"
              class="alert-rule-more-btn"
            >
              <v-icon>mdi-dots-vertical</v-icon>
            </v-btn>
          </template>

          <v-list density="compact" class="alert-rule-menu">
            <v-list-item 
              v-if="!isArchived"
              @click="goDetail"
            >
              <template #prepend>
                <v-icon size="18">mdi-eye-outline</v-icon>
              </template>
              <v-list-item-title>상세 보기</v-list-item-title>
            </v-list-item>

            <v-list-item 
              v-if="!isArchived"
              @click="onArchive"
            >
              <template #prepend>
                <v-icon size="18">mdi-archive-outline</v-icon>
              </template>
              <v-list-item-title>보관함으로 이동</v-list-item-title>
            </v-list-item>

            <v-list-item
              v-if="isArchived"
              @click="onRestore"
            >
              <template #prepend>
                <v-icon size="18">mdi-archive-arrow-up-outline</v-icon>
              </template>
              <v-list-item-title>보관 해제</v-list-item-title>
            </v-list-item>

            <v-list-item @click="onDelete">
              <template #prepend>
                <v-icon size="18">mdi-delete-outline</v-icon>
              </template>
              <v-list-item-title>삭제</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>

      </div>
    </div>

    <div class="alert-rule-condition">
      {{ alert.name }}
    </div>

    <div class="alert-rule-meta">
      <div class="alert-rule-meta-main">
        {{ formatTimeFrame(alert.params) }}
        ·
        {{ formatThrottleSeconds(alert.isOnce, alert.throttleSeconds) }}
      </div>

      <div class="alert-rule-meta-date">
        마지막 수정 {{ formatDate(alert.updatedAt) }}
      </div>
    </div>
  </v-card>
</template>

<script setup lang="ts">
import {computed} from "vue"
import type { AlertDto } from "@/services/alert.types"
import { AlertStatus, AlertStatusLabel } from "@/services/alert.types"
import { formatDate, formatThrottleSeconds, formatTimeFrame } from "@/utils/format"
const isArchived = computed(() => props.alert.status === AlertStatus.ARCHIVED)
const props = defineProps<{
  alert: AlertDto
}>()

const emit = defineEmits<{
  (e: "detail", value: { alertId: number }): void,
  (e: "delete", value: AlertDto): void,
  (e: "archive", value: AlertDto): void,
  (e: "restore", value: AlertDto): void,
  (e: "changeStatus", value: AlertDto): void,
}>()

const goDetail = () => {
  emit("detail", { alertId: props.alert.id })
}

const onChangeStatus = () => {
  emit("changeStatus", props.alert)
}

const onArchive = () => {
  emit("archive", props.alert)
}

const onRestore = () => {
  emit("restore", props.alert)
}

const onDelete = () => {
  emit("delete", props.alert)
}

</script>