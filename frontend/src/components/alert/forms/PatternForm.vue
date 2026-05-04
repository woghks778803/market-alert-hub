<template>
  <div class="rs-type-form">
    <div class="rs-field-block">
      <div class="rs-field-label">패턴</div>
      <v-select
        :model-value="modelValue.pattern"
        :items="patternItems"
        item-title="title"
        item-value="value"
        variant="solo-filled"
        flat
        rounded="lg"
        density="comfortable"
        hide-details="auto"
        placeholder="패턴 선택"
      />
    </div>

    <div class="rs-field-block">
      <div class="rs-field-label">기간</div>
      <v-select
        :model-value="modelValue.period"
        :items="periodItems"
        item-title="title"
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
import type { PatternFormValue } from '@/services/alert.types'

defineProps<{
  modelValue: PatternFormValue
  error?: Record<string, string> | null
}>()

defineEmits<{
  (e: 'update:modelValue', value: PatternFormValue): void
  (e: 'blur'): void
  (e: 'input'): void
}>()

const patternItems = [
  { title: '골든 크로스', value: 'golden_cross' },
  { title: '데드 크로스', value: 'dead_cross' },
  { title: '상승 다이버전스', value: 'bullish_divergence' },
  { title: '하락 다이버전스', value: 'bearish_divergence' },
]

const periodItems = [
  { title: '5분', value: 5 },
  { title: '15분', value: 15 },
  { title: '1시간', value: 60 },
  { title: '4시간', value: 240 },
  { title: '1일', value: 1440 },
]
</script>
