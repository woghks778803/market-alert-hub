<template>
  <div class="mk-tabs">
    <v-chip-group
      selected-class="mk-tab-active"
      multiple
      :model-value="currentSystemTab"
      @update:model-value="onUpdate"
    >
      <v-chip
        v-for="tab in tabs"
        :key="tab.code"
        :value="tab.code"
      >
        {{ tab.name }}
      </v-chip>
    </v-chip-group>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import type { ExchangeDto } from '@/services/market.types'
import { useMarketStore } from '@/stores/market.store'

const marketStore = useMarketStore()
const { currentSystemTab } = storeToRefs(marketStore)

const props = defineProps<{
  exchangeTabs: ExchangeDto[]
}>()

const emit = defineEmits<{
  (e: 'change', value: string[]): void
}>()

const systemTabs = [
  { name: '전체', code: 'all' },
  { name: '즐겨찾기', code: 'watchlist' },
]

const tabs = computed(() => [...systemTabs, ...props.exchangeTabs])

function onUpdate(val: string[]) {
  emit('change', val)
}
</script>
