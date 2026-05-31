<template>
  <AppLoading
    :show="exchangeAction.loading.value"
    overlay
  />

  <v-container 
    class="app-container market-entity-page"
  >
    <template v-if="exchange">
      <!-- 거래소 기본 정보 -->
      <v-card
        class="market-entity-summary"
        elevation="0"
      >
        <div class="market-entity-summary__top">
          <div class="market-entity-logo">
            {{ exchange.code.charAt(0) }}
          </div>
  
          <div class="market-entity-summary__content">
            <div class="market-entity-title-row">
              <strong class="market-entity-title">
                {{ exchange.name }}
              </strong>
  
              <v-chip
                size="small"
                variant="tonal"
              >
                {{ exchange.code }}
              </v-chip>
            </div>
  
            <div class="market-entity-subtitle">
              {{ exchange.nameKo }}
            </div>
          </div>
  
          <!-- <v-btn
            icon="mdi-open-in-new"
            variant="text"
            color="medium-emphasis"
            aria-label="거래소 홈페이지 열기"
          /> -->
        </div>
  
        <v-divider class="market-entity-divider" />
  
        <div class="market-entity-info-grid">
          <div class="market-entity-info">
            <div class="market-entity-info__label">
              국가
            </div>
  
            <div class="market-entity-info__value">
              {{ exchange.country || '-' }}
            </div>
          </div>
  
          <div class="market-entity-info">
            <div class="market-entity-info__label">
              지원 마켓
            </div>
  
            <div class="market-entity-info__value">
              {{ exchange.marketCount.toLocaleString() }} 개
            </div>
          </div>
        </div>
      </v-card>
  
      <!-- 마켓 목록 -->
      <section class="market-entity-section">
        <div class="market-entity-section__header">
          <div>
            <div class="market-entity-section__title">
              지원 마켓
            </div>
  
            <div class="market-entity-section__subtitle">
              {{ exchange.name }}에서 지원하는 마켓입니다.
            </div>
          </div>
  
          <span class="market-entity-count">
            {{ markets.length.toLocaleString() }}개
          </span>
        </div>
  
        <RelatedMarketList
          :items="markets"
          @select="goMarketDetail"
        >
          <template #chip="{ market }">
            {{ market.baseSymbol }}
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
const { exchange, markets } = storeToRefs(marketStore)
const exchangeAction = useAsyncAction()

onMounted(async () => {
  marketStore.resetMarket()
  const exchangeCode = route.params.exchange as string

  exchangeAction.run(async () => {
    await marketStore.fetchExchange(exchangeCode)
    await marketStore.fetchExchangeMarkets(exchangeCode)
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