<template>
  <v-text-field
    :model-value="marketListQuery.search"
    placeholder="심볼/마켓 검색"
    prepend-inner-icon="mdi-magnify"
    variant="solo"
    density="comfortable"
    rounded="lg"
    hide-details
    clearable
    flat
    class="mk-search"
    @update:model-value="onInput"
  />
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useMarketStore } from '@/stores/market.store'

const marketStore = useMarketStore()
const { marketListQuery } = storeToRefs(marketStore)

const emit = defineEmits<{
  (e: 'search', value: string): void
}>()

function onInput(v: string) {
  emit('search', v)
}
</script>
