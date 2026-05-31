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
  
        <RelatedMarketList
          :items="markets"
          @select="goMarketDetail"
        >
          <template #chip="{ market }">
            {{ market.exchangeCode }}
          </template>
        </RelatedMarketList>
      </section>
    </template>
  </v-container>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { onMounted, onUnmounted, onDeactivated, watch } from 'vue'
import { storeToRefs } from 'pinia'

import AppLoading from '@/components/common/AppLoading.vue'
import RelatedMarketList from '@/components/market/RelatedMarketList.vue'
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

  marketStore.initWs()
})

onUnmounted(cleanup)
onDeactivated(cleanup)

function cleanup() {
  marketStore.unsubscribeMarkets()
  marketStore.cleanupWs()
}

function goMarketDetail(market: MarketDto) {
  router.push({
    name: 'MarketDetail',
    params: {
      exchange: market.exchangeCode,
      exchangeSymbol: market.exchangeSymbol,
    },
  })
}

watch(
  () => markets.value,
  async () => {
    marketStore.subscribeMarkets()
  },
  { immediate: true }
)
</script>