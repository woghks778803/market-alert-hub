<template>
  <div class="rs-type-form">
    <div class="rs-field-block">
      <div class="rs-field-label">기준값</div>
      <v-text-field
        v-model="localValue.threshold"
        variant="solo-filled"
        flat
        rounded="lg"
        density="comfortable"
        hide-details="auto"
        inputmode="decimal"
        placeholder="교차 기준값 입력"
        :error="!!error?.threshold"
        :error-messages="error?.threshold ? [error?.threshold] : []"
      />
    </div>

    <div class="rs-field-block">
      <div class="rs-field-label">확인 캔들 수</div>
      <v-select
        v-model="localValue.confirmBars"
        :items="confirmBarOptions"
        itme-title="title"
        item-value="value"
        variant="solo-filled"
        flat
        rounded="lg"
        density="comfortable"
        hide-details="auto"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import type { CrossFormValue } from "@/services/alert.types"

const props = defineProps<{
  modelValue: CrossFormValue
  error?: Record<string, string> | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: CrossFormValue): void
  (e: "blur"): void
  (e: "input"): void
}>()

const confirmBarOptions = [
  { title: '즉시 (1캔들)', value: 1 },
  { title: '2캔들 확인', value: 2 },
  { title: '3캔들 확인', value: 3 },
  { title: '5캔들 확인', value: 5 },
]

const localValue = reactive<CrossFormValue>({
  threshold: props.modelValue?.threshold ?? '',
  confirmBars: props.modelValue?.confirmBars ?? 1,
})

watch(
  () => props.modelValue,
  (value) => {
    if (!value) return
    localValue.threshold = value.threshold
    localValue.confirmBars = value.confirmBars
  },
  { deep: true },
)

watch(
  localValue,
  () => {
    emit('update:modelValue', {
      threshold: localValue.threshold,
      confirmBars: localValue.confirmBars,
    })
  },
  { deep: true },
)

function onBlur() {
  emit('blur')
}

function onInput() {
  emit('input')
}
</script>