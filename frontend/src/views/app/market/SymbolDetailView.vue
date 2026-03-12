<template>
  <v-container class="app-container">
    <SymbolSummaryCard :symbol="symbol" />

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
          block
          size="large"
          variant="outlined"
          class="sd-favorite-btn"
          prepend-icon="mdi-star"
        >
          관심 해제
        </v-btn>
      </v-col>
    </v-row>

  </v-container>
</template>

<script setup lang="ts">
import SymbolSummaryCard from "@/components/market/SymbolSummaryCard.vue"
import SymbolChartCard from "@/components/market/SymbolChartCard.vue"

const symbol = {
  symbol: "BTC/USDT",
  name: "Bitcoin",
  exchange: "UPBIT",
  price: "₩58,420,000",
  change: "+2.35%",
  high: "₩59,200,000",
  low: "₩56,800,000",
  volume: "₩1.2T",
}
</script>