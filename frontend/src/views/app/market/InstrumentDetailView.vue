<template>
  <AppLoading
    :show="instrumentAction.loading.value"
    overlay
  />

  <v-container class="app-container market-entity-page">
    <template v-if="instrument">
      <!-- 종목 기본 정보 -->
      <v-card
        class="market-entity-summary"
        elevation="0"
      >
        <div class="market-entity-summary__top">
          <div class="market-entity-logo">
            {{ instrument.symbol.charAt(0) }}
          </div>
  
          <div class="market-entity-summary__content">
            <div class="market-entity-title-row">
              <strong class="market-entity-title">
                {{ instrument.name }}
              </strong>
  
              <v-chip
                size="small"
                variant="tonal"
              >
                {{ instrument.symbol }}
              </v-chip>
            </div>
  
            <div class="market-entity-subtitle">
              {{ instrument.nameKo }}
            </div>
          </div>
        </div>
  
        <v-divider class="market-entity-divider" />
  
        <div class="market-entity-info-grid">
          <div class="market-entity-info">
            <div class="market-entity-info__label">
              자산 유형
            </div>
  
            <div class="market-entity-info__value">
              {{ instrument.assetType || '-' }}
            </div>
          </div>
  
          <div class="market-entity-info">
            <div class="market-entity-info__label">
              지원 거래소
            </div>
  
            <div class="market-entity-info__value">
              {{ instrument.exchangeCount.toLocaleString() }} 개
            </div>
          </div>
  
          <div class="market-entity-info">
            <div class="market-entity-info__label">
              지원 마켓
            </div>
  
            <div class="market-entity-info__value">
              {{ instrument.marketCount.toLocaleString() }} 개
            </div>
          </div>
        </div>
      </v-card>
  
      <!-- 거래소별 마켓 목록 -->
      <section class="market-entity-section">
        <div class="market-entity-section__header">
          <div>
            <div class="market-entity-section__title">
              지원 마켓
            </div>
  
            <div class="market-entity-section__subtitle">
              {{ instrument.name }}을 거래할 수 있는 마켓입니다.
            </div>
          </div>
  
          <span class="market-entity-count">
            3개
          </span>
        </div>
  
        <div class="mk-list">

          <v-card
            v-for="market in markets"
            :key="market.exchangeInstrumentId"
            class="mk-card market-entity-market-card"
            elevation="0"
            @click="goMarketDetail(market)"
          >
            <div class="mk-row-top">
              <div>
                <div class="market-entity-symbol-row">
                  <strong class="mk-symbol">
                    {{ market.baseSymbol }}/{{ market.quoteSymbol }}
                  </strong>
  
                  <v-chip
                    size="x-small"
                    variant="tonal"
                  >
                    {{ market.exchangeCode }}
                  </v-chip>
                </div>
  
                <div class="mk-name">
                  {{ market.name }}
                </div>
              </div>
  
              <div class="mk-change-block">
                <div class="mk-price">
                  {{ formatPrice(market.closePrice, getDecimalPlaces(market.closePrice)) }}
                  {{ market.quoteSymbol }}
                </div>
  
                <div 
                  :class="market.changeRate && market.changeRate < 0 ? 'mk-change-down' : 'mk-change-up'"
                >
                  {{ formatChange(market.changeRate) }}%
                </div>
              </div>
            </div>
  
            <div class="mk-row-bottom">
              <span class="mk-volume">
                거래대금(원) {{ formatVolume(market.normalizedVolume) }}
              </span>
  
              <v-icon
                icon="mdi-chevron-right"
                size="20"
                color="medium-emphasis"
              />
            </div>
          </v-card>
  
        </div>
      </section>
    </template>
  </v-container>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'

import { formatPrice, formatChange, formatVolume } from '@/utils/format'
import { getDecimalPlaces } from '@/utils/number'
import AppLoading from '@/components/common/AppLoading.vue'
import { useAsyncAction } from '@/composables/common/useAsyncAction'
import type { MarketDto } from '@/services/market.types'
import { useMarketStore } from '@/stores/market.store'

const route = useRoute()
const router = useRouter()
const marketStore = useMarketStore()
const { instrument, markets } = storeToRefs(marketStore)
const instrumentAction = useAsyncAction()

onMounted(async () => {
  marketStore.resetMarket()
  const instrumentSymbol = route.params.symbol as string

  instrumentAction.run(async () => {
    await marketStore.fetchInstrument(instrumentSymbol)
    await marketStore.fetchInstrumentMarkets(instrumentSymbol)
  })

  // marketStore.initWs()
})

function goMarketDetail(market: MarketDto) {
  router.push({
    name: 'MarketDetail',
    params: {
      exchange: market.exchangeCode,
      exchangeSymbol: market.exchangeSymbol,
    },
  })
}
</script>