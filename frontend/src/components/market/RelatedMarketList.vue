<script setup lang="ts">
import type { MarketDto } from '@/services/market.types'
import RelatedMarketItem from './RelatedMarketItem.vue'

defineProps<{
  items: MarketDto[]
}>()

const emit = defineEmits<{
  select: [market: MarketDto]
}>()
</script>

<template>
  <div class="mk-list">
    <RelatedMarketItem
      v-for="item in items"
      :key="item.exchangeInstrumentId"
      :item="item"
      @select="emit('select', $event)"
    >
      <template #chip>
        <slot
          name="chip"
          :market="item"
        />
      </template>
    </RelatedMarketItem>
  </div>
</template>