<template>
  <v-container class="app-container">
    <MarketSearchBar />

    <MarketFilterTabs />

    <div class="mk-header">

      <div class="mk-sort">
        거래대금
        <v-icon size="16">mdi-chevron-down</v-icon>
      </div>

      <div class="mk-count">
        {{ markets.length }}개 결과
      </div>

    </div>

    <MarketList :items="markets" />

  </v-container>
</template>

<script setup lang="ts">
import MarketSearchBar from "@/components/market/MarketSearchBar.vue"
import MarketFilterTabs from "@/components/market/MarketFilterTabs.vue"
import MarketList from "@/components/market/MarketList.vue"

const markets = [
  {
    symbol: "BTC/USDT",
    exchange: "UPBIT",
    pair: "KRW",
    name: "Bitcoin",
    price: "₩58,420,000",
    change: "+2.35%",
    favorite: true,
  },
  {
    symbol: "ETH/USDT",
    exchange: "UPBIT",
    pair: "KRW",
    name: "Ethereum",
    price: "₩3,250,000",
    change: "+1.87%",
    favorite: true,
  },
  {
    symbol: "XRP/USDT",
    exchange: "BINANCE",
    pair: "USDT",
    name: "Ripple",
    price: "$0.6234",
    change: "-1.23%",
    favorite: false,
  },
  {
    symbol: "XRP/USDT",
    exchange: "BINANCE",
    pair: "USDT",
    name: "Ripple",
    price: "$0.6234",
    change: "-1.23%",
    favorite: false,
  },
  {
    symbol: "XRP/USDT",
    exchange: "BINANCE",
    pair: "USDT",
    name: "Ripple",
    price: "$0.6234",
    change: "-1.23%",
    favorite: false,
  },
]
</script>