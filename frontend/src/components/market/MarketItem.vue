<template>
  <v-card
    class="mk-card"
    :class="{ flash }"
    tabindex="0"
    @click="goMarketDetail"
  >
    <v-card-text>
      <!-- row 1 -->
      <div class="mk-row-top">
        <div>
          <div class="mk-symbol">
            {{ item.exchangeSymbol }}
          </div>

          <div class="mk-exchange">{{ item.exchangeCode }} · {{ item.quoteSymbol }}</div>

          <div class="mk-name">
            {{ item.name }}
          </div>
        </div>

        <v-icon
          :icon="item.isWatchlisted ? 'mdi-star' : 'mdi-star-outline'"
          :color="item.isWatchlisted ? 'amber' : 'grey'"
          size="25"
          @click.stop.prevent="onToggle"
        />
      </div>

      <!-- row 2 -->
      <div class="mk-row-bottom">
        <div class="mk-price">
          {{ formatPrice(item.closePrice, getDecimalPlaces(item.closePrice)) }} {{ item.quoteSymbol }}
        </div>

        <div class="mk-change-block">
          <div
            class="mk-change"
            :class="item.change && item.change < 0 ? 'mk-change-down' : 'mk-change-up'"
          >
            {{ formatChange(item.changeRate) }}%
          </div>

          <div class="mk-volume">
            <div>거래량 {{ formatVolume(item.volume) }}</div>
            <div>거래대금(원) {{ formatVolume(item.normalizedVolume) }}</div>
          </div>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { formatChange, formatPrice, formatVolume } from '@/utils/format'
import { getDecimalPlaces } from '@/utils/number'
import type { MarketDto } from '@/services/market.types'
import { useMarketStore } from '@/stores/market.store'

const flash = ref(false)
const marketStore = useMarketStore()
const props = defineProps<{
  item: MarketDto
}>()

const emit = defineEmits<{
  (e: 'select', payload: { exchange: string; exchangeSymbol: string }): void
}>()

function goMarketDetail() {
  emit('select', {
    exchange: props.item.exchangeCode,
    exchangeSymbol: props.item.exchangeSymbol,
  })
}

async function onToggle() {
  // e: MouseEvent
  // e.stopPropagation()
  await marketStore.toggleWatchlist(props.item)
}

watch(
  () => [
    props.item.closePrice,
    props.item.changeRate,
    props.item.change,
    props.item.volume,
    props.item.normalizedVolume,
    props.item.normalizedPrice,
  ],
  (newVal, oldVal) => {
    if (oldVal === undefined) return
    if (newVal === oldVal) return
    triggerFlash()
  }
)

function triggerFlash() {
  flash.value = true

  setTimeout(() => {
    flash.value = false
  }, 500)
}
</script>
