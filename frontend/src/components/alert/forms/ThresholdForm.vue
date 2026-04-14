<template>
  <div class="rs-type-form">
    <div class="rs-field-block">
      <div class="rs-field-label">기준값</div>
      <v-text-field
        v-model="modelValue.threshold"
        variant="solo-filled"
        flat
        rounded="lg"
        density="comfortable"
        hide-details="auto"
        inputmode="decimal"
        placeholder="기준값 입력"
        :error="!!error?.threshold"
        :error-messages="error?.threshold ? [error?.threshold] : []"
        @update:model-value="onInput"
        @blur="onBlur"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ThresholdFormValue } from "@/services/alert.types" 

const props = defineProps<{
  modelValue: ThresholdFormValue
  error?: Record<string, string> | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: ThresholdFormValue): void
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