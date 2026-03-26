<template>
  <v-container class="app-container">
    <MarketSearchBar :search="search" @search="marketStore.setSearch" />

    <MarketFilterTabs :exchangeTabs="exchanges" @change="marketStore.setExchange" />

    <div class="mk-header">

      <div class="mk-sort" @click="openSort = true">
        {{ marketStore.currentSortLabel }}
        <v-icon size="16">mdi-chevron-down</v-icon>
      </div>

      <v-menu v-model="openSort">
        <v-list>
          <v-list-item
            v-for="(label, key) in MarketSortLabel"
            :key="key"
            @click="selectSort(key)"
          >
            {{ label }}
          </v-list-item>
        </v-list>
      </v-menu>

      <div class="mk-count">
        {{ markets.length }}개 결과
      </div>

    </div>

    <MarketList :items="markets"/>

  </v-container>
</template>

<script setup lang="ts">
import { onMounted } from "vue"
import { storeToRefs } from "pinia"

import MarketSearchBar from "@/components/market/MarketSearchBar.vue"
import MarketFilterTabs from "@/components/market/MarketFilterTabs.vue"
import MarketList from "@/components/market/MarketList.vue"

import { useMarketStore } from "@/stores/market.store"
import { MarketSortLabel, MarketSort } from "@/services/market.types"

const marketStore = useMarketStore()
const { markets, exchanges, openSort, search } = storeToRefs(marketStore)

onMounted(() => {
  marketStore.resetMarket()
  marketStore.fetchExchanges()
  marketStore.fetchMarkets()
})

function selectSort(sort: MarketSort) {
  marketStore.setSort(sort)
  openSort.value = false
}

</script>