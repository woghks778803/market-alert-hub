<template>

  <v-card class="mk-card" @click="goDetail" tabindex="0">

    <v-card-text>

      <!-- row 1 -->
      <div class="mk-row-top">

        <div>

          <div class="mk-symbol">
            {{ item.symbol }}
          </div>

          <div class="mk-exchange">
            {{ item.exchange }} · {{ item.quoteAsset }}
          </div>

          <div class="mk-name">
            {{ item.name }}
          </div>

        </div>

        <v-icon
          :icon="item.isWatchlisted ? 'mdi-star' : 'mdi-star-outline'"
          :color="item.isWatchlisted ? 'amber' : 'grey'"
          @click.stop="toggle"
          size="25"
        />

      </div>

      <!-- row 2 -->
      <div class="mk-row-bottom">

        <div class="mk-price">
          {{ formatPrice(item.closePrice) }} {{ item.quoteAsset }}
        </div>

        <div class="mk-change-block">

          <div
            class="mk-change"
            :class="item.change && item.change<0 ? 'mk-change-down' : 'mk-change-up'"
          >
            {{ formatChange(item.changeRate) }}%
          </div>

          <div class="mk-volume">
            <div>거래량 {{ formatVolume(item.volume) }} </div>
            <div>거래대금(원) {{ formatVolume(item.normalizedVolume) }}</div>
          </div>

        </div>

      </div>

    </v-card-text>

  </v-card>

</template>

<script setup lang="ts">
import {formatChange, formatPrice, formatVolume} from "@/utils/format"
import type { MarketDto } from "@/services/market.types"
import { useMarketStore } from "@/stores/market.store"

const marketStore = useMarketStore()
const props = defineProps<{
  item: MarketDto
}>()

const emit = defineEmits<{
  (e: 'select', payload: { exchange: string; symbol: string }): void
}>()

function goDetail() {
  emit('select', {
    exchange: props.item.exchange,
    symbol: props.item.symbol,
  })
}

async function toggle(e: MouseEvent) {
  // e.stopPropagation()
  await marketStore.toggleWatchlist(props.item)
}
</script>