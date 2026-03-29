<template>

  <v-card
    rounded="lg"
    variant="flat"
    class="sd-summary-card"
  >

    <v-card-text>

      <div class="sd-top">

        <div>

        <div class="sd-name">
          {{ market.name }}
          <v-chip size="x-small">{{ market.exchange }}</v-chip>
        </div>

        <div class="sd-base">
          {{ market.baseAsset }}
        </div>

        </div>

      <v-icon 
        size="25" 
        :icon="market.isWatchlisted ? 'mdi-star' : 'mdi-star-outline'" 
        :color="market.isWatchlisted ? 'amber' : 'grey'" 
        @click.stop="toggle"
      >
      mdi-star
      </v-icon>

      </div>

      <div class="sd-price">
        {{ formatPrice(market.closePrice) }} {{ market.quoteAsset }}
      </div>

      <div
        class="sd-change"
        :class="market.changeRate && market.changeRate < 0 ? 'sd-change-down' : 'sd-change-up'"
      >
        {{ formatChange(market.changeRate) }}%
      </div>

      <div class="sd-stats">

      <div>
        <div class="label">고가</div>
        <div>{{ formatPrice(market.high) }}</div>
      </div>

      <div>
        <div class="label">저가</div>
        <div>{{ formatPrice(market.low) }}</div>
      </div>

      <div>
        <div class="label">거래대금(원)</div>
        <div>{{ formatVolume(market.normalizedVolume) }}</div>
      </div>

    </div>

    </v-card-text>

  </v-card>

</template>

<script setup lang="ts">
import type { MarketDto } from "@/services/market.types"
import { useMarketStore } from "@/stores/market.store"
import { formatPrice, formatChange, formatVolume } from "@/utils/format"

const marketStore = useMarketStore()

const props = defineProps<{
  market: MarketDto
}>()

async function toggle() {
  await marketStore.toggleWatchlist(props.market)
}
</script>