<template>
  <v-container class="app-container">
    <SymbolSummaryCard v-if="market" :market="market" />

    <SymbolChartCard />

    <v-row class="sd-actions mt-4">
      <v-col cols="12">
        <v-btn
          block
          size="large"
          color="primary"
          class="sd-alert-btn"
          prepend-icon="mdi-bell-outline"
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
          @click.stop="toggle"
        >
          {{ market.isWatchlisted ? '관심 해제' : '관심 등록' }}
        </v-btn>
      </v-col>
    </v-row>

  </v-container>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router"
import { onMounted, onUnmounted, onDeactivated } from "vue"
import { storeToRefs } from "pinia"
import SymbolSummaryCard from "@/components/market/SymbolSummaryCard.vue"
import SymbolChartCard from "@/components/market/SymbolChartCard.vue"
import { useMarketStore } from "@/stores/market.store"

const route = useRoute()
const marketStore = useMarketStore()
const { market } = storeToRefs(marketStore)

onMounted(async () => {
  marketStore.resetMarket()

  const exchange_code = route.params.exchange as string
  const symbol = route.params.symbol as string
  await marketStore.fetchMarket(exchange_code, symbol)

  marketStore.subscribeMarket()
  marketStore.initWs()
})

onUnmounted(cleanup)
onDeactivated(cleanup)

function cleanup() {
  marketStore.unsubscribeMarket()
  marketStore.cleanupWs()
}

async function toggle() {
  if (!market.value) return
  await marketStore.toggleWatchlist(market.value)
}

</script>