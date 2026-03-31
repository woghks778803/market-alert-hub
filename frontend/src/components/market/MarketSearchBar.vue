<template>
  <v-text-field
    placeholder="심볼/마켓 검색"
    prepend-inner-icon="mdi-magnify"
    variant="solo"
    density="comfortable"
    hide-details
    class="mk-search"
    :model-value="marketListQuery.search"
    @update:modelValue="onInput"
  />
</template>

<script setup lang="ts">
import { storeToRefs } from "pinia"
import { useMarketStore } from "@/stores/market.store"

const marketStore = useMarketStore()
const { marketListQuery } = storeToRefs(marketStore)

const emit = defineEmits<{
  (e: "search", value: string): void
}>()

function onInput(v: string) {
  emit("search", v)
}
</script>
