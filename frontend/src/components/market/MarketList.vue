<template>

  <div class="mk-list">

    <MarketItem
      v-for="item in items"
      :key="item.id"
      :item="item"
    />

  </div>

</template>


<script setup lang="ts">
import type { MarketDto } from "@/services/market.types"
import MarketItem from '@/components/market/MarketItem.vue'
// <{}>() 타입 문법
defineProps<{
  items: MarketDto[],
}>()
</script>
