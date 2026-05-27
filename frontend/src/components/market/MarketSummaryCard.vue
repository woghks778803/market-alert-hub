<template>
  <v-card
    rounded="lg"
    variant="flat"
    class="sd-summary-card"
  >
    <v-card-text>
      <div class="sd-row">
        <div class="sd-left">
          <div class="sd-top">
            <div class="sd-name">
              {{ market.name }}
              <v-chip size="x-small" @click.stop="goExchangeDetail">{{ market.exchangeCode }}</v-chip>
              <v-chip size="x-small" @click.stop="goInstrumentDetail">{{ market.baseSymbol }}</v-chip>
            </div>
          </div>

          <div class="sd-price">{{ formatPrice(market.closePrice) }} {{ market.quoteSymbol }}</div>

          <div
            class="sd-change"
            :class="market.changeRate && market.changeRate < 0 ? 'sd-change-down' : 'sd-change-up'"
          >
            {{ formatChange(market.changeRate) }}%
          </div>
        </div>

        <div class="sd-actions">
          <v-btn
            icon
            size="small"
            variant="tonal"
          >
            <v-icon
              size="25"
              :icon="market.isWatchlisted ? 'mdi-star' : 'mdi-star-outline'"
              :color="market.isWatchlisted ? 'amber' : 'grey'"
              @click.stop="toggleWatchlist"
            >
              mdi-star
            </v-icon>
          </v-btn>

          <v-btn
            icon
            size="small"
            variant="tonal"
            class="sd-collapse-btn"
            @click.stop="toggleCollapsed"
          >
            <v-icon>
              {{ collapsed ? 'mdi-chevron-down' : 'mdi-chevron-up' }}
            </v-icon>
          </v-btn>
        </div>
      </div>

      <div
        v-show="!props.collapsed"
        class="sd-stats"
      >
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
import type { MarketDto } from '@/services/market.types'
import { useMarketStore } from '@/stores/market.store'
import { formatPrice, formatChange, formatVolume } from '@/utils/format'

const marketStore = useMarketStore()

const props = defineProps<{
  market: MarketDto
  collapsed: boolean
}>()

const emit = defineEmits<{
  (e: 'toggle'): void
  (e: 'exchange', payload: { exchange: string }): void
  (e: 'instrument', payload: { symbol: string }): void
}>()

async function toggleWatchlist() {
  await marketStore.toggleWatchlist(props.market)
}

async function toggleCollapsed() {
  emit('toggle')
}

async function goExchangeDetail() {
  emit('exchange', {
    exchange: props.market.exchangeCode,
  })
}

async function goInstrumentDetail() {
  emit('instrument', {
    symbol: props.market.baseSymbol,
  })
}
</script>
