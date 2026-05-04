<template>
  <AppLoading
    :show="marketAction.loading.value || candleAction.loading.value"
    overlay
  />

  <v-container class="app-container">
    <SymbolSummaryCard
      v-if="market"
      :market="market"
      :collapsed="collapsed"
      @toggle="toggleCollapsed"
    />

    <SymbolChartCard
      :market="market"
      :collapsed="collapsed"
      :candle-run="candleAction.run"
    />

    <v-row class="sd-actions mt-4">
      <v-col cols="12">
        <v-btn
          block
          size="large"
          color="primary"
          class="sd-alert-btn"
          prepend-icon="mdi-bell-outline"
          @click="goSetting"
        >
          알림 만들기
        </v-btn>
      </v-col>

      <v-col cols="12">
        <v-btn
          v-if="market"
          block
          size="large"
          variant="outlined"
          class="sd-favorite-btn"
          :prepend-icon="market.isWatchlisted ? 'mdi-star' : 'mdi-star-outline'"
          @click.stop="toggleWatchlist"
        >
          {{ market.isWatchlisted ? '관심 해제' : '관심 등록' }}
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { onMounted, onUnmounted, onDeactivated, watch, ref } from 'vue'
import { storeToRefs } from 'pinia'
import AppLoading from '@/components/common/AppLoading.vue'
import SymbolSummaryCard from '@/components/market/SymbolSummaryCard.vue'
import SymbolChartCard from '@/components/market/SymbolChartCard.vue'
import { useAsyncAction } from '@/composables/common/useAsyncAction'
import { WsChannelType, CandleInterval, TickerInterval } from '@/services/market.types'
import { useMarketStore } from '@/stores/market.store'

const route = useRoute()
const router = useRouter()
const marketStore = useMarketStore()
const { market } = storeToRefs(marketStore)
const marketAction = useAsyncAction()
const candleAction = useAsyncAction()

const collapsed = ref(false)

onMounted(async () => {
  marketStore.resetMarket()
  const exchange_code = route.params.exchange as string
  const symbol = route.params.symbol as string

  marketAction.run(async () => {
    await marketStore.fetchMarket(exchange_code, symbol)
  })

  marketStore.initWs()
})

onUnmounted(cleanup)
onDeactivated(cleanup)

function cleanup() {
  marketStore.unsubscribeMarket(WsChannelType.TICKER, TickerInterval.HOUR_24)
  marketStore.unsubscribeMarket(WsChannelType.CANDLE, CandleInterval.SEC_1)
  // marketStore.unsubscribeMarket(WsChannelType.CANDLE, currentTimeframe.value)
  marketStore.cleanupWs()
  marketStore.resetMarket()
}

async function toggleWatchlist() {
  if (!market.value) return
  await marketStore.toggleWatchlist(market.value)
}

async function toggleCollapsed() {
  collapsed.value = !collapsed.value
}

function goSetting() {
  router.push({ name: 'RuleSetting' })
}

watch(
  () => market.value,
  async (m) => {
    if (!m) return
    // 차트용
    marketStore.subscribeMarket(WsChannelType.CANDLE, CandleInterval.SEC_1)
    // 상세용 ticker
    marketStore.subscribeMarket(WsChannelType.TICKER, TickerInterval.HOUR_24)
    // 타임프레임 확정 캔들 (현재 TradingView Lightweight Charts는 과거 데이터 수정을 지원하지 않고 확장만 가능, 확정 캔들을 받을 필요가 없음)
    // marketStore.subscribeMarket(WsChannelType.CANDLE, currentTimeframe.value)
  },
  { immediate: true }
)

// watch( () => marketAction.loading.value, (v) => { console.log('[market loading]', v) } )
// watch( () => candleAction.loading.value, (v) => { console.log('[candle loading]', v) } )
// watch( () => marketAction.loading.value || candleAction.loading.value, (v) => { console.log('[page loading]', v) } )
</script>
