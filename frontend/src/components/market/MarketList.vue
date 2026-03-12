<template>

  <div class="mk-list">

    <MarketItem
      v-for="item in items"
      :key="item.symbol"
      :item="item"
    />

  </div>

</template>


<script setup lang="ts">
import MarketItem from '@/components/market/MarketItem.vue'
defineProps({
  items: Array
})
</script>
