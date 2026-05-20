import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as watchlistSevice from '@/services/watchlist.service'

export const useWatchlistStore = defineStore('watchlist', () => {
  const items = ref<Set<number>>(new Set())

  async function createWatchlist(id: number) {
    await watchlistSevice.createWatchlist({ exchangeInstrumentId: id })
    items.value.add(id)
  }

  async function removeWatchlist(id: number) {
    await watchlistSevice.removeWatchlist(id)
    items.value.delete(id)
  }

  function isWatchlisted(id: number) {
    return items.value.has(id)
  }

  return {
    items,
    createWatchlist,
    removeWatchlist,
    isWatchlisted,
  }
})
