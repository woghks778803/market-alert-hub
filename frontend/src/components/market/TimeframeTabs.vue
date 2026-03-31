<template>

<div class="mk-tabs">

    <v-chip-group
      selected-class="mk-tab-active"
      :model-value="currentTimeframe"
      @update:modelValue="onUpdate"
    >
      <v-chip
        v-for="tab in tabs"
        :key="tab.value"
        :value="tab.value"
      >
        {{ tab.label }}
      </v-chip>
    </v-chip-group>

  </div>

</template>

<script setup lang="ts">
import { storeToRefs } from "pinia"
import type { ChartTimeframe } from "@/services/market.types"
import { useMarketStore } from "@/stores/market.store"

const marketStore = useMarketStore()
const { currentTimeframe } = storeToRefs(marketStore)

const tabs = [
  { label: "1m", value: "1m" },
  { label: "1h", value: "1h" },
  { label: "1d", value: "1d" },
]

async function onUpdate(val: ChartTimeframe) {
  await marketStore.changeTimeFrame(val)
}
</script>