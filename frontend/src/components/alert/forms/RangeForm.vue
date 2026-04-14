<template>
  <div class="rs-type-form">
    <div class="rs-field-row">
      <div class="rs-field-col">
        <div class="rs-field-label">최소값</div>
        <v-text-field
          v-model="modelValue.minValue"
          variant="solo-filled"
          flat
          rounded="lg"
          density="comfortable"
          hide-details="auto"
          inputmode="decimal"
          placeholder="최소값"
          :error="!!error?.minValue"
          :error-messages="error?.minValue ? [error?.minValue] : []"
        />
      </div>

      <div class="rs-field-col">
        <div class="rs-field-label">최대값</div>
        <v-text-field
          v-model="modelValue.maxValue"
          variant="solo-filled"
          flat
          rounded="lg"
          density="comfortable"
          hide-details="auto"
          inputmode="decimal"
          placeholder="최대값"
          :error="!!error?.maxValue"
          :error-messages="error?.maxValue ? [error?.maxValue] : []"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { RangeFormValue } from "@/services/alert.types"

const props = defineProps<{
  modelValue: RangeFormValue
  error?: Record<string, string> | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: RangeFormValue): void
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