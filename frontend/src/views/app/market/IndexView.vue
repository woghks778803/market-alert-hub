<template>
  <AppLoading :show="marketAction.loading.value" overlay />
  
  <v-container class="app-container">
    <MarketSearchBar @search="handleSearch" />

    <MarketFilterTabs :exchangeTabs="exchanges" @change="handleFilter" />

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
            @click="handleSort(key)"
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
import { onMounted, onUnmounted, onDeactivated } from "vue"
import { storeToRefs } from "pinia"

import AppLoading from "@/components/common/AppLoading.vue"
import MarketSearchBar from "@/components/market/MarketSearchBar.vue"
import MarketFilterTabs from "@/components/market/MarketFilterTabs.vue"
import MarketList from "@/components/market/MarketList.vue"

import { useAsyncAction } from "@/composables/common/useAsyncAction"
import { useMarketStore } from "@/stores/market.store"
import { MarketSortLabel, MarketSort } from "@/services/market.types"

const marketStore = useMarketStore()
const { markets, exchanges, openSort } = storeToRefs(marketStore)
const marketAction = useAsyncAction()

onMounted(async () => {
  marketStore.resetMarket()

  marketAction.run(async () => {
    await marketStore.fetchExchanges()
    await marketStore.fetchMarkets()
  })

  marketStore.subscribeMarkets()
  marketStore.initWs()
})

onUnmounted(cleanup)
onDeactivated(cleanup)

function cleanup() {
  marketStore.unsubscribeMarkets()
  marketStore.cleanupWs()
}

function handleSort(sort: MarketSort) {
  marketAction.run(() => {
    marketStore.setSort(sort)
    openSort.value = false
  })
}

const handleSearch = (keyword: string) => {
  marketAction.run(() => {
    marketStore.setSearch(keyword)
  })
}

const handleFilter = (filter: string[]) => {
  marketAction.run(() => {
    marketStore.setMarketFilter(filter)
  })
}

// watch( () => marketAction.loading.value, (v) => { console.log('[market loading]', v) } ) 
</script>