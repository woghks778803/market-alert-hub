<template>
  <div class="mk-tabs">
    <v-chip-group
      mandatory
      selected-class="mk-tab-active"
      :model-value="modelValue"
      @update:model-value="onUpdate"
    >
      <v-chip
        v-for="(option, timeframe) in ChartTimeframeLabel"
        :key="timeframe"
        :value="timeframe"
      >
        {{ option.label }}
      </v-chip>
    </v-chip-group>
  </div>
</template>

<script setup lang="ts">
import type { ChartTimeframe } from '@/services/market.types'
import { ChartTimeframeLabel } from '@/services/market.types'

defineProps<{
  modelValue: ChartTimeframe
}>()

const emit = defineEmits<{
  'update:modelValue': [value: ChartTimeframe]
}>()

function onUpdate(value: ChartTimeframe): void {
  emit('update:modelValue', value)
}

</script>
