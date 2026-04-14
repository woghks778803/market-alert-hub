<template>
  <div class="rs-type-form">
    <div class="rs-field-block">
      <div class="rs-field-label">퍼센트(%)</div>
      <v-text-field
        v-model="modelValue.percent"
        variant="solo-filled"
        flat
        rounded="lg"
        density="comfortable"
        hide-details="auto"
        inputmode="decimal"
        placeholder="예: 5"
        :error="!!error?.percent"
        :error-messages="error?.percent ? [error?.percent] : []"
        @update:model-value="onInput"
        @blur="onBlur"
      />
      <div class="rs-form-helper-text">
        변동률은 알림 생성 시점의 현재가를 기준으로 계산됩니다.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PercentFormValue } from "@/services/alert.types"

const props = defineProps<{
  modelValue: PercentFormValue
  error?: Record<string, string> | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: PercentFormValue): void
  (e: "blur"): void
  (e: "input"): void
}>()

function onBlur() {
  emit('blur')
}

function onInput() {
  emit('input')
}
</script>