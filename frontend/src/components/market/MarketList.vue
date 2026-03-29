<template>

  <div class="mk-list">

    <MarketItem
      v-for="item in items"
      :key="item.exchange + ':' + item.symbol"
      :item="item"
      @select="goDetail"
    />

  </div>

</template>


<script setup lang="ts">
import { useRouter } from "vue-router";
import type { MarketDto } from "@/services/market.types"
import MarketItem from '@/components/market/MarketItem.vue'

const router = useRouter();

// <{}>() 타입 문법
defineProps<{
  items: MarketDto[],
}>()

function goDetail(payload: { exchange: string; symbol: string }) {
  router.push({
    name: 'SymbolDetail',
    params: payload,
  })
  // console.log('Navigate to detail view for', payload)
}
</script>
